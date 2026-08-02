import asyncio
import copy
import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, _limit):
        return copy.deepcopy(self.docs)


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    async def find_one(self, filter_doc, projection=None):
        for doc in self.docs:
            if self._matches(doc, filter_doc):
                return self._project(doc, projection)
        return None

    def find(self, filter_doc, projection=None):
        return FakeCursor([
            self._project(doc, projection)
            for doc in self.docs
            if self._matches(doc, filter_doc)
        ])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return object()

    async def update_one(self, filter_doc, update_doc):
        for doc in self.docs:
            matched_array_index = self._matched_array_index(doc, filter_doc)
            if not self._matches(doc, filter_doc):
                continue

            before = copy.deepcopy(doc)
            for key, value in update_doc.get("$set", {}).items():
                self._set_value(doc, key, value, matched_array_index)
            for key, value in update_doc.get("$inc", {}).items():
                self._set_value(doc, key, self._get_value(doc, key) + value, matched_array_index)

            return FakeUpdateResult(
                matched_count=1,
                modified_count=1 if doc != before else 0,
            )
        return FakeUpdateResult()

    def _matches(self, doc, filter_doc):
        for key, expected in filter_doc.items():
            if key == "steps" and isinstance(expected, dict) and "$elemMatch" in expected:
                if not any(self._matches(step, expected["$elemMatch"]) for step in doc.get("steps", [])):
                    return False
                continue

            actual = self._get_value(doc, key)
            if isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    def _matched_array_index(self, doc, filter_doc):
        elem_match = filter_doc.get("steps", {}).get("$elemMatch") if isinstance(filter_doc.get("steps"), dict) else None
        if not elem_match:
            return None
        for index, step in enumerate(doc.get("steps", [])):
            if self._matches(step, elem_match):
                return index
        return None

    def _project(self, doc, projection):
        result = copy.deepcopy(doc)
        if not projection:
            return result

        include_keys = [key for key, value in projection.items() if value == 1]
        if include_keys:
            return {key: copy.deepcopy(doc[key]) for key in include_keys if key in doc}

        for key, value in projection.items():
            if value == 0:
                result.pop(key, None)
        return result

    def _get_value(self, doc, dotted_key):
        current = doc
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _set_value(self, doc, dotted_key, value, matched_array_index=None):
        parts = dotted_key.split(".")
        current = doc
        for index, part in enumerate(parts[:-1]):
            if part == "$":
                part = matched_array_index
            current = current[part]
        current[parts[-1]] = value


class FakeDb:
    def __init__(self, **collections):
        self.inspections = FakeCollection(collections.get("inspections"))
        self.inspection_progress = FakeCollection(collections.get("inspection_progress"))
        self.reports = FakeCollection(collections.get("reports"))
        self.inspector_profiles = FakeCollection(collections.get("inspector_profiles"))
        self.notifications = FakeCollection(collections.get("notifications"))
        self.users = FakeCollection(collections.get("users"))


def completed_steps():
    steps = []
    for step in server.INSPECTION_STEPS:
        steps.append({
            "step_name": step["step_name"],
            "description": step["description"],
            "required_photos": step["required_photos"],
            "completed": True,
            "photos": [f"/uploads/{step['step_name']}.jpg"],
            "notes": f"{step['step_name']} ok",
        })
    return steps


def incomplete_steps():
    return [
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


def make_inspection(status="in_progress", inspector_id="inspector-1"):
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
        "inspector_name": "Inspector",
        "created_at": "2026-05-24T00:00:00+00:00",
        "accepted_at": "2026-05-24T00:00:00+00:00",
        "completed_at": None,
    }


def test_submit_report_is_idempotent_and_uses_authoritative_progress():
    progress_steps = completed_steps()
    server.db = FakeDb(
        inspections=[make_inspection()],
        inspection_progress=[{
            "inspection_id": "inspection-1",
            "current_step": len(server.INSPECTION_STEPS) - 1,
            "steps": progress_steps,
        }],
        inspector_profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    stale_report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "stale", "photos": []}],
        overall_notes="Looks good",
        recommendation="buy",
    )

    first = asyncio.run(server.submit_report("inspection-1", stale_report))
    second = asyncio.run(server.submit_report("inspection-1", stale_report))

    assert first["report_id"] == second["report_id"]
    assert len(server.db.reports.docs) == 1
    assert server.db.reports.docs[0]["steps"] == progress_steps
    assert server.db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert server.db.inspector_profiles.docs[0]["earnings"] == 216.0


def test_verify_code_requires_acceptance_and_is_idempotent():
    server.db = FakeDb(inspections=[make_inspection(status="pending", inspector_id=None)])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(server.verify_security_code("inspection-1", "123456"))

    assert exc_info.value.status_code == 400
    assert server.db.inspections.docs[0]["status"] == "pending"
    assert server.db.inspection_progress.docs == []

    server.db = FakeDb(inspections=[make_inspection(status="accepted")])

    asyncio.run(server.verify_security_code("inspection-1", "123456"))
    asyncio.run(server.verify_security_code("inspection-1", "123456"))

    assert server.db.inspections.docs[0]["status"] == "in_progress"
    assert len(server.db.inspection_progress.docs) == 1


def test_complete_step_does_not_skip_on_duplicate_or_wrong_step():
    server.db = FakeDb(
        inspection_progress=[{
            "inspection_id": "inspection-1",
            "current_step": 0,
            "steps": incomplete_steps(),
        }]
    )

    asyncio.run(server.complete_step("inspection-1", "exterior_front", "front ok"))
    asyncio.run(server.complete_step("inspection-1", "exterior_front", "duplicate"))

    progress = server.db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][0]["notes"] == "front ok"

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(server.complete_step("inspection-1", "exterior_rear", "wrong"))

    assert exc_info.value.status_code == 400
    assert progress["current_step"] == 1
    assert progress["steps"][2]["completed"] is False


def test_available_inspections_do_not_leak_security_code():
    server.db = FakeDb(inspections=[make_inspection(status="pending", inspector_id=None)])

    jobs = asyncio.run(server.get_available_inspections())

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]
