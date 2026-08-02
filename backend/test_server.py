import asyncio
import copy
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self, docs=None, before_update=None):
        self.docs = [copy.deepcopy(doc) for doc in (docs or [])]
        self.before_update = before_update
        self.inserted = []

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def update_one(self, query, update):
        if self.before_update:
            self.before_update(self)
            self.before_update = None

        for doc in self.docs:
            if self._matches(doc, query):
                for key, value in update.get("$set", {}).items():
                    doc[key] = value
                return FakeUpdateResult(1)
        return FakeUpdateResult(0)

    async def insert_one(self, doc):
        self.inserted.append(copy.deepcopy(doc))
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    def _matches(self, doc, query):
        return all(doc.get(key) == value for key, value in query.items())

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection:
            for key, include in projection.items():
                if include == 0:
                    projected.pop(key, None)
        return projected


def run(coro):
    return asyncio.run(coro)


def install_fake_db(monkeypatch, *, inspections, users, profiles, race_before_accept=None):
    fake_db = SimpleNamespace(
        inspections=FakeCollection(inspections, before_update=race_before_accept),
        users=FakeCollection(users),
        inspector_profiles=FakeCollection(profiles),
        notifications=FakeCollection(),
    )
    monkeypatch.setattr(server, "db", fake_db)
    return fake_db


def test_accept_inspection_does_not_overwrite_concurrent_assignment(monkeypatch):
    def another_inspector_accepts(collection):
        collection.docs[0]["status"] = "accepted"
        collection.docs[0]["inspector_id"] = "inspector-first"
        collection.docs[0]["inspector_name"] = "First Inspector"

    fake_db = install_fake_db(
        monkeypatch,
        inspections=[{
            "id": "inspection-1",
            "buyer_id": "buyer-1",
            "status": "pending",
        }],
        users=[{
            "id": "inspector-second",
            "full_name": "Second Inspector",
            "user_type": "inspector",
        }],
        profiles=[{
            "user_id": "inspector-second",
            "id_verified": True,
        }],
        race_before_accept=another_inspector_accepts,
    )

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-second"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspections.docs[0]["inspector_id"] == "inspector-first"
    assert fake_db.inspections.docs[0]["inspector_name"] == "First Inspector"
    assert fake_db.notifications.inserted == []


def test_accept_inspection_requires_verified_inspector(monkeypatch):
    fake_db = install_fake_db(
        monkeypatch,
        inspections=[{
            "id": "inspection-1",
            "buyer_id": "buyer-1",
            "status": "pending",
        }],
        users=[{
            "id": "inspector-1",
            "full_name": "Unverified Inspector",
            "user_type": "inspector",
        }],
        profiles=[{
            "user_id": "inspector-1",
            "id_verified": False,
        }],
    )

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "inspector-1"))

    assert exc_info.value.status_code == 403
    assert fake_db.inspections.docs[0]["status"] == "pending"
    assert fake_db.notifications.inserted == []
