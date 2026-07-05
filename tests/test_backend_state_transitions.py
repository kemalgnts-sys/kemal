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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import server  # noqa: E402


class FakeResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, _limit):
        return [copy.deepcopy(doc) for doc in self.docs]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [copy.deepcopy(doc) for doc in (docs or [])]

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
        return FakeResult(matched_count=1, modified_count=1)

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, update, query)
                return FakeResult(matched_count=1, modified_count=1)

        if upsert:
            doc = copy.deepcopy(update.get("$setOnInsert", {}))
            self._apply_update(doc, {k: v for k, v in update.items() if k != "$setOnInsert"}, query)
            self.docs.append(doc)
            return FakeResult(matched_count=0, modified_count=0)

        return FakeResult()

    async def find_one_and_update(self, query, update, projection=None, return_document=None):
        for doc in self.docs:
            if self._matches(doc, query):
                before = copy.deepcopy(doc)
                self._apply_update(doc, update, query)
                selected = doc if return_document == server.ReturnDocument.AFTER else before
                return self._project(selected, projection)
        return None

    def _matches(self, doc, query):
        for key, expected in query.items():
            if key == "steps" and "$elemMatch" in expected:
                if not any(self._matches(step, expected["$elemMatch"]) for step in doc.get("steps", [])):
                    return False
                continue

            values = self._values_for_path(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected:
                    if any(value == expected["$ne"] for value in values):
                        return False
                else:
                    raise AssertionError(f"Unsupported query operator: {expected}")
            elif expected not in values:
                return False
        return True

    def _values_for_path(self, value, path):
        parts = path.split(".")
        values = [value]
        for part in parts:
            next_values = []
            for item in values:
                if isinstance(item, list):
                    next_values.extend(element.get(part) for element in item if isinstance(element, dict) and part in element)
                elif isinstance(item, dict) and part in item:
                    next_values.append(item[part])
            values = next_values
        return values

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if not projection:
            return projected

        if any(value == 1 for value in projection.values()):
            included = {
                key: copy.deepcopy(projected[key])
                for key, value in projection.items()
                if value == 1 and key in projected
            }
            if projection.get("_id") != 0 and "_id" in projected:
                included["_id"] = projected["_id"]
            return included

        for key, value in projection.items():
            if value == 0:
                projected.pop(key, None)
        return projected

    def _apply_update(self, doc, update, query):
        for path, value in update.get("$set", {}).items():
            self._set_path(doc, path, value, query)
        for path, value in update.get("$inc", {}).items():
            doc[path] = doc.get(path, 0) + value
        for path, value in update.get("$push", {}).items():
            self._push_path(doc, path, value, query)

    def _target_step_name(self, query):
        if "steps.step_name" in query:
            return query["steps.step_name"]
        if "steps" in query and "$elemMatch" in query["steps"]:
            return query["steps"]["$elemMatch"].get("step_name")
        return None

    def _set_path(self, doc, path, value, query):
        if path.startswith("steps.$."):
            field = path.split(".", 2)[2]
            step_name = self._target_step_name(query)
            for step in doc["steps"]:
                if step["step_name"] == step_name:
                    step[field] = value
                    return
            raise AssertionError(f"Step not found for update: {step_name}")
        doc[path] = value

    def _push_path(self, doc, path, value, query):
        if path.startswith("steps.$."):
            field = path.split(".", 2)[2]
            step_name = self._target_step_name(query)
            for step in doc["steps"]:
                if step["step_name"] == step_name:
                    step.setdefault(field, []).append(value)
                    return
            raise AssertionError(f"Step not found for update: {step_name}")
        doc.setdefault(path, []).append(value)


class FakeDB:
    def __init__(self, **collections):
        self.users = FakeCollection(collections.get("users"))
        self.inspections = FakeCollection(collections.get("inspections"))
        self.notifications = FakeCollection(collections.get("notifications"))
        self.inspection_progress = FakeCollection(collections.get("inspection_progress"))
        self.reports = FakeCollection(collections.get("reports"))
        self.inspector_profiles = FakeCollection(collections.get("inspector_profiles"))


def run(coro):
    return asyncio.run(coro)


def inspection_doc(status="pending", inspector_id=None):
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
        "inspector_id": inspector_id,
        "inspector_name": "Inspector One" if inspector_id else None,
        "created_at": "2026-06-09T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }


def progress_doc():
    return {
        "inspection_id": "inspection-1",
        "steps": [
            {
                "step_name": step["step_name"],
                "description": step["description"],
                "required_photos": step["required_photos"],
                "completed": False,
                "photos": [],
                "notes": "",
            }
            for step in server.INSPECTION_STEPS
        ],
        "current_step": 0,
        "started_at": "2026-06-09T00:00:00+00:00",
    }


def inspector(user_id="inspector-1", name="Inspector One"):
    return {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "full_name": name,
        "phone": "+15555550123",
        "user_type": "inspector",
        "is_verified": True,
        "created_at": "2026-06-09T00:00:00+00:00",
    }


def report_payload():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "exterior_front", "completed": True}],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_inspector_surfaces_do_not_leak_security_code_and_accept_is_atomic():
    db = FakeDB(
        users=[inspector(), inspector("inspector-2", "Inspector Two")],
        inspections=[inspection_doc()],
    )
    server.db = db

    async def scenario():
        available = await server.get_available_inspections()
        assert available
        assert "security_code" not in available[0]

        accepted = await server.accept_inspection("inspection-1", "inspector-1")
        assert accepted["status"] == "accepted"
        assert accepted["inspector_id"] == "inspector-1"
        assert "security_code" not in accepted

        with pytest.raises(HTTPException) as exc:
            await server.accept_inspection("inspection-1", "inspector-2")
        assert exc.value.status_code == 400
        assert len(db.notifications.docs) == 1

        jobs = await server.get_inspector_jobs("inspector-1")
        assert jobs
        assert "security_code" not in jobs[0]

    run(scenario())


