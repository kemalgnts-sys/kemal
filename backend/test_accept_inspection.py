import asyncio
import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeInspections:
    def __init__(self, modified_count):
        self.modified_count = modified_count
        self.update_filter = None
        self.update_doc = None
        self.doc = {
            "id": "inspection-1",
            "buyer_id": "buyer-1",
            "status": "pending",
        }

    async def find_one(self, query, projection=None):
        if query == {"id": "inspection-1"}:
            return dict(self.doc)
        return None

    async def update_one(self, query, update):
        self.update_filter = query
        self.update_doc = update
        if self.modified_count:
            self.doc.update(update["$set"])
        return FakeUpdateResult(self.modified_count)


class FakeUsers:
    async def find_one(self, query, projection=None):
        if query == {"id": "inspector-1"}:
            return {"id": "inspector-1", "full_name": "Test Inspector"}
        return None


class FakeNotifications:
    def __init__(self):
        self.inserted = []

    async def insert_one(self, doc):
        self.inserted.append(doc)


class FakeDb:
    def __init__(self, modified_count):
        self.inspections = FakeInspections(modified_count)
        self.users = FakeUsers()
        self.notifications = FakeNotifications()


def test_accept_inspection_claims_pending_job_atomically(monkeypatch):
    fake_db = FakeDb(modified_count=1)
    monkeypatch.setattr(server, "db", fake_db)

    result = asyncio.run(server.accept_inspection("inspection-1", "inspector-1"))

    assert fake_db.inspections.update_filter == {
        "id": "inspection-1",
        "status": "pending",
    }
    assert result["status"] == "accepted"
    assert result["inspector_id"] == "inspector-1"
    assert len(fake_db.notifications.inserted) == 1


def test_accept_inspection_rejects_lost_concurrent_claim_without_notifying(monkeypatch):
    fake_db = FakeDb(modified_count=0)
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(server.accept_inspection("inspection-1", "inspector-1"))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Inspection already accepted"
    assert fake_db.inspections.update_filter == {
        "id": "inspection-1",
        "status": "pending",
    }
    assert fake_db.notifications.inserted == []
