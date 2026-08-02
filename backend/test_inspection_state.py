import asyncio
import copy
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, modified_count=0):
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

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
        return FakeCursor([self._project(doc, projection) for doc in self.docs if self._matches(doc, query)])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                if "$set" in update:
                    for key, value in update["$set"].items():
                        self._set_path(doc, key, value)
                if "$inc" in update:
                    for key, value in update["$inc"].items():
                        self._set_path(doc, key, self._get_path(doc, key) + value)
                return FakeUpdateResult(modified_count=1)

        if upsert:
            new_doc = copy.deepcopy(query)
            for key, value in update.get("$setOnInsert", {}).items():
                self._set_path(new_doc, key, value)
            self.docs.append(new_doc)

        return FakeUpdateResult(modified_count=0)

    def _matches(self, doc, query):
        return all(self._get_path(doc, key) == value for key, value in query.items())

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection:
            for key, value in projection.items():
                if value == 0:
                    projected.pop(key, None)
        return projected

    def _get_path(self, doc, path):
        current = doc
        for part in path.split("."):
            if isinstance(current, list):
                current = current[int(part)]
            else:
                current = current.get(part)
        return current

    def _set_path(self, doc, path, value):
        parts = path.split(".")
        current = doc
        for part in parts[:-1]:
            if isinstance(current, list):
                current = current[int(part)]
            else:
                current = current.setdefault(part, {})

        last = parts[-1]
        if isinstance(current, list):
            current[int(last)] = value
        else:
            current[last] = value


class FakeDB:
    def __init__(self, **collections):
        self.inspections = FakeCollection(collections.get("inspections"))
        self.inspection_progress = FakeCollection(collections.get("inspection_progress"))
        self.reports = FakeCollection(collections.get("reports"))
        self.inspector_profiles = FakeCollection(collections.get("inspector_profiles"))
        self.notifications = FakeCollection(collections.get("notifications"))


def run(coro):
    return asyncio.run(coro)


def inspection_doc(status="in_progress"):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer",
        "vehicle": {"year": 2021, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": "inspector-1",
        "inspector_name": "Inspector",
        "created_at": "2026-05-21T00:00:00+00:00",
        "accepted_at": "2026-05-21T00:01:00+00:00",
        "completed_at": None,
    }


def report_payload():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[{"step_name": "exterior_front", "completed": True}],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_submit_report_is_idempotent_and_does_not_double_pay(monkeypatch):
    fake_db = FakeDB(
        inspections=[inspection_doc()],
        inspector_profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.submit_report("inspection-1", report_payload()))
    second = run(server.submit_report("inspection-1", report_payload()))

    assert second["report_id"] == first["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == pytest.approx(216.0)


def test_submit_report_rejects_before_inspection_starts(monkeypatch):
    fake_db = FakeDB(
        inspections=[inspection_doc(status="accepted")],
        inspector_profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        run(server.submit_report("inspection-1", report_payload()))

    assert exc.value.status_code == 400
    assert len(fake_db.reports.docs) == 0
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 0
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 0.0


def test_verify_code_requires_accepted_inspection(monkeypatch):
    pending = inspection_doc(status="pending")
    pending["inspector_id"] = None
    pending["inspector_name"] = None
    fake_db = FakeDB(inspections=[pending])
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc.value.status_code == 400
    assert fake_db.inspections.docs[0]["status"] == "pending"
    assert fake_db.inspection_progress.docs == []


def test_verify_code_is_idempotent_after_start(monkeypatch):
    fake_db = FakeDB(inspections=[inspection_doc(status="accepted")])
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.verify_security_code("inspection-1", "123456"))
    second = run(server.verify_security_code("inspection-1", "123456"))

    assert first["steps"] == second["steps"]
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_available_inspections_do_not_expose_security_code(monkeypatch):
    fake_db = FakeDB(inspections=[inspection_doc(status="pending")])
    monkeypatch.setattr(server, "db", fake_db)

    jobs = run(server.get_available_inspections(inspector_lat=41.8781, inspector_lng=-87.6298, radius=50))

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]
