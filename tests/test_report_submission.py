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
        self.docs = docs or []

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return copy.deepcopy(doc)
        return None

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                for key, value in update.get("$set", {}).items():
                    doc[key] = value
                for key, value in update.get("$inc", {}).items():
                    doc[key] = doc.get(key, 0) + value
                return UpdateResult(1)
        return UpdateResult(0)

    async def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return

    @staticmethod
    def _matches(doc, query):
        return all(doc.get(key) == value for key, value in query.items())


class FakeDb:
    def __init__(self, inspection):
        self.inspections = FakeCollection([inspection])
        self.reports = FakeCollection()
        self.inspector_profiles = FakeCollection(
            [{"user_id": inspection["inspector_id"], "total_inspections": 0, "earnings": 0.0}]
        )
        self.notifications = FakeCollection()


def make_inspection(status="in_progress"):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "inspector_id": "inspector-1",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "total_amount": 250.0,
        "status": status,
    }


def make_report(inspection_id="inspection-1"):
    return server.InspectionReportCreate(
        inspection_id=inspection_id,
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_submit_report_retry_is_idempotent(monkeypatch):
    fake_db = FakeDb(make_inspection())
    monkeypatch.setattr(server, "db", fake_db)

    first = asyncio.run(server.submit_report("inspection-1", make_report()))
    second = asyncio.run(server.submit_report("inspection-1", make_report()))

    assert second["report_id"] == first["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspections.docs[0]["status"] == "completed"
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 200.0


def test_submit_report_rejects_mismatched_inspection_id(monkeypatch):
    fake_db = FakeDb(make_inspection())
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(server.submit_report("inspection-1", make_report("other-inspection")))

    assert exc_info.value.status_code == 400
    assert len(fake_db.reports.docs) == 0
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 0.0
