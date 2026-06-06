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
sys.path.append(str(Path(__file__).resolve().parents[1]))

import backend.server as server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction):
        reverse = direction < 0
        self.docs.sort(key=lambda doc: doc.get(key), reverse=reverse)
        return self

    async def to_list(self, limit):
        return copy.deepcopy(self.docs[:limit])


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    def find(self, query, projection=None):
        docs = [self._project(doc, projection) for doc in self.docs if self._matches(doc, query)]
        return FakeCursor(docs)

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, update, query)
                return FakeUpdateResult(1)

        if upsert:
            new_doc = copy.deepcopy(query)
            for key, value in update.get("$setOnInsert", {}).items():
                self._set_path(new_doc, key, copy.deepcopy(value))
            self.docs.append(new_doc)
            return FakeUpdateResult(1)

        return FakeUpdateResult(0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            actual = self._get_path(doc, key)
            if isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
                continue
            if actual != expected:
                return False
        return True

    def _project(self, doc, projection):
        result = copy.deepcopy(doc)
        if not projection:
            return result

        include_keys = {key for key, value in projection.items() if value == 1}
        exclude_keys = {key for key, value in projection.items() if value == 0}

        if include_keys:
            result = {key: self._get_path(doc, key) for key in include_keys if self._get_path(doc, key) is not None}

        for key in exclude_keys:
            result.pop(key, None)
        return result

    def _apply_update(self, doc, update, query):
        for key, value in update.get("$set", {}).items():
            self._set_path(doc, key, copy.deepcopy(value))
        for key, value in update.get("$setOnInsert", {}).items():
            if self._get_path(doc, key) is None:
                self._set_path(doc, key, copy.deepcopy(value))
        for key, value in update.get("$inc", {}).items():
            self._set_path(doc, key, self._get_path(doc, key) + value)
        for key, value in update.get("$push", {}).items():
            self._push_path(doc, key, copy.deepcopy(value), query)

    def _get_path(self, doc, path):
        current = doc
        parts = path.split(".")
        for index, part in enumerate(parts):
            if isinstance(current, list):
                if part.isdigit():
                    current = current[int(part)]
                    continue
                remaining = ".".join(parts[index:])
                for item in current:
                    found = self._get_path(item, remaining)
                    if found is not None:
                        return found
                return None
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _set_path(self, doc, path, value):
        current = doc
        parts = path.split(".")
        for part in parts[:-1]:
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current.setdefault(part, {})
        last = parts[-1]
        if last.isdigit():
            current[int(last)] = value
        else:
            current[last] = value

    def _push_path(self, doc, path, value, query):
        parts = path.split(".")
        if "$" not in parts:
            target = self._get_path(doc, path)
            target.append(value)
            return

        step_name = query.get("steps.step_name")
        if step_name is None:
            raise AssertionError("Fake positional push requires steps.step_name query")

        step_index = next(
            index for index, step in enumerate(doc["steps"]) if step["step_name"] == step_name
        )
        resolved = ".".join(str(step_index) if part == "$" else part for part in parts)
        target = self._get_path(doc, resolved)
        target.append(value)


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.inspections = FakeCollection()
        self.inspection_progress = FakeCollection()
        self.inspector_profiles = FakeCollection()
        self.reports = FakeCollection()
        self.notifications = FakeCollection()


def make_inspection(**overrides):
    doc = {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer",
        "vehicle": {"year": 2024, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298, "city": "Chicago", "state": "IL"},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 25.0,
        "total_amount": 275.0,
        "security_code": "123456",
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
        "created_at": "2026-06-06T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }
    doc.update(overrides)
    return doc


def make_report():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "exterior_front", "completed": True, "photos": [], "notes": "ok"}],
        overall_notes="Looks good",
        recommendation="buy",
    )


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(server, "db", db)
    return db


def test_available_and_inspector_jobs_do_not_expose_security_code(fake_db):
    fake_db.inspections.docs.append(make_inspection(inspector_id="inspector-1"))

    available = run(server.get_available_inspections())
    inspector_jobs = run(server.get_inspector_jobs("inspector-1"))

    assert available
    assert inspector_jobs
    assert "security_code" not in available[0]
    assert "security_code" not in inspector_jobs[0]


def test_accept_inspection_is_status_gated_and_does_not_overwrite_assignment(fake_db):
    fake_db.users.docs.extend([
        {"id": "inspector-1", "full_name": "First Inspector"},
        {"id": "inspector-2", "full_name": "Second Inspector"},
    ])
    fake_db.inspections.docs.append(make_inspection())

    first = run(server.accept_inspection("inspection-1", "inspector-1"))

    with pytest.raises(HTTPException) as exc:
        run(server.accept_inspection("inspection-1", "inspector-2"))

    assert exc.value.status_code == 400
    assert first["inspector_id"] == "inspector-1"
    assert fake_db.inspections.docs[0]["inspector_id"] == "inspector-1"
    assert len(fake_db.notifications.docs) == 1


def test_verify_code_requires_accepted_status_and_is_idempotent(fake_db):
    fake_db.inspections.docs.append(make_inspection())

    with pytest.raises(HTTPException) as exc:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc.value.status_code == 400
    fake_db.inspections.docs[0]["status"] = "accepted"

    run(server.verify_security_code("inspection-1", "123456"))
    run(server.verify_security_code("inspection-1", "123456"))

    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_complete_step_missing_progress_404_and_repeat_does_not_skip_steps(fake_db):
    with pytest.raises(HTTPException) as exc:
        run(server.complete_step("inspection-1", "exterior_front"))

    assert exc.value.status_code == 404

    fake_db.inspection_progress.docs.append(server.build_progress_doc("inspection-1"))
    run(server.complete_step("inspection-1", "exterior_front", "first"))
    run(server.complete_step("inspection-1", "exterior_front", "repeat"))

    progress = fake_db.inspection_progress.docs[0]
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][0]["notes"] == "first"
    assert progress["current_step"] == 1


def test_submit_report_is_idempotent_and_pays_inspector_once(fake_db):
    fake_db.inspections.docs.append(make_inspection(status="in_progress", inspector_id="inspector-1"))
    fake_db.inspector_profiles.docs.append({"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0})

    first = run(server.submit_report("inspection-1", make_report()))
    second = run(server.submit_report("inspection-1", make_report()))

    assert first["report_id"] == second["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 220.0
    assert len(fake_db.notifications.docs) == 1


def test_upload_photo_rejects_invalid_steps_and_sanitizes_extension(fake_db, tmp_path, monkeypatch):
    monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)

    with pytest.raises(HTTPException) as exc:
        run(server.upload_inspection_photo(
            "inspection-1",
            "../../evil",
            type("Upload", (), {"filename": "photo.jpg", "file": io.BytesIO(b"bad")})(),
        ))

    assert exc.value.status_code == 400
    assert not list(tmp_path.iterdir())

    fake_db.inspection_progress.docs.append(server.build_progress_doc("inspection-1"))
    response = run(server.upload_inspection_photo(
        "inspection-1",
        "exterior_front",
        type("Upload", (), {"filename": "../../../shell.php", "file": io.BytesIO(b"image")})(),
    ))

    assert ".." not in response["photo_url"]
    assert response["photo_url"].endswith(".jpg")
    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].parent == tmp_path
