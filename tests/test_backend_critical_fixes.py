import asyncio
import copy
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, field, direction):
        reverse = direction < 0
        self.docs.sort(key=lambda doc: doc.get(field, ""), reverse=reverse)
        return self

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
        return FakeCursor([
            self._project(doc, projection)
            for doc in self.docs
            if self._matches(doc, query)
        ])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                before = copy.deepcopy(doc)
                self._apply_update(doc, query, update)
                return FakeUpdateResult(
                    matched_count=1,
                    modified_count=0 if doc == before else 1,
                )
        return FakeUpdateResult()

    def _matches(self, doc, query):
        for key, expected in query.items():
            actual = self._get_value(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
                continue
            if key == "steps.step_name":
                if not any(step.get("step_name") == expected for step in doc.get("steps", [])):
                    return False
                continue
            if actual != expected:
                return False
        return True

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if not projection:
            return projected
        for key, value in projection.items():
            if value == 0:
                projected.pop(key, None)
        return projected

    def _apply_update(self, doc, query, update):
        for path, value in update.get("$set", {}).items():
            self._set_value(doc, query, path, value)
        for path, value in update.get("$inc", {}).items():
            doc[path] = doc.get(path, 0) + value
        for path, value in update.get("$push", {}).items():
            target = self._get_value(doc, path)
            if target is not None:
                target.append(value)

    def _get_value(self, doc, path):
        current = doc
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _set_value(self, doc, query, path, value):
        parts = path.split(".")
        if "$" in parts:
            array_name = parts[0]
            remainder = parts[2:]
            step_name = query.get(f"{array_name}.step_name")
            for item in doc.get(array_name, []):
                if item.get("step_name") == step_name:
                    self._set_nested(item, remainder, value)
                    return
        self._set_nested(doc, parts, value)

    def _set_nested(self, doc, parts, value):
        current = doc
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value


class FakeDB:
    def __init__(self):
        self.inspections = FakeCollection()
        self.inspection_progress = FakeCollection()
        self.users = FakeCollection()
        self.reports = FakeCollection()
        self.inspector_profiles = FakeCollection()
        self.notifications = FakeCollection()


def run(coro):
    return asyncio.run(coro)


def install_db(monkeypatch, fake_db):
    monkeypatch.setattr(server, "db", fake_db)


def make_inspection(status="pending"):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": "inspector-1",
        "inspector_name": "Inspector One",
        "created_at": "2026-01-01T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }


def make_report():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "exterior_front", "completed": True}],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_inspector_facing_routes_do_not_return_security_codes(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspections.docs = [make_inspection()]
    fake_db.users.docs = [{"id": "inspector-1", "full_name": "Inspector One"}]
    install_db(monkeypatch, fake_db)

    available = run(server.get_available_inspections())
    assert available
    assert "security_code" not in available[0]

    accepted = run(server.accept_inspection("inspection-1", "inspector-1"))
    assert accepted["status"] == "accepted"
    assert "security_code" not in accepted

    jobs = run(server.get_inspector_jobs("inspector-1"))
    assert jobs
    assert "security_code" not in jobs[0]


def test_security_code_verification_is_idempotent_and_does_not_reopen_completed(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspections.docs = [make_inspection(status="accepted")]
    install_db(monkeypatch, fake_db)

    first_response = run(server.verify_security_code("inspection-1", "123456"))
    assert first_response["message"] == "Code verified, inspection started"
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1

    second_response = run(server.verify_security_code("inspection-1", "123456"))
    assert second_response["message"] == "Code already verified, inspection already started"
    assert len(fake_db.inspection_progress.docs) == 1

    fake_db.inspections.docs[0]["status"] = "completed"
    with pytest.raises(HTTPException) as exc_info:
        run(server.verify_security_code("inspection-1", "123456"))
    assert exc_info.value.status_code == 409
    assert fake_db.inspections.docs[0]["status"] == "completed"


def test_complete_step_retry_does_not_skip_steps(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspection_progress.docs = [{
        "inspection_id": "inspection-1",
        "current_step": 0,
        "steps": [
            {"step_name": "exterior_front", "completed": False, "notes": ""},
            {"step_name": "interior", "completed": False, "notes": ""},
            {"step_name": "engine", "completed": False, "notes": ""},
        ],
    }]
    install_db(monkeypatch, fake_db)

    run(server.complete_step("inspection-1", "exterior_front", "done"))
    assert fake_db.inspection_progress.docs[0]["current_step"] == 1

    run(server.complete_step("inspection-1", "exterior_front", "done again"))
    assert fake_db.inspection_progress.docs[0]["current_step"] == 1


def test_complete_step_returns_404_when_progress_is_missing(monkeypatch):
    fake_db = FakeDB()
    install_db(monkeypatch, fake_db)

    with pytest.raises(HTTPException) as exc_info:
        run(server.complete_step("missing-inspection", "exterior_front", "done"))
    assert exc_info.value.status_code == 404


def test_report_submission_is_idempotent_for_payouts_and_notifications(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspections.docs = [make_inspection(status="in_progress")]
    fake_db.inspector_profiles.docs = [{
        "user_id": "inspector-1",
        "total_inspections": 0,
        "earnings": 0.0,
    }]
    install_db(monkeypatch, fake_db)

    first_response = run(server.submit_report("inspection-1", make_report()))
    second_response = run(server.submit_report("inspection-1", make_report()))

    assert first_response["report_id"] == second_response["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == pytest.approx(216.0)


def test_report_submission_requires_in_progress_inspection(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspections.docs = [make_inspection(status="accepted")]
    fake_db.inspector_profiles.docs = [{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}]
    install_db(monkeypatch, fake_db)

    with pytest.raises(HTTPException) as exc_info:
        run(server.submit_report("inspection-1", make_report()))

    assert exc_info.value.status_code == 409
    assert fake_db.reports.docs == []
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 0.0
