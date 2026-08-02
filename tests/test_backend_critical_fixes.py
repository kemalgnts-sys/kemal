import asyncio
import copy
import os
import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, field, direction):
        reverse = direction < 0
        self.docs = sorted(self.docs, key=lambda doc: doc.get(field, ""), reverse=reverse)
        return self

    async def to_list(self, length):
        return copy.deepcopy(self.docs[:length])


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])
        self.update_queries = []

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
        return object()

    async def update_one(self, query, update):
        self.update_queries.append(copy.deepcopy(query))
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, query, update)
                return FakeUpdateResult(matched_count=1, modified_count=1)
        return FakeUpdateResult()

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if not projection:
            return projected

        include_fields = {field for field, enabled in projection.items() if enabled and field != "_id"}
        if include_fields:
            return {field: projected[field] for field in include_fields if field in projected}

        for field, enabled in projection.items():
            if enabled == 0:
                projected.pop(field, None)
        return projected

    def _matches(self, doc, query):
        return all(self._matches_key(doc, key, expected) for key, expected in query.items())

    def _matches_key(self, doc, key, expected):
        if key == "steps" and isinstance(expected, dict) and "$elemMatch" in expected:
            return any(self._matches(step, expected["$elemMatch"]) for step in doc.get("steps", []))

        values = self._values_for_key(doc, key)
        if not values:
            return False
        return any(self._matches_value(value, expected) for value in values)

    def _matches_value(self, value, expected):
        if isinstance(expected, dict):
            for operator, operand in expected.items():
                if operator == "$ne" and value == operand:
                    return False
                if operator != "$ne":
                    raise NotImplementedError(f"Unsupported query operator {operator}")
            return True
        return value == expected

    def _values_for_key(self, doc, key):
        parts = key.split(".")
        values = [doc]
        for part in parts:
            next_values = []
            for value in values:
                if isinstance(value, list):
                    next_values.extend(item.get(part) for item in value if isinstance(item, dict) and part in item)
                elif isinstance(value, dict) and part in value:
                    next_values.append(value[part])
            values = next_values
        return values

    def _apply_update(self, doc, query, update):
        positional_step = self._positional_step_index(doc, query)

        for field, value in update.get("$set", {}).items():
            self._set_value(doc, field, value, positional_step)

        for field, value in update.get("$inc", {}).items():
            self._set_value(doc, field, self._single_value(doc, field) + value, positional_step)

        for field, value in update.get("$push", {}).items():
            target = self._single_value(doc, field, positional_step)
            target.append(value)

    def _positional_step_index(self, doc, query):
        if "steps.step_name" in query:
            step_name = query["steps.step_name"]
            return self._find_step_index(doc, lambda step: step.get("step_name") == step_name)

        elem_match = query.get("steps", {}).get("$elemMatch") if isinstance(query.get("steps"), dict) else None
        if elem_match:
            return self._find_step_index(doc, lambda step: self._matches(step, elem_match))

        return None

    def _find_step_index(self, doc, predicate):
        for index, step in enumerate(doc.get("steps", [])):
            if predicate(step):
                return index
        return None

    def _single_value(self, doc, field, positional_step=None):
        if "$" not in field:
            return self._values_for_key(doc, field)[0]

        collection, _, remainder = field.partition(".$.")
        value = doc[collection][positional_step]
        for part in remainder.split("."):
            value = value[part]
        return value

    def _set_value(self, doc, field, value, positional_step=None):
        if "$" in field:
            collection, _, remainder = field.partition(".$.")
            target = doc[collection][positional_step]
            parts = remainder.split(".")
        else:
            target = doc
            parts = field.split(".")

        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value


class FakeDb:
    def __init__(self):
        self.inspections = FakeCollection()
        self.users = FakeCollection()
        self.notifications = FakeCollection()
        self.inspection_progress = FakeCollection()
        self.reports = FakeCollection()
        self.inspector_profiles = FakeCollection()


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDb()
    monkeypatch.setattr(server, "db", db)
    return db


