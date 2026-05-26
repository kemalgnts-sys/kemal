import copy
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_database")

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
                modified = 1 if doc != before else 0
                return SimpleNamespace(matched_count=1, modified_count=modified)
        return SimpleNamespace(matched_count=0, modified_count=0)

    def _matches(self, doc, query):
        return all(self._matches_key(doc, key, expected) for key, expected in query.items())

    def _matches_key(self, doc, key, expected):
        values = self._values_for_key(doc, key)
        if isinstance(expected, dict):
            if "$ne" in expected:
                return any(value != expected["$ne"] for value in values)
            raise AssertionError(f"Unsupported query operator in {expected}")
        return any(value == expected for value in values)

    def _values_for_key(self, doc, key):
        values = [doc]
        for part in key.split("."):
            next_values = []
            for value in values:
                if isinstance(value, list):
                    next_values.extend(item.get(part) for item in value if isinstance(item, dict) and part in item)
                elif isinstance(value, dict) and part in value:
                    next_values.append(value[part])
            values = next_values
        return values

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if not projection:
            return projected
        if any(value == 1 for value in projection.values()):
            projected = {
                key: copy.deepcopy(doc[key])
                for key, include in projection.items()
                if include == 1 and key in doc
            }
        for key, include in projection.items():
            if include == 0:
                projected.pop(key, None)
        return projected

    def _apply_update(self, doc, query, update):
        for key, value in update.get("$set", {}).items():
            self._set_value(doc, query, key, value)
        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value
        for key, value in update.get("$push", {}).items():
            target = self._get_positional_step(doc, query) if key.startswith("steps.$.") else None
            if target is not None:
                target.setdefault(key.split(".", 2)[2], []).append(value)
            else:
                doc.setdefault(key, []).append(value)

    def _set_value(self, doc, query, key, value):
        if key.startswith("steps.$."):
            target = self._get_positional_step(doc, query)
            if target is not None:
                target[key.split(".", 2)[2]] = value
            return
        parts = key.split(".")
        target = doc
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    def _get_positional_step(self, doc, query):
        step_name = query.get("steps.step_name")
        if not step_name:
            return None
        return next((step for step in doc.get("steps", []) if step.get("step_name") == step_name), None)


class FakeDB:
    def __init__(self, **collections):
        for name in [
            "users",
            "inspector_profiles",
            "inspections",
            "inspection_progress",
            "reports",
            "notifications",
        ]:
            setattr(self, name, FakeCollection(collections.get(name, [])))


def make_inspection(**overrides):
    inspection = {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 0.0,
        "total_amount": 250.0,
        "security_code": "123456",
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
    }
    inspection.update(overrides)
    return inspection


def make_progress(**overrides):
    progress = {
        "inspection_id": "inspection-1",
        "steps": [
            {
                "step_name": step["step_name"],
                "description": step["description"],
                "required_photos": step["required_photos"],
                "completed": True,
                "photos": [],
                "notes": "",
            }
            for step in server.INSPECTION_STEPS
        ],
        "current_step": len(server.INSPECTION_STEPS) - 1,
        "started_at": "2026-01-01T00:00:00+00:00",
    }
    progress.update(overrides)
    return progress


@pytest.mark.asyncio
async def test_available_inspections_do_not_expose_security_code(monkeypatch):
    fake_db = FakeDB(inspections=[make_inspection()])
    monkeypatch.setattr(server, "db", fake_db)

    jobs = await server.get_available_inspections(inspector_lat=41.8781, inspector_lng=-87.6298)

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]


@pytest.mark.asyncio
async def test_accept_requires_verified_inspector_and_only_notifies_once(monkeypatch):
    fake_db = FakeDB(
        users=[
            {
                "id": "inspector-1",
                "full_name": "Inspector One",
                "user_type": "inspector",
            },
            {
                "id": "inspector-2",
                "full_name": "Inspector Two",
                "user_type": "inspector",
            },
        ],
        inspector_profiles=[
            {"user_id": "inspector-1", "id_verified": False},
            {"user_id": "inspector-2", "id_verified": True},
        ],
        inspections=[make_inspection()],
    )
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        await server.accept_inspection("inspection-1", "inspector-1")
    assert exc_info.value.status_code == 403

    fake_db.inspector_profiles.docs[0]["id_verified"] = True
    accepted = await server.accept_inspection("inspection-1", "inspector-1")
    assert accepted["inspector_id"] == "inspector-1"

    with pytest.raises(HTTPException) as exc_info:
        await server.accept_inspection("inspection-1", "inspector-2")
    assert exc_info.value.status_code == 400
    assert len(fake_db.notifications.docs) == 1


@pytest.mark.asyncio
async def test_verify_code_is_idempotent_and_does_not_duplicate_progress(monkeypatch):
    fake_db = FakeDB(inspections=[make_inspection(status="accepted", inspector_id="inspector-1")])
    monkeypatch.setattr(server, "db", fake_db)

    first_response = await server.verify_security_code("inspection-1", "123456")
    second_response = await server.verify_security_code("inspection-1", "123456")

    assert first_response["steps"]
    assert second_response["steps"]
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


@pytest.mark.asyncio
async def test_submit_report_is_idempotent_and_pays_once(monkeypatch):
    fake_db = FakeDB(
        inspections=[make_inspection(status="in_progress", inspector_id="inspector-1")],
        inspection_progress=[make_progress()],
        inspector_profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    monkeypatch.setattr(server, "db", fake_db)
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=make_progress()["steps"],
        overall_notes="Looks good",
        recommendation="buy",
    )

    first_response = await server.submit_report("inspection-1", report)
    second_response = await server.submit_report("inspection-1", report)

    assert first_response["report_id"] == second_response["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 200.0


@pytest.mark.asyncio
async def test_complete_step_without_progress_returns_404(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc_info:
        await server.complete_step("missing-inspection", "exterior_front")

    assert exc_info.value.status_code == 404
