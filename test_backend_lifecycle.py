import asyncio
import copy
import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server  # noqa: E402


class UpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if matches(doc, query):
                return project(doc, projection)
        return None

    async def update_one(self, query, update):
        for doc in self.docs:
            if matches(doc, query):
                apply_update(doc, update)
                return UpdateResult(1)
        return UpdateResult(0)

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return object()


class FakeDb:
    def __init__(self, **collections):
        for name, docs in collections.items():
            setattr(self, name, FakeCollection(docs))


def get_path(doc, path):
    value = doc
    for part in path.split("."):
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value.get(part)
        if value is None:
            return None
    return value


def set_path(doc, path, new_value):
    target = doc
    parts = path.split(".")
    for part in parts[:-1]:
        if isinstance(target, list):
            target = target[int(part)]
        else:
            target = target[part]

    last = parts[-1]
    if isinstance(target, list):
        target[int(last)] = new_value
    else:
        target[last] = new_value


def matches(doc, query):
    for key, expected in query.items():
        actual = get_path(doc, key)
        if isinstance(expected, dict):
            if "$ne" in expected and actual == expected["$ne"]:
                return False
        elif actual != expected:
            return False
    return True


def project(doc, projection):
    copied = copy.deepcopy(doc)
    if not projection:
        return copied

    if all(value == 0 for value in projection.values()):
        for key, value in projection.items():
            if value == 0:
                copied.pop(key, None)
        return copied

    return {key: get_path(copied, key) for key, value in projection.items() if value == 1}


def apply_update(doc, update):
    for key, value in update.get("$set", {}).items():
        set_path(doc, key, copy.deepcopy(value))

    for key, value in update.get("$inc", {}).items():
        set_path(doc, key, get_path(doc, key) + value)


def run(coro):
    return asyncio.run(coro)


def set_fake_db(monkeypatch, **collections):
    fake_db = FakeDb(
        inspections=collections.get("inspections", []),
        users=collections.get("users", []),
        notifications=collections.get("notifications", []),
        inspection_progress=collections.get("inspection_progress", []),
        reports=collections.get("reports", []),
        inspector_profiles=collections.get("inspector_profiles", []),
    )
    monkeypatch.setattr(server, "db", fake_db)
    return fake_db


def test_accept_inspection_is_atomic(monkeypatch):
    fake_db = set_fake_db(
        monkeypatch,
        inspections=[{
            "id": "inspection-1",
            "buyer_id": "buyer-1",
            "status": "pending",
        }],
        users=[
            {"id": "inspector-1", "full_name": "First Inspector"},
            {"id": "inspector-2", "full_name": "Second Inspector"},
        ],
    )

    run(server.accept_inspection("inspection-1", "inspector-1"))

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-2"))

    assert exc_info.value.status_code == 400
    inspection = fake_db.inspections.docs[0]
    assert inspection["inspector_id"] == "inspector-1"
    assert len(fake_db.notifications.docs) == 1


def test_verify_security_code_does_not_duplicate_progress(monkeypatch):
    fake_db = set_fake_db(
        monkeypatch,
        inspections=[{
            "id": "inspection-1",
            "security_code": "123456",
            "status": "accepted",
        }],
    )

    first_response = run(server.verify_security_code("inspection-1", "123456"))
    second_response = run(server.verify_security_code("inspection-1", "123456"))

    assert first_response["steps"] == second_response["steps"]
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_complete_step_is_idempotent(monkeypatch):
    steps = server.build_inspection_steps()
    fake_db = set_fake_db(
        monkeypatch,
        inspection_progress=[{
            "inspection_id": "inspection-1",
            "steps": steps,
            "current_step": 0,
        }],
    )

    run(server.complete_step("inspection-1", "exterior_front", "looks good"))
    run(server.complete_step("inspection-1", "exterior_front", "still looks good"))

    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][0]["notes"] == "still looks good"


def test_complete_step_returns_404_when_progress_missing(monkeypatch):
    set_fake_db(monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        run(server.complete_step("missing-inspection", "exterior_front"))

    assert exc_info.value.status_code == 404


def test_submit_report_is_idempotent_and_does_not_double_pay(monkeypatch):
    fake_db = set_fake_db(
        monkeypatch,
        inspections=[{
            "id": "inspection-1",
            "status": "in_progress",
            "inspector_id": "inspector-1",
            "buyer_id": "buyer-1",
            "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
            "total_amount": 300.0,
        }],
        inspector_profiles=[{
            "user_id": "inspector-1",
            "total_inspections": 0,
            "earnings": 0.0,
        }],
    )
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="good car",
        recommendation="buy",
    )

    first_response = run(server.submit_report("inspection-1", report))
    second_response = run(server.submit_report("inspection-1", report))

    assert second_response["report_id"] == first_response["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    profile = fake_db.inspector_profiles.docs[0]
    assert profile["total_inspections"] == 1
    assert profile["earnings"] == 240.0