def test_verify_code_is_idempotent_and_does_not_duplicate_progress():
    db = FakeDB(inspections=[inspection_doc(status="accepted", inspector_id="inspector-1")])
    server.db = db

    async def scenario():
        first = await server.verify_security_code("inspection-1", "123456")
        second = await server.verify_security_code("inspection-1", "123456")

        assert first["message"] == "Code verified, inspection started"
        assert second["message"] == "Code verified, inspection already started"
        assert db.inspections.docs[0]["status"] == "in_progress"
        assert len(db.inspection_progress.docs) == 1

    run(scenario())


def test_complete_step_rejects_invalid_or_out_of_order_steps_without_advancing():
    db = FakeDB(inspection_progress=[progress_doc()])
    server.db = db

    async def scenario():
        with pytest.raises(HTTPException) as invalid:
            await server.complete_step("inspection-1", "../bad-step")
        assert invalid.value.status_code == 400
        assert db.inspection_progress.docs[0]["current_step"] == 0

        with pytest.raises(HTTPException) as out_of_order:
            await server.complete_step("inspection-1", "engine")
        assert out_of_order.value.status_code == 400
        assert db.inspection_progress.docs[0]["current_step"] == 0

        completed = await server.complete_step("inspection-1", "exterior_front", "Front looks good")
        assert completed["message"] == "Step completed"
        assert db.inspection_progress.docs[0]["current_step"] == 1
        assert db.inspection_progress.docs[0]["steps"][0]["completed"] is True

        retry = await server.complete_step("inspection-1", "exterior_front", "Front looks good")
        assert retry["message"] == "Step already completed"
        assert db.inspection_progress.docs[0]["current_step"] == 1

    run(scenario())


def test_upload_photo_rejects_invalid_step_or_extension():
    db = FakeDB(inspection_progress=[progress_doc()])
    server.db = db

    async def scenario():
        with pytest.raises(HTTPException) as invalid_step:
            await server.upload_inspection_photo(
                "inspection-1",
                "../bad-step",
                SimpleNamespace(filename="photo.jpg", file=io.BytesIO(b"image")),
            )
        assert invalid_step.value.status_code == 400
        assert db.inspection_progress.docs[0]["steps"][0]["photos"] == []

        with pytest.raises(HTTPException) as invalid_extension:
            await server.upload_inspection_photo(
                "inspection-1",
                "exterior_front",
                SimpleNamespace(filename="photo.exe", file=io.BytesIO(b"image")),
            )
        assert invalid_extension.value.status_code == 400
        assert db.inspection_progress.docs[0]["steps"][0]["photos"] == []

    run(scenario())


def test_submit_report_replay_does_not_duplicate_reports_or_earnings():
    db = FakeDB(
        inspections=[inspection_doc(status="in_progress", inspector_id="inspector-1")],
        inspector_profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    server.db = db

    async def scenario():
        first = await server.submit_report("inspection-1", report_payload())
        second = await server.submit_report("inspection-1", report_payload())

        assert first["report_id"] == second["report_id"]
        assert len(db.reports.docs) == 1
        assert len(db.notifications.docs) == 1
        assert db.inspector_profiles.docs[0]["total_inspections"] == 1
        assert db.inspector_profiles.docs[0]["earnings"] == 216.0

    run(scenario())
