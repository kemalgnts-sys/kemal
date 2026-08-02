import asyncio
import copy
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [copy.deepcopy(doc) for doc in (docs or [])]

    async def find_one(self, filter_doc, projection=None):
        for doc in self.docs:
            if self._matches(doc, filter_doc):
                return self._project(doc, projection)
        return None

    async def find_one_and_update(self, filter_doc, update_doc, projection=None, return_document=None):
        for doc in self.docs:
            if self._matches(doc, filter_doc):
                before = self._project(doc, projection)
                self._apply_update(doc, filter_doc, update_doc)
                return before
        return None

    async def update_one(self, filter_doc, update_doc):
        for doc in self.docs:
            if self._matches(doc, filter_doc):
                self._apply_update(doc, filter_doc, update_doc)
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    def _matches(self, doc, filter_doc):
        for key, expected in filter_doc.items():
            actual = self._get_value(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
            elif key == "steps.step_name":
                if not any(step.get("step_name") == expected for step in doc.get("steps", [])):
                    return False
            elif actual != expected:
                return False
        return True

    def _get_value(self, doc, dotted_key):
        value = doc
        for part in dotted_key.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

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

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection and projection.get("_id") == 0:
            projected.pop("_id", None)
        return projected


class FakeDB:
    def __init__(self, inspections=None, progress=None, profiles=None):
        self.inspections = FakeCollection(inspections)
        self.inspection_progress = FakeCollection(progress)
        self.reports = FakeCollection()
        self.inspector_profiles = FakeCollection(profiles)
        self.notifications = FakeCollection()


def run(coro):
    return asyncio.run(coro)


def make_report():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )


def test_submit_report_is_idempotent_after_success(monkeypatch):
    fake_db = FakeDB(
        inspections=[
            {
                "id": "inspection-1",
                "status": "in_progress",
                "inspector_id": "inspector-1",
                "buyer_id": "buyer-1",
                "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
                "total_amount": 250.0,
            }
        ],
        profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.submit_report("inspection-1", make_report()))
    second = run(server.submit_report("inspection-1", make_report()))

    assert second["report_id"] == first["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 200.0


def test_complete_step_rejects_missing_progress(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        run(server.complete_step("missing-inspection", "exterior_front"))

    assert exc.value.status_code == 404


def test_complete_step_only_advances_current_step(monkeypatch):
    fake_db = FakeDB(
        progress=[
            {
                "inspection_id": "inspection-1",
                "current_step": 0,
                "steps": [
                    {"step_name": "exterior_front", "completed": False, "notes": ""},
                    {"step_name": "engine", "completed": False, "notes": ""},
                ],
            }
        ]
    )
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        run(server.complete_step("inspection-1", "engine", "out of order"))

    assert exc.value.status_code == 400
    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 0
    assert progress["steps"][1]["completed"] is False


def test_complete_step_advances_once_for_expected_step(monkeypatch):
    fake_db = FakeDB(
        progress=[
            {
                "inspection_id": "inspection-1",
                "current_step": 0,
                "steps": [
                    {"step_name": "exterior_front", "completed": False, "notes": ""},
                    {"step_name": "engine", "completed": False, "notes": ""},
                ],
            }
        ]
    )
    monkeypatch.setattr(server, "db", fake_db)

    result = run(server.complete_step("inspection-1", "exterior_front", "done"))

    assert result == {"message": "Step completed"}
    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][0]["notes"] == "done"
