import asyncio
import copy
import os

import pytest
from fastapi import HTTPException


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server  # noqa: E402


class UpdateResult:
    def __init__(self, matched_count=0):
        self.matched_count = matched_count


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.before_update = None

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def update_one(self, query, update, upsert=False):
        if self.before_update:
            before_update = self.before_update
            self.before_update = None
            before_update()

        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, query, update)
                return UpdateResult(matched_count=1)

        if upsert:
            new_doc = {
                key: copy.deepcopy(value)
                for key, value in query.items()
                if "." not in key and not isinstance(value, dict)
            }
            new_doc.update(copy.deepcopy(update.get("$setOnInsert", {})))
            self.docs.append(new_doc)

        return UpdateResult(matched_count=0)

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    def _matches(self, doc, query):
        for key, expected in query.items():
            if key == "steps.step_name":
                if not any(step.get("step_name") == expected for step in doc.get("steps", [])):
                    return False
                continue

            actual = doc.get(key)
            if isinstance(expected, dict):
                if "$in" in expected and actual not in expected["$in"]:
                    return False
            elif actual != expected:
                return False

        return True

    def _apply_update(self, doc, query, update):
        for key, value in update.get("$set", {}).items():
            if key.startswith("steps.$."):
                step_key = key.split(".", 2)[2]
                step_name = query["steps.step_name"]
                for step in doc.get("steps", []):
                    if step.get("step_name") == step_name:
                        step[step_key] = copy.deepcopy(value)
                        break
            else:
                doc[key] = copy.deepcopy(value)

        for key, value in update.get("$setOnInsert", {}).items():
            doc.setdefault(key, copy.deepcopy(value))

    def _project(self, doc, projection):
        result = copy.deepcopy(doc)
        if projection and projection.get("_id") == 0:
            result.pop("_id", None)
        return result


class FakeDB:
    def __init__(self):
        self.inspections = FakeCollection()
        self.users = FakeCollection()
        self.inspector_profiles = FakeCollection()
        self.notifications = FakeCollection()
        self.inspection_progress = FakeCollection()


def run(coro):
    return asyncio.run(coro)


def test_accept_inspection_loses_race_without_assigning_or_notifying(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspections.docs.append({
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
    })
    fake_db.users.docs.append({
        "id": "inspector-1",
        "full_name": "Inspector One",
        "user_type": "inspector",
    })
    fake_db.inspector_profiles.docs.append({
        "user_id": "inspector-1",
        "id_verified": True,
    })

    def competing_acceptance():
        fake_db.inspections.docs[0].update({
            "status": "accepted",
            "inspector_id": "inspector-2",
            "inspector_name": "Inspector Two",
        })

    fake_db.inspections.before_update = competing_acceptance
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        run(server.accept_inspection("inspection-1", "inspector-1"))

    assert exc.value.status_code == 400
    assert fake_db.inspections.docs[0]["inspector_id"] == "inspector-2"
    assert fake_db.notifications.docs == []


def test_verify_security_code_is_idempotent(monkeypatch):
    fake_db = FakeDB()
    fake_db.inspections.docs.append({
        "id": "inspection-1",
        "security_code": "123456",
        "status": "accepted",
    })
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.verify_security_code("inspection-1", "123456"))
    second = run(server.verify_security_code("inspection-1", "123456"))

    assert first["steps"] == second["steps"]
    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1


def test_complete_step_retries_do_not_skip_steps(monkeypatch):
    fake_db = FakeDB()
    steps = [
        {
            "step_name": "exterior_front",
            "description": "Front",
            "required_photos": 3,
            "completed": False,
            "photos": [],
            "notes": "",
        },
        {
            "step_name": "exterior_sides",
            "description": "Sides",
            "required_photos": 4,
            "completed": False,
            "photos": [],
            "notes": "",
        },
    ]
    fake_db.inspection_progress.docs.append({
        "inspection_id": "inspection-1",
        "steps": steps,
        "current_step": 0,
    })
    monkeypatch.setattr(server, "db", fake_db)

    run(server.complete_step("inspection-1", "exterior_front", "ok"))
    run(server.complete_step("inspection-1", "exterior_front", "ok"))

    progress = fake_db.inspection_progress.docs[0]
    assert progress["steps"][0]["completed"] is True
    assert progress["current_step"] == 1