def run(coro):
    return asyncio.run(coro)


def make_inspection(**overrides):
    inspection = {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 0.0,
        "total_amount": 250.0,
        "security_code": "123456",
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }
    inspection.update(overrides)
    return inspection


def make_report():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_accept_inspection_is_status_gated(fake_db):
    fake_db.inspections.docs.append(make_inspection())
    fake_db.users.docs.extend([
        {"id": "inspector-1", "full_name": "Inspector One", "user_type": "inspector"},
        {"id": "inspector-2", "full_name": "Inspector Two", "user_type": "inspector"},
    ])

    accepted = run(server.accept_inspection("inspection-1", "inspector-1"))
    assert accepted["inspector_id"] == "inspector-1"

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-2"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspections.docs[0]["inspector_id"] == "inspector-1"
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspections.update_queries[0] == {"id": "inspection-1", "status": "pending"}


def test_verify_security_code_requires_acceptance_and_is_idempotent(fake_db):
    fake_db.inspections.docs.append(make_inspection())

    with pytest.raises(HTTPException) as exc_info:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspection_progress.docs == []

    fake_db.inspections.docs[0].update({"status": "accepted", "inspector_id": "inspector-1"})
    result = run(server.verify_security_code("inspection-1", "123456"))

    assert result["message"] == "Code verified, inspection started"
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1

    second_result = run(server.verify_security_code("inspection-1", "123456"))

    assert second_result["message"] == "Code already verified"
    assert len(fake_db.inspection_progress.docs) == 1


def test_complete_step_handles_missing_progress_and_replays(fake_db):
    with pytest.raises(HTTPException) as exc_info:
        run(server.complete_step("inspection-1", "exterior_front"))

    assert exc_info.value.status_code == 404

    fake_db.inspection_progress.docs.append(server.build_initial_progress_document("inspection-1"))
    result = run(server.complete_step("inspection-1", "exterior_front", "front ok"))

    assert result["message"] == "Step completed"
    assert fake_db.inspection_progress.docs[0]["current_step"] == 1
    assert fake_db.inspection_progress.docs[0]["steps"][0]["completed"] is True

    replay = run(server.complete_step("inspection-1", "exterior_front", "front ok"))

    assert replay["message"] == "Step already completed"
    assert fake_db.inspection_progress.docs[0]["current_step"] == 1


def test_submit_report_is_idempotent_and_does_not_duplicate_payout(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="in_progress", inspector_id="inspector-1"))
    fake_db.inspector_profiles.docs.append({
        "user_id": "inspector-1",
        "total_inspections": 0,
        "earnings": 0.0,
    })

    first = run(server.submit_report("inspection-1", make_report()))
    second = run(server.submit_report("inspection-1", make_report()))

    assert first["report_id"] == second["report_id"]
    assert second["message"] == "Report already submitted"
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 200.0


def test_upload_photo_rejects_invalid_step_before_writing(fake_db, tmp_path, monkeypatch):
    fake_db.inspections.docs.append(make_inspection(status="in_progress", inspector_id="inspector-1"))
    fake_db.inspection_progress.docs.append(server.build_initial_progress_document("inspection-1"))
    monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)

    upload = UploadFile(filename="photo.jpg", file=BytesIO(b"image-data"))

    with pytest.raises(HTTPException) as exc_info:
        run(server.upload_inspection_photo("inspection-1", "../../../evil", upload))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_inspector_job_lists_do_not_expose_security_codes(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="pending"))
    available = run(server.get_available_inspections())

    assert available
    assert "security_code" not in available[0]

    fake_db.inspections.docs[0].update({"status": "accepted", "inspector_id": "inspector-1"})
    jobs = run(server.get_inspector_jobs("inspector-1"))

    assert jobs
    assert "security_code" not in jobs[0]
