import asyncio
import copy
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import server  # noqa: E402


class UpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, limit):
        return copy.deepcopy(self.docs[:limit])


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    def find(self, query, projection=None):
        return FakeCursor([self._project(doc, projection) for doc in self.docs if self._matches(doc, query)])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, update, query)
                return UpdateResult(1)

        if upsert:
            doc = {key: value for key, value in query.items() if "." not in key and not isinstance(value, dict)}
            self._apply_update(doc, update, query, inserting=True)
            self.docs.append(doc)
        return UpdateResult(0)

    async def find_one_and_update(self, query, update, projection=None, return_document=None):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, update, query)
                return self._project(doc, projection)
        return None

    def _matches(self, doc, query):
        for key, expected in query.items():
            actual = self._get_value(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
            elif key == "steps.step_name":
                if not any(step.get("step_name") == expected for step in doc.get("steps", [])):
                    return False
            elif actual != expected:
                return False
        return True

    def _get_value(self, doc, key):
        value = doc
        for part in key.split("."):
            if isinstance(value, list):
                return None
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value

    def _project(self, doc, projection):
        result = copy.deepcopy(doc)
        if projection and projection.get("_id") == 0:
            result.pop("_id", None)
        return result

    def _apply_update(self, doc, update, query, inserting=False):
        if inserting:
            for key, value in update.get("$setOnInsert", {}).items():
                self._set_value(doc, key, copy.deepcopy(value), query)
        for key, value in update.get("$set", {}).items():
            self._set_value(doc, key, copy.deepcopy(value), query)
        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value
        for key, value in update.get("$push", {}).items():
            self._push_value(doc, key, copy.deepcopy(value), query)

    def _set_value(self, doc, key, value, query):
        if key.startswith("steps.$."):
            field = key.split(".", 2)[2]
            step_name = query["steps.step_name"]
            for step in doc["steps"]:
                if step["step_name"] == step_name:
                    step[field] = value
                    return
        doc[key] = value

    def _push_value(self, doc, key, value, query):
        if key.startswith("steps.$."):
            field = key.split(".", 2)[2]
            step_name = query["steps.step_name"]
            for step in doc["steps"]:
                if step["step_name"] == step_name:
                    step.setdefault(field, []).append(value)
                    return


class FakeDB:
    def __init__(self, inspections=None, progress=None, profiles=None, reports=None):
        self.inspections = FakeCollection(inspections)
        self.inspection_progress = FakeCollection(progress)
        self.inspector_profiles = FakeCollection(profiles)
        self.reports = FakeCollection(reports)
        self.notifications = FakeCollection()
        self.users = FakeCollection()


def run(coro):
    return asyncio.run(coro)


def inspection_doc(status="pending"):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": "inspector-1",
        "inspector_name": "Inspector",
        "created_at": "2026-05-22T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }


def progress_doc():
    return {
        "inspection_id": "inspection-1",
        "steps": [
            server.InspectionStep(
                step_name=step["step_name"],
                description=step["description"],
                required_photos=step["required_photos"],
            ).model_dump()
            for step in server.INSPECTION_STEPS
        ],
        "current_step": 0,
        "started_at": "2026-05-22T00:00:00+00:00",
    }


def report_payload():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "exterior_front", "completed": True}],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_available_jobs_redact_security_code(monkeypatch):
    fake_db = FakeDB(inspections=[inspection_doc()])
    monkeypatch.setattr(server, "db", fake_db)

    jobs = run(server.get_available_inspections(inspector_lat=41.8781, inspector_lng=-87.6298, radius=50))

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]


def test_verify_code_requires_accepted_job_and_is_idempotent(monkeypatch):
    fake_db = FakeDB(inspections=[inspection_doc(status="pending")])
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        run(server.verify_security_code("inspection-1", "123456"))
    assert exc_info.value.status_code == 400

    fake_db.inspections.docs[0]["status"] = "accepted"

    run(server.verify_security_code("inspection-1", "123456"))
    run(server.verify_security_code("inspection-1", "123456"))

    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_complete_step_handles_missing_progress_and_retries(monkeypatch):
    fake_db = FakeDB(progress=[progress_doc()])
    monkeypatch.setattr(server, "db", fake_db)

    run(server.complete_step("inspection-1", "exterior_front", "Front looks good"))
    run(server.complete_step("inspection-1", "exterior_front", "Front looks good"))

    assert fake_db.inspection_progress.docs[0]["current_step"] == 1
    assert fake_db.inspection_progress.docs[0]["steps"][0]["completed"] is True

    empty_db = FakeDB()
    monkeypatch.setattr(server, "db", empty_db)
    with pytest.raises(HTTPException) as exc_info:
        run(server.complete_step("inspection-1", "exterior_front", "Front looks good"))
    assert exc_info.value.status_code == 404


def test_submit_report_is_idempotent_and_pays_once(monkeypatch):
    fake_db = FakeDB(
        inspections=[inspection_doc(status="in_progress")],
        profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.submit_report("inspection-1", report_payload()))
    second = run(server.submit_report("inspection-1", report_payload()))

    assert first["report_id"] == second["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == pytest.approx(216.0)
    assert len(fake_db.notifications.docs) == 1
