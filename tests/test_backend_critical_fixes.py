import asyncio
import copy
import io
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import server  # noqa: E402


class UpdateResult:
    def __init__(self, modified_count=0):
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, limit):
        return copy.deepcopy(self.docs[:limit])


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
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, query, update, inserting=False)
                return UpdateResult(1)

        if upsert:
            doc = {
                key: value
                for key, value in query.items()
                if "." not in key and not isinstance(value, dict)
            }
            self._apply_update(doc, query, update, inserting=True)
            self.docs.append(doc)
        return UpdateResult(0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            values = self._values_for_key(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected and any(value == expected["$ne"] for value in values):
                    return False
                continue
            if expected not in values:
                return False
        return True

    def _values_for_key(self, doc, dotted_key):
        parts = dotted_key.split(".")
        values = [doc]
        for part in parts:
            next_values = []
            for value in values:
                if isinstance(value, list):
                    next_values.extend(item.get(part) for item in value if isinstance(item, dict))
                elif isinstance(value, dict) and part in value:
                    next_values.append(value[part])
            values = next_values
        return values

    def _project(self, doc, projection):
        result = copy.deepcopy(doc)
        if not projection:
            return result

        included = {key for key, value in projection.items() if value == 1}
        excluded = {key for key, value in projection.items() if value == 0}

        if included:
            result = {key: copy.deepcopy(doc[key]) for key in included if key in doc}
            excluded.add("_id")
        for key in excluded:
            result.pop(key, None)
        return result

    def _apply_update(self, doc, query, update, inserting):
        if inserting:
            for key, value in update.get("$setOnInsert", {}).items():
                doc[key] = copy.deepcopy(value)

        for key, value in update.get("$set", {}).items():
            self._set_value(doc, query, key, value)
        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value
        for key, value in update.get("$push", {}).items():
            target = self._get_array_for_push(doc, query, key)
            target.append(copy.deepcopy(value))

    def _set_value(self, doc, query, dotted_key, value):
        if dotted_key.startswith("steps.$."):
            step = self._matching_step(doc, query)
            step[dotted_key.removeprefix("steps.$.")] = copy.deepcopy(value)
            return

        parts = dotted_key.split(".")
        target = doc
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = copy.deepcopy(value)

    def _get_array_for_push(self, doc, query, dotted_key):
        if dotted_key.startswith("steps.$."):
            step = self._matching_step(doc, query)
            field = dotted_key.removeprefix("steps.$.")
            return step.setdefault(field, [])
        return doc.setdefault(dotted_key, [])

    def _matching_step(self, doc, query):
        step_name = query.get("steps.step_name")
        for step in doc.get("steps", []):
            if step.get("step_name") == step_name:
                return step
        raise AssertionError(f"No matching step for {step_name}")


class FakeDb:
    def __init__(self):
        self.inspections = FakeCollection()
        self.users = FakeCollection()
        self.notifications = FakeCollection()
        self.inspection_progress = FakeCollection()
        self.reports = FakeCollection()
        self.inspector_profiles = FakeCollection()


def make_inspection(status="pending", inspector_id=None):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 0,
        "total_amount": 250.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": inspector_id,
        "inspector_name": "Inspector" if inspector_id else None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }


def make_report():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_available_inspections_do_not_leak_security_codes(monkeypatch):
    async def run():
        fake_db = FakeDb()
        fake_db.inspections.docs.append(make_inspection())
        monkeypatch.setattr(server, "db", fake_db)

        jobs = await server.get_available_inspections()

        assert len(jobs) == 1
        assert "security_code" not in jobs[0]

    asyncio.run(run())


def test_accept_inspection_is_status_gated(monkeypatch):
    async def run():
        fake_db = FakeDb()
        fake_db.inspections.docs.append(make_inspection())
        fake_db.users.docs.extend([
            {"id": "inspector-1", "full_name": "Inspector One"},
            {"id": "inspector-2", "full_name": "Inspector Two"},
        ])
        monkeypatch.setattr(server, "db", fake_db)

        accepted = await server.accept_inspection("inspection-1", "inspector-1")
        assert accepted["inspector_id"] == "inspector-1"

        with pytest.raises(HTTPException) as exc:
            await server.accept_inspection("inspection-1", "inspector-2")

        assert exc.value.status_code == 400
        assert fake_db.inspections.docs[0]["inspector_id"] == "inspector-1"
        assert len(fake_db.notifications.docs) == 1

    asyncio.run(run())


def test_verify_security_code_requires_accepted_job_and_is_idempotent(monkeypatch):
    async def run():
        fake_db = FakeDb()
        fake_db.inspections.docs.append(make_inspection(status="pending"))
        monkeypatch.setattr(server, "db", fake_db)

        with pytest.raises(HTTPException) as exc:
            await server.verify_security_code("inspection-1", "123456")
        assert exc.value.status_code == 400
        assert fake_db.inspection_progress.docs == []

        fake_db.inspections.docs[0]["status"] = "accepted"
        await server.verify_security_code("inspection-1", "123456")
        await server.verify_security_code("inspection-1", "123456")

        assert fake_db.inspections.docs[0]["status"] == "in_progress"
        assert len(fake_db.inspection_progress.docs) == 1

    asyncio.run(run())


def test_complete_step_requires_progress_and_retries_do_not_advance(monkeypatch):
    async def run():
        fake_db = FakeDb()
        monkeypatch.setattr(server, "db", fake_db)

        with pytest.raises(HTTPException) as exc:
            await server.complete_step("inspection-1", "exterior_front")
        assert exc.value.status_code == 400

        fake_db.inspection_progress.docs.append({
            "inspection_id": "inspection-1",
            "steps": server.build_progress_steps(),
            "current_step": 0,
        })

        await server.complete_step("inspection-1", "exterior_front", "first pass")
        await server.complete_step("inspection-1", "exterior_front", "retry")

        progress = fake_db.inspection_progress.docs[0]
        assert progress["current_step"] == 1
        assert progress["steps"][0]["completed"] is True
        assert progress["steps"][0]["notes"] == "first pass"

    asyncio.run(run())


def test_submit_report_is_status_gated_and_does_not_double_pay(monkeypatch):
    async def run():
        fake_db = FakeDb()
        fake_db.inspections.docs.append(make_inspection(status="in_progress", inspector_id="inspector-1"))
        fake_db.inspection_progress.docs.append({
            "inspection_id": "inspection-1",
            "steps": server.build_progress_steps(),
            "current_step": 0,
        })
        fake_db.inspector_profiles.docs.append({
            "user_id": "inspector-1",
            "total_inspections": 0,
            "earnings": 0.0,
        })
        monkeypatch.setattr(server, "db", fake_db)

        first = await server.submit_report("inspection-1", make_report())
        second = await server.submit_report("inspection-1", make_report())

        assert first["report_id"] == second["report_id"]
        assert len(fake_db.reports.docs) == 1
        assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
        assert fake_db.inspector_profiles.docs[0]["earnings"] == 200.0

    asyncio.run(run())


def test_upload_photo_rejects_path_traversal_step_and_sanitizes_extension(monkeypatch, tmp_path):
    async def run():
        fake_db = FakeDb()
        fake_db.inspection_progress.docs.append({
            "inspection_id": "../inspection-1",
            "steps": server.build_progress_steps(),
            "current_step": 0,
        })
        monkeypatch.setattr(server, "db", fake_db)
        monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)

        malicious_file = SimpleNamespace(filename="photo.jpg", file=io.BytesIO(b"bad"))
        with pytest.raises(HTTPException) as exc:
            await server.upload_inspection_photo("../inspection-1", "../../escape", malicious_file)
        assert exc.value.status_code == 400
        assert list(tmp_path.iterdir()) == []

        unsafe_extension_file = SimpleNamespace(filename="../../payload.py", file=io.BytesIO(b"ok"))
        response = await server.upload_inspection_photo("../inspection-1", "exterior_front", unsafe_extension_file)

        assert ".." not in response["photo_url"]
        assert response["photo_url"].endswith(".jpg")
        written_files = list(tmp_path.iterdir())
        assert len(written_files) == 1
        assert written_files[0].parent == tmp_path

    asyncio.run(run())
