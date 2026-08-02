import asyncio
import copy
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import server  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, _limit):
        return copy.deepcopy(self.docs)


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    def find(self, query, projection=None):
        return FakeCursor([self._project(doc, projection) for doc in self.docs if self._matches(doc, query)])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, query, update)
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            if key == "steps.step_name":
                if not any(step.get("step_name") == expected for step in doc.get("steps", [])):
                    return False
                continue

            actual = self._value_for_key(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    def _value_for_key(self, doc, key):
        value = doc
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    def _apply_update(self, doc, query, update):
        for key, value in update.get("$set", {}).items():
            if key.startswith("steps.$."):
                step_field = key.split(".", 2)[2]
                step_name = query["steps.step_name"]
                for step in doc["steps"]:
                    if step["step_name"] == step_name:
                        step[step_field] = value
                        break
            else:
                doc[key] = value

        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value

        for key, value in update.get("$push", {}).items():
            if key.startswith("steps.$."):
                step_field = key.split(".", 2)[2]
                step_name = query["steps.step_name"]
                for step in doc["steps"]:
                    if step["step_name"] == step_name:
                        step.setdefault(step_field, []).append(value)
                        break

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection and projection.get("_id") == 0:
            projected.pop("_id", None)
        return projected


class FakeDb:
    def __init__(self, *, inspections=None, users=None, profiles=None, progress=None, reports=None):
        self.inspections = FakeCollection(inspections)
        self.users = FakeCollection(users)
        self.inspector_profiles = FakeCollection(profiles)
        self.inspection_progress = FakeCollection(progress)
        self.reports = FakeCollection(reports)
        self.notifications = FakeCollection([])


def inspection_doc(status="pending", inspector_id=None):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.0, "lng": -87.0},
        "package_type": "basic",
        "package_price": 100.0,
        "tip_amount": 0.0,
        "total_amount": 100.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": inspector_id,
        "inspector_name": "Inspector One" if inspector_id else None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }


def inspector_user(user_id="inspector-1"):
    return {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "full_name": "Inspector One",
        "user_type": "inspector",
    }


def inspector_profile(user_id="inspector-1", verified=True):
    return {
        "user_id": user_id,
        "id_verified": verified,
        "total_inspections": 0,
        "earnings": 0.0,
    }


def progress_doc(current_step=0):
    steps = [server.InspectionStep(**step).model_dump() for step in server.INSPECTION_STEPS]
    return {"inspection_id": "inspection-1", "steps": steps, "current_step": current_step}


def report_payload():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_accept_requires_verified_inspector(monkeypatch):
    fake_db = FakeDb(
        inspections=[inspection_doc()],
        users=[inspector_user()],
        profiles=[inspector_profile(verified=False)],
    )
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-1"))

    assert exc_info.value.status_code == 403
    assert fake_db.inspections.docs[0]["status"] == "pending"
    assert fake_db.notifications.docs == []


def test_verify_code_does_not_reopen_completed_inspection(monkeypatch):
    fake_db = FakeDb(
        inspections=[inspection_doc(status="completed", inspector_id="inspector-1")],
        progress=[progress_doc()],
    )
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspections.docs[0]["status"] == "completed"
    assert len(fake_db.inspection_progress.docs) == 1


def test_complete_step_is_ordered_and_retry_safe(monkeypatch):
    fake_db = FakeDb(progress=[progress_doc()])
    monkeypatch.setattr(server, "db", fake_db)

    run(server.complete_step("inspection-1", "exterior_front", "ok"))
    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True

    run(server.complete_step("inspection-1", "exterior_front", "ok"))
    assert fake_db.inspection_progress.docs[0]["current_step"] == 1

    with pytest.raises(HTTPException) as exc_info:
        run(server.complete_step("inspection-1", "exterior_rear", "skip ahead"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspection_progress.docs[0]["current_step"] == 1


def test_submit_report_is_idempotent_and_does_not_double_pay(monkeypatch):
    fake_db = FakeDb(
        inspections=[inspection_doc(status="in_progress", inspector_id="inspector-1")],
        profiles=[inspector_profile()],
    )
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.submit_report("inspection-1", report_payload()))
    second = run(server.submit_report("inspection-1", report_payload()))

    assert second["report_id"] == first["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 80.0
