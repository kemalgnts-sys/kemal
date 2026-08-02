import copy
import importlib
import os
import asyncio

import pytest
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
server = importlib.import_module("backend.server")


class FakeUpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [copy.deepcopy(doc) for doc in (docs or [])]

    async def find_one(self, filter_doc, projection=None):
        for doc in self.docs:
            if self._matches(doc, filter_doc):
                return self._project(doc, projection)
        return None

    async def insert_one(self, doc):
        if "_id" in doc and any(existing.get("_id") == doc["_id"] for existing in self.docs):
            raise DuplicateKeyError("duplicate _id")
        self.docs.append(copy.deepcopy(doc))
        return object()

    async def update_one(self, filter_doc, update_doc):
        for doc in self.docs:
            if self._matches(doc, filter_doc):
                self._apply_update(doc, filter_doc, update_doc)
                return FakeUpdateResult(matched_count=1, modified_count=1)
        return FakeUpdateResult()

    def _matches(self, doc, filter_doc):
        return all(self._matches_key(doc, key, expected) for key, expected in filter_doc.items())

    def _matches_key(self, doc, key, expected):
        if key == "steps.step_name":
            return any(step.get("step_name") == expected for step in doc.get("steps", []))

        actual = doc.get(key)
        if isinstance(expected, dict):
            if "$ne" in expected:
                return actual != expected["$ne"]
            raise AssertionError(f"Unsupported operator in test fake: {expected}")
        return actual == expected

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection and projection.get("_id") == 0:
            projected.pop("_id", None)
        return projected

    def _apply_update(self, doc, filter_doc, update_doc):
        for key, value in update_doc.get("$set", {}).items():
            if key.startswith("steps.$."):
                step_name = filter_doc["steps.step_name"]
                field = key.split(".", 2)[2]
                for step in doc["steps"]:
                    if step["step_name"] == step_name:
                        step[field] = value
                        break
            else:
                doc[key] = value

        for key, value in update_doc.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value


class FakeDB:
    def __init__(self):
        self.inspections = FakeCollection()
        self.inspection_progress = FakeCollection()
        self.reports = FakeCollection()
        self.inspector_profiles = FakeCollection()
        self.notifications = FakeCollection()
        self.users = FakeCollection()


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(server, "db", db)
    return db


def inspection_doc(status="in_progress"):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "inspector_id": "inspector-1",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "total_amount": 100.0,
        "security_code": "123456",
        "status": status,
    }


def report_payload():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "exterior_front", "completed": True}],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_submit_report_is_idempotent_for_retries(fake_db):
    asyncio.run(_submit_report_is_idempotent_for_retries(fake_db))


async def _submit_report_is_idempotent_for_retries(fake_db):
    fake_db.inspections.docs.append(inspection_doc())
    fake_db.inspector_profiles.docs.append(
        {"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}
    )

    first = await server.submit_report("inspection-1", report_payload())
    second = await server.submit_report("inspection-1", report_payload())

    assert second["report_id"] == first["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 80.0


def test_complete_step_rejects_invalid_step_without_advancing(fake_db):
    asyncio.run(_complete_step_rejects_invalid_step_without_advancing(fake_db))


async def _complete_step_rejects_invalid_step_without_advancing(fake_db):
    fake_db.inspection_progress.docs.append(
        {
            "inspection_id": "inspection-1",
            "current_step": 0,
            "steps": [
                {
                    "step_name": "exterior_front",
                    "completed": False,
                    "notes": "",
                    "photos": [],
                },
                {
                    "step_name": "exterior_sides",
                    "completed": False,
                    "notes": "",
                    "photos": [],
                },
            ],
        }
    )

    await server.complete_step("inspection-1", "exterior_front", "front ok")
    await server.complete_step("inspection-1", "exterior_front", "front still ok")

    with pytest.raises(HTTPException) as exc_info:
        await server.complete_step("inspection-1", "not_a_real_step", "bad")

    assert exc_info.value.status_code == 400
    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][0]["notes"] == "front still ok"


def test_verify_security_code_does_not_duplicate_or_reset_progress(fake_db):
    asyncio.run(_verify_security_code_does_not_duplicate_or_reset_progress(fake_db))


async def _verify_security_code_does_not_duplicate_or_reset_progress(fake_db):
    fake_db.inspections.docs.append(inspection_doc(status="accepted"))

    await server.verify_security_code("inspection-1", "123456")
    fake_db.inspection_progress.docs[0]["current_step"] = 2
    await server.verify_security_code("inspection-1", "123456")

    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1
    assert fake_db.inspection_progress.docs[0]["current_step"] == 2
