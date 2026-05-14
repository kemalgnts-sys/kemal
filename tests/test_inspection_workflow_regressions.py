import asyncio
import importlib
import os
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

server = importlib.import_module("backend.server")


class FakeUpdateResult:
    def __init__(self, modified_count=0):
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [deepcopy(doc) for doc in docs or []]

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def insert_one(self, doc):
        self.docs.append(deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, update, inserting=False)
                return FakeUpdateResult(modified_count=1)

        if upsert:
            new_doc = {key: value for key, value in query.items() if not key.startswith("$")}
            self._apply_update(new_doc, update, inserting=True)
            self.docs.append(new_doc)

        return FakeUpdateResult(modified_count=0)

    def _matches(self, doc, query):
        return all(doc.get(key) == value for key, value in query.items())

    def _apply_update(self, doc, update, inserting):
        for key, value in update.get("$set", {}).items():
            doc[key] = deepcopy(value)
        if inserting:
            for key, value in update.get("$setOnInsert", {}).items():
                doc[key] = deepcopy(value)

    def _project(self, doc, projection):
        if not projection:
            return deepcopy(doc)
        if any(value == 1 for value in projection.values()):
            return {
                key: deepcopy(doc[key])
                for key, include in projection.items()
                if include == 1 and key in doc
            }
        result = deepcopy(doc)
        for key, include in projection.items():
            if include == 0:
                result.pop(key, None)
        return result


class RacingInspectionCollection(FakeCollection):
    async def update_one(self, query, update, upsert=False):
        if query.get("status") == "pending":
            for doc in self.docs:
                if doc.get("id") == query.get("id"):
                    doc["status"] = "accepted"
                    doc["inspector_id"] = "winner-inspector"
                    doc["inspector_name"] = "Winning Inspector"
                    break
        return await super().update_one(query, update, upsert=upsert)


def run(coro):
    return asyncio.run(coro)


def install_fake_db(monkeypatch, inspections, users=None, progress=None, racing=False):
    inspection_collection = (
        RacingInspectionCollection(inspections)
        if racing
        else FakeCollection(inspections)
    )
    fake_db = SimpleNamespace(
        inspections=inspection_collection,
        users=FakeCollection(users or []),
        notifications=FakeCollection(),
        inspection_progress=FakeCollection(progress or []),
    )
    monkeypatch.setattr(server, "db", fake_db)
    return fake_db


def test_accept_rejects_concurrent_stale_update_without_overwriting(monkeypatch):
    fake_db = install_fake_db(
        monkeypatch,
        inspections=[
            {
                "id": "inspection-1",
                "buyer_id": "buyer-1",
                "status": "pending",
                "inspector_id": None,
                "inspector_name": None,
            }
        ],
        users=[{"id": "late-inspector", "full_name": "Late Inspector"}],
        racing=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        run(server.accept_inspection("inspection-1", "late-inspector"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspections.docs[0]["inspector_id"] == "winner-inspector"
    assert fake_db.notifications.docs == []


def test_verify_security_code_is_idempotent_and_keeps_single_progress_doc(monkeypatch):
    fake_db = install_fake_db(
        monkeypatch,
        inspections=[
            {
                "id": "inspection-1",
                "status": "accepted",
                "security_code": "123456",
            }
        ],
    )

    first_response = run(server.verify_security_code("inspection-1", "123456"))
    second_response = run(server.verify_security_code("inspection-1", "123456"))

    assert first_response["message"] == "Code verified, inspection started"
    assert second_response["message"] == "Code already verified, inspection started"
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_verify_security_code_does_not_reopen_completed_inspection(monkeypatch):
    fake_db = install_fake_db(
        monkeypatch,
        inspections=[
            {
                "id": "inspection-1",
                "status": "completed",
                "security_code": "123456",
            }
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc_info.value.status_code == 400
    assert fake_db.inspections.docs[0]["status"] == "completed"
    assert fake_db.inspection_progress.docs == []
