import asyncio
import copy
import io
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction):
        reverse = direction < 0
        self.docs.sort(key=lambda doc: doc.get(key, ""), reverse=reverse)
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
        docs = [self._project(doc, projection) for doc in self.docs if self._matches(doc, query)]
        return FakeCursor(docs)

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return object()

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                changed = self._apply_update(doc, query, update)
                return FakeUpdateResult(1 if changed else 0)
        return FakeUpdateResult(0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            if key == "steps.step_name":
                if not any(step.get("step_name") == expected for step in doc.get("steps", [])):
                    return False
                continue

            actual = doc.get(key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
                continue

            if actual != expected:
                return False
        return True

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection and projection.get("_id") == 0:
            projected.pop("_id", None)
        return projected

    def _apply_update(self, doc, query, update):
        before = copy.deepcopy(doc)

        for key, value in update.get("$set", {}).items():
            if key.startswith("steps.$."):
                step_key = key.removeprefix("steps.$.")
                for step in doc.get("steps", []):
                    if step.get("step_name") == query.get("steps.step_name"):
                        step[step_key] = value
                        break
            else:
                doc[key] = value

        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value

        for key, value in update.get("$push", {}).items():
            if key == "steps.$.photos":
                for step in doc.get("steps", []):
                    if step.get("step_name") == query.get("steps.step_name"):
                        step.setdefault("photos", []).append(value)
                        break

        return before != doc


class FakeDB:
    def __init__(self):
        self.inspections = FakeCollection()
        self.inspection_progress = FakeCollection()
        self.inspector_profiles = FakeCollection()
        self.reports = FakeCollection()
        self.notifications = FakeCollection()
        self.users = FakeCollection()


class FakeUpload:
    def __init__(self, filename):
        self.filename = filename
        self.file = io.BytesIO(b"photo-bytes")


@pytest.fixture(autouse=True)
def fake_db(monkeypatch, tmp_path):
    db = FakeDB()
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)
    return db


def make_inspection(status="in_progress"):
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
        "created_at": "2026-05-28T00:00:00+00:00",
        "accepted_at": "2026-05-28T00:01:00+00:00",
        "completed_at": None,
    }


def make_progress():
    steps = [
        {
            "step_name": step["step_name"],
            "description": step["description"],
            "required_photos": step["required_photos"],
            "completed": False,
            "photos": [],
            "notes": "",
        }
        for step in server.INSPECTION_STEPS
    ]
    return {"inspection_id": "inspection-1", "steps": steps, "current_step": 0}


def run(coro):
    return asyncio.run(coro)


def test_available_jobs_do_not_leak_security_code(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="pending"))

    jobs = run(server.get_available_inspections(41.8781, -87.6298, 50))

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]


def test_accept_is_atomic_and_does_not_return_security_code(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="pending"))
    fake_db.users.docs.append({"id": "inspector-1", "full_name": "Inspector"})

    accepted = run(server.accept_inspection("inspection-1", "inspector-1"))
    assert accepted["status"] == "accepted"
    assert "security_code" not in accepted

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-1"))
    assert exc_info.value.status_code == 400
    assert len(fake_db.notifications.docs) == 1


def test_verify_code_is_state_gated_and_idempotent(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="accepted"))

    first = run(server.verify_security_code("inspection-1", "123456"))
    second = run(server.verify_security_code("inspection-1", "123456"))

    assert first["steps"]
    assert second["message"] == "Inspection already started"
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_verify_code_does_not_reopen_completed_inspection(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="completed"))

    with pytest.raises(HTTPException) as exc_info:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspections.docs[0]["status"] == "completed"
    assert fake_db.inspection_progress.docs == []


def test_submit_report_is_single_use_for_payouts(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="in_progress"))
    fake_db.inspector_profiles.docs.append({"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0})
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )

    run(server.submit_report("inspection-1", report))
    with pytest.raises(HTTPException) as exc_info:
        run(server.submit_report("inspection-1", report))

    assert exc_info.value.status_code == 400
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == pytest.approx(216.0)


def test_upload_photo_rejects_invalid_step_and_extension(fake_db):
    fake_db.inspection_progress.docs.append(make_progress())

    with pytest.raises(HTTPException) as bad_step:
        run(server.upload_inspection_photo("inspection-1", "../outside", FakeUpload("photo.jpg")))
    assert bad_step.value.status_code == 400

    with pytest.raises(HTTPException) as bad_extension:
        run(server.upload_inspection_photo("inspection-1", "exterior_front", FakeUpload("photo.jpg/../../evil.py")))
    assert bad_extension.value.status_code == 400


def test_complete_step_returns_404_when_progress_is_missing(fake_db):
    with pytest.raises(HTTPException) as exc_info:
        run(server.complete_step("missing", "exterior_front"))

    assert exc_info.value.status_code == 404


def test_complete_step_retry_does_not_skip_steps(fake_db):
    fake_db.inspection_progress.docs.append(make_progress())

    run(server.complete_step("inspection-1", "exterior_front", "Front looks good"))
    run(server.complete_step("inspection-1", "exterior_front", "Front looks good"))

    progress = fake_db.inspection_progress.docs[0]
    assert progress["steps"][0]["completed"] is True
    assert progress["current_step"] == 1
