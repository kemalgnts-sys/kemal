import asyncio
import copy
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server


class FakeUpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count
        self.modified_count = matched_count


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, _limit):
        return copy.deepcopy(self.docs)


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = copy.deepcopy(docs or [])

    def find(self, query, projection=None):
        return FakeCursor([self._project(doc, projection) for doc in self.docs if self._matches(doc, query)])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, update)
                return FakeUpdateResult(1)

        if upsert:
            doc = copy.deepcopy(query)
            self._apply_update(doc, update, inserting=True)
            self.docs.append(doc)
        return FakeUpdateResult(0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            actual = doc.get(key)
            if isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
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
            result = {key: copy.deepcopy(doc[key]) for key in includes if key in doc}

        for key in excludes:
            result.pop(key, None)
        return result

    def _apply_update(self, doc, update, inserting=False):
        if "$set" in update:
            for key, value in update["$set"].items():
                self._set_value(doc, key, value)

        if inserting and "$setOnInsert" in update:
            for key, value in update["$setOnInsert"].items():
                self._set_value(doc, key, value)

        if "$inc" in update:
            for key, value in update["$inc"].items():
                doc[key] = doc.get(key, 0) + value

    def _set_value(self, doc, dotted_key, value):
        parts = dotted_key.split(".")
        target = doc
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = copy.deepcopy(value)


def run(coro):
    return asyncio.run(coro)


def install_db(monkeypatch, **collections):
    db = SimpleNamespace(
        inspections=FakeCollection(collections.get("inspections")),
        users=FakeCollection(collections.get("users")),
        inspector_profiles=FakeCollection(collections.get("inspector_profiles")),
        inspection_progress=FakeCollection(collections.get("inspection_progress")),
        reports=FakeCollection(collections.get("reports")),
        notifications=FakeCollection(collections.get("notifications")),
    )
    monkeypatch.setattr(server, "db", db)
    return db


def inspection_doc(**overrides):
    doc = {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry", "color": "Silver"},
        "seller": {"name": "Seller", "city": "Chicago", "state": "IL", "lat": 41.8781, "lng": -87.6298},
        "package_type": "basic",
        "package_price": 100.0,
        "tip_amount": 0.0,
        "total_amount": 100.0,
        "security_code": "123456",
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
        "created_at": "2026-05-15T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }
    doc.update(overrides)
    return doc


def test_available_inspections_redact_security_code_and_buyer_id(monkeypatch):
    install_db(monkeypatch, inspections=[inspection_doc()])

    available = run(server.get_available_inspections(inspector_lat=41.8781, inspector_lng=-87.6298, radius=50))

    assert len(available) == 1
    assert available[0]["id"] == "inspection-1"
    assert "security_code" not in available[0]
    assert "buyer_id" not in available[0]


def test_accept_requires_verified_inspector(monkeypatch):
    db = install_db(
        monkeypatch,
        inspections=[inspection_doc()],
        users=[{"id": "inspector-1", "user_type": "inspector", "full_name": "Inspector One"}],
        inspector_profiles=[{"user_id": "inspector-1", "id_verified": False}],
    )

    with pytest.raises(HTTPException) as exc:
        run(server.accept_inspection("inspection-1", "inspector-1"))

    assert exc.value.status_code == 403
    assert db.inspections.docs[0]["status"] == "pending"
    assert db.notifications.docs == []


def test_verify_code_rejects_pending_inspection(monkeypatch):
    db = install_db(monkeypatch, inspections=[inspection_doc()])

    with pytest.raises(HTTPException) as exc:
        run(server.verify_security_code("inspection-1", "123456"))

    assert exc.value.status_code == 400
    assert db.inspections.docs[0]["status"] == "pending"
    assert db.inspection_progress.docs == []


def test_verify_code_is_idempotent_after_start(monkeypatch):
    db = install_db(
        monkeypatch,
        inspections=[inspection_doc(status="accepted", inspector_id="inspector-1")],
    )

    first = run(server.verify_security_code("inspection-1", "123456"))
    second = run(server.verify_security_code("inspection-1", "123456"))

    assert first["steps"]
    assert second["steps"]
    assert db.inspections.docs[0]["status"] == "in_progress"
    assert len(db.inspection_progress.docs) == 1


def test_submit_report_requires_completed_progress(monkeypatch):
    db = install_db(
        monkeypatch,
        inspections=[inspection_doc(status="in_progress", inspector_id="inspector-1")],
        inspection_progress=[
            {
                "inspection_id": "inspection-1",
                "current_step": 0,
                "steps": [{"step_name": "exterior_front", "completed": False}],
            }
        ],
    )
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks fine",
        recommendation="buy",
    )

    with pytest.raises(HTTPException) as exc:
        run(server.submit_report("inspection-1", report))

    assert exc.value.status_code == 400
    assert db.inspections.docs[0]["status"] == "in_progress"
    assert db.reports.docs == []
