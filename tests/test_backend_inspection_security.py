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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import server


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction):
        reverse = direction < 0
        self.docs = sorted(self.docs, key=lambda doc: doc.get(key, ""), reverse=reverse)
        return self

    async def to_list(self, length):
        return copy.deepcopy(self.docs[:length])


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

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                before = copy.deepcopy(doc)
                self._apply_update(doc, query, update)
                return SimpleNamespace(matched_count=1, modified_count=int(doc != before))
        return SimpleNamespace(matched_count=0, modified_count=0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            if "." in key:
                first, rest = key.split(".", 1)
                values = doc.get(first, [])
                if not any(item.get(rest) == expected for item in values):
                    return False
                continue
            actual = doc.get(key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    def _project(self, doc, projection):
        result = copy.deepcopy(doc)
        if not projection:
            return result
        includes = {key for key, value in projection.items() if value == 1}
        excludes = {key for key, value in projection.items() if value == 0}
        if includes:
            result = {key: result[key] for key in includes if key in result}
        for key in excludes:
            result.pop(key, None)
        return result

    def _apply_update(self, doc, query, update):
        for key, value in update.get("$set", {}).items():
            if key.startswith("steps.$."):
                field = key.split(".", 2)[2]
                step_name = query.get("steps.step_name")
                for step in doc.get("steps", []):
                    if step.get("step_name") == step_name:
                        step[field] = value
                        break
            else:
                doc[key] = value
        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value
        for key, value in update.get("$push", {}).items():
            if key.startswith("steps.$."):
                field = key.split(".", 2)[2]
                step_name = query.get("steps.step_name")
                for step in doc.get("steps", []):
                    if step.get("step_name") == step_name:
                        step.setdefault(field, []).append(value)
                        break
            else:
                doc.setdefault(key, []).append(value)


class FakeDb:
    def __init__(self, *, users=None, profiles=None, inspections=None, progress=None, reports=None):
        self.users = FakeCollection(users)
        self.inspector_profiles = FakeCollection(profiles)
        self.inspections = FakeCollection(inspections)
        self.inspection_progress = FakeCollection(progress)
        self.reports = FakeCollection(reports)
        self.notifications = FakeCollection([])


@pytest.fixture(autouse=True)
def restore_db():
    original_db = server.db
    yield
    server.db = original_db


def inspection_doc(status="pending", inspector_id=None):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {
            "name": "Seller",
            "phone": "+15555550100",
            "address": "1 Main St",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601",
            "lat": 41.8781,
            "lng": -87.6298,
        },
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": inspector_id,
        "inspector_name": "Inspector One" if inspector_id else None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "accepted_at": "2026-01-01T01:00:00+00:00" if inspector_id else None,
        "completed_at": None,
    }


def verified_inspector(user_id="inspector-1"):
    return (
        {
            "id": user_id,
            "email": f"{user_id}@example.com",
            "password": "secret",
            "full_name": "Inspector One",
            "phone": "+15555550101",
            "user_type": "inspector",
            "is_verified": True,
            "created_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "user_id": user_id,
            "id_verified": True,
            "location_lat": 41.8781,
            "location_lng": -87.6298,
            "radius_miles": 50,
            "total_inspections": 0,
            "rating": 5.0,
            "earnings": 0.0,
        },
    )


def test_inspector_job_responses_do_not_expose_security_code():
    asyncio.run(_test_inspector_job_responses_do_not_expose_security_code())


async def _test_inspector_job_responses_do_not_expose_security_code():
    user, profile = verified_inspector()
    server.db = FakeDb(
        users=[user],
        profiles=[profile],
        inspections=[
            inspection_doc(status="pending"),
            inspection_doc(status="accepted", inspector_id="inspector-1"),
        ],
    )

    available_jobs = await server.get_available_inspections()
    my_jobs = await server.get_inspector_jobs("inspector-1")

    assert available_jobs
    assert my_jobs
    assert all("security_code" not in job for job in available_jobs)
    assert all("security_code" not in job for job in my_jobs)


def test_accept_requires_verified_inspector_and_atomic_pending_status():
    asyncio.run(_test_accept_requires_verified_inspector_and_atomic_pending_status())


async def _test_accept_requires_verified_inspector_and_atomic_pending_status():
    inspector, profile = verified_inspector()
    second_inspector, second_profile = verified_inspector("inspector-2")
    buyer = {
        **inspector,
        "id": "buyer-2",
        "email": "buyer@example.com",
        "user_type": "buyer",
        "full_name": "Buyer Two",
    }
    server.db = FakeDb(
        users=[buyer, inspector, second_inspector],
        profiles=[profile, second_profile],
        inspections=[inspection_doc(status="pending")],
    )

    with pytest.raises(HTTPException) as buyer_error:
        await server.accept_inspection("inspection-1", "buyer-2")
    assert buyer_error.value.status_code == 403

    accepted = await server.accept_inspection("inspection-1", "inspector-1")
    assert accepted["inspector_id"] == "inspector-1"
    assert "security_code" not in accepted

    with pytest.raises(HTTPException) as second_accept_error:
        await server.accept_inspection("inspection-1", "inspector-2")
    assert second_accept_error.value.status_code == 400

    stored = await server.db.inspections.find_one({"id": "inspection-1"})
    assert stored["inspector_id"] == "inspector-1"
    assert len(server.db.notifications.docs) == 1


def test_verify_code_requires_assignment_and_is_idempotent():
    asyncio.run(_test_verify_code_requires_assignment_and_is_idempotent())


async def _test_verify_code_requires_assignment_and_is_idempotent():
    inspector, profile = verified_inspector()
    other_inspector, other_profile = verified_inspector("inspector-2")
    server.db = FakeDb(
        users=[inspector, other_inspector],
        profiles=[profile, other_profile],
        inspections=[inspection_doc(status="accepted", inspector_id="inspector-1")],
    )

    with pytest.raises(HTTPException) as wrong_inspector_error:
        await server.verify_security_code("inspection-1", "123456", "inspector-2")
    assert wrong_inspector_error.value.status_code == 403

    started = await server.verify_security_code("inspection-1", "123456", "inspector-1")
    repeated = await server.verify_security_code("inspection-1", "123456", "inspector-1")

    assert started["steps"] == server.INSPECTION_STEPS
    assert repeated["steps"] == server.INSPECTION_STEPS
    stored = await server.db.inspections.find_one({"id": "inspection-1"})
    assert stored["status"] == "in_progress"
    assert len(server.db.inspection_progress.docs) == 1


def test_submit_report_cannot_duplicate_payout_or_reports():
    asyncio.run(_test_submit_report_cannot_duplicate_payout_or_reports())


async def _test_submit_report_cannot_duplicate_payout_or_reports():
    inspector, profile = verified_inspector()
    server.db = FakeDb(
        users=[inspector],
        profiles=[profile],
        inspections=[inspection_doc(status="in_progress", inspector_id="inspector-1")],
    )
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )

    first = await server.submit_report("inspection-1", report, "inspector-1")
    second = await server.submit_report("inspection-1", report, "inspector-1")

    assert first["report_id"] == second["report_id"]
    assert len(server.db.reports.docs) == 1
    assert len(server.db.notifications.docs) == 1
    stored_profile = await server.db.inspector_profiles.find_one({"user_id": "inspector-1"})
    assert stored_profile["total_inspections"] == 1
    assert stored_profile["earnings"] == 216.0


def test_complete_step_retry_does_not_skip_required_steps():
    asyncio.run(_test_complete_step_retry_does_not_skip_required_steps())


async def _test_complete_step_retry_does_not_skip_required_steps():
    first_step = server.build_progress_doc("inspection-1")
    server.db = FakeDb(progress=[first_step])

    await server.complete_step("inspection-1", "exterior_front", "done")
    retry_result = await server.complete_step("inspection-1", "exterior_front", "duplicate")
    assert retry_result == {"message": "Step already completed"}
    await server.complete_step("inspection-1", "exterior_sides", "done")

    progress = await server.db.inspection_progress.find_one({"inspection_id": "inspection-1"})
    assert progress["current_step"] == 2
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][1]["completed"] is True
