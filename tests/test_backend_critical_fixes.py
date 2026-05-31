import asyncio
import copy
import io
import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server


def run(coro):
    return asyncio.run(coro)


class UpdateResult:
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, length):
        return copy.deepcopy(self.docs[:length])


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def find_one(self, query=None, projection=None):
        for doc in self.docs:
            if self._matches(doc, query or {}):
                return self._project(doc, projection)
        return None

    def find(self, query=None, projection=None):
        docs = [
            self._project(doc, projection)
            for doc in self.docs
            if self._matches(doc, query or {})
        ]
        return FakeCursor(docs)

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                before = copy.deepcopy(doc)
                self._apply_update(doc, query, update)
                return UpdateResult(1, 1 if doc != before else 0)
        return UpdateResult(0, 0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            if key == "steps" and "$elemMatch" in expected:
                if not any(self._matches(step, expected["$elemMatch"]) for step in doc.get("steps", [])):
                    return False
                continue

            if "." in key:
                first, rest = key.split(".", 1)
                value = doc.get(first)
                if isinstance(value, list):
                    if not any(self._matches({rest: item.get(rest)}, {rest: expected}) for item in value):
                        return False
                    continue
                value = self._nested_get(doc, key)
            else:
                value = doc.get(key)

            if isinstance(expected, dict) and "$ne" in expected:
                if value == expected["$ne"]:
                    return False
            elif value != expected:
                return False
        return True

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if not projection:
            return projected

        include_keys = {key for key, value in projection.items() if value == 1}
        exclude_keys = {key for key, value in projection.items() if value == 0}

        if include_keys:
            projected = {key: copy.deepcopy(doc[key]) for key in include_keys if key in doc}
            if projection.get("_id") == 0:
                projected.pop("_id", None)
            return projected

        for key in exclude_keys:
            projected.pop(key, None)
        return projected

    def _apply_update(self, doc, query, update):
        step_name = self._step_name_from_query(query)

        for key, value in update.get("$set", {}).items():
            if key.startswith("steps.$.") and step_name:
                field = key.replace("steps.$.", "")
                for step in doc.get("steps", []):
                    if step.get("step_name") == step_name:
                        step[field] = value
                        break
            else:
                doc[key] = value

        for key, value in update.get("$push", {}).items():
            if key == "steps.$.photos" and step_name:
                for step in doc.get("steps", []):
                    if step.get("step_name") == step_name:
                        step.setdefault("photos", []).append(value)
                        break

        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value

    def _step_name_from_query(self, query):
        if "steps.step_name" in query:
            return query["steps.step_name"]
        elem_match = query.get("steps", {}).get("$elemMatch")
        if elem_match:
            return elem_match.get("step_name")
        return None

    def _nested_get(self, doc, key):
        value = doc
        for part in key.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value


class FakeDB:
    def __init__(self, **collections):
        self.inspections = FakeCollection(collections.get("inspections"))
        self.users = FakeCollection(collections.get("users"))
        self.inspector_profiles = FakeCollection(collections.get("inspector_profiles"))
        self.inspection_progress = FakeCollection(collections.get("inspection_progress"))
        self.reports = FakeCollection(collections.get("reports"))
        self.notifications = FakeCollection(collections.get("notifications"))


def inspection_doc(status="pending", inspector_id=None):
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
        "inspector_id": inspector_id,
        "inspector_name": "Inspector" if inspector_id else None,
        "created_at": "2026-05-31T11:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }


def verified_inspector(user_id="inspector-1"):
    return {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "full_name": "Inspector",
        "phone": "+10000000000",
        "user_type": "inspector",
        "created_at": "2026-05-31T11:00:00+00:00",
    }


def inspector_profile(user_id="inspector-1"):
    return {
        "user_id": user_id,
        "id_verified": True,
        "location_lat": 41.8781,
        "location_lng": -87.6298,
        "radius_miles": 50,
        "total_inspections": 0,
        "earnings": 0.0,
    }


def test_inspector_job_lists_do_not_expose_security_codes(monkeypatch):
    db = FakeDB(
        inspections=[
            inspection_doc(status="pending"),
            inspection_doc(status="accepted", inspector_id="inspector-1"),
        ]
    )
    monkeypatch.setattr(server, "db", db)

    available = run(server.get_available_inspections())
    my_jobs = run(server.get_inspector_jobs("inspector-1"))

    assert available
    assert my_jobs
    assert "security_code" not in available[0]
    assert "security_code" not in my_jobs[0]


def test_accept_inspection_cannot_be_overwritten(monkeypatch):
    db = FakeDB(
        inspections=[inspection_doc(status="pending")],
        users=[verified_inspector("inspector-1"), verified_inspector("inspector-2")],
        inspector_profiles=[inspector_profile("inspector-1"), inspector_profile("inspector-2")],
    )
    monkeypatch.setattr(server, "db", db)

    accepted = run(server.accept_inspection("inspection-1", "inspector-1"))
    assert accepted["inspector_id"] == "inspector-1"

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-2"))

    assert exc_info.value.status_code == 400
    assert db.inspections.docs[0]["inspector_id"] == "inspector-1"
    assert len(db.notifications.docs) == 1


def test_verify_security_code_is_idempotent(monkeypatch):
    db = FakeDB(inspections=[inspection_doc(status="accepted", inspector_id="inspector-1")])
    monkeypatch.setattr(server, "db", db)

    first = run(server.verify_security_code("inspection-1", "123456"))
    second = run(server.verify_security_code("inspection-1", "123456"))

    assert first["steps"] == server.INSPECTION_STEPS
    assert second["steps"] == server.INSPECTION_STEPS
    assert db.inspections.docs[0]["status"] == "in_progress"
    assert len(db.inspection_progress.docs) == 1


def test_complete_step_does_not_advance_twice_on_retry(monkeypatch):
    db = FakeDB(
        inspection_progress=[{
            "inspection_id": "inspection-1",
            "steps": server.build_inspection_steps(),
            "current_step": 0,
            "started_at": "2026-05-31T11:00:00+00:00",
        }]
    )
    monkeypatch.setattr(server, "db", db)

    run(server.complete_step("inspection-1", "exterior_front", "done"))
    run(server.complete_step("inspection-1", "exterior_front", "done"))

    progress = db.inspection_progress.docs[0]
    assert progress["steps"][0]["completed"] is True
    assert progress["current_step"] == 1


def test_upload_photo_rejects_invalid_step_before_writing(monkeypatch, tmp_path):
    db = FakeDB(
        inspection_progress=[{
            "inspection_id": "inspection-1",
            "steps": server.build_inspection_steps(),
            "current_step": 0,
            "started_at": "2026-05-31T11:00:00+00:00",
        }]
    )
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)

    upload = type("Upload", (), {"filename": "photo.jpg", "file": io.BytesIO(b"image")})()

    with pytest.raises(HTTPException) as exc_info:
        run(server.upload_inspection_photo("inspection-1", "../../escape", upload))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_submit_report_is_idempotent_and_does_not_double_pay(monkeypatch):
    db = FakeDB(
        inspections=[inspection_doc(status="in_progress", inspector_id="inspector-1")],
        inspector_profiles=[inspector_profile("inspector-1")],
    )
    monkeypatch.setattr(server, "db", db)
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )

    first = run(server.submit_report("inspection-1", report))
    second = run(server.submit_report("inspection-1", report))

    assert first["report_id"] == second["report_id"]
    assert len(db.reports.docs) == 1
    assert len(db.notifications.docs) == 1
    assert db.inspections.docs[0]["status"] == "completed"
    assert db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert db.inspector_profiles.docs[0]["earnings"] == 216.0
