import os
import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_db")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import server  # noqa: E402


def test_passwords_are_hashed_and_verified():
    password = "TestPass123!"

    hashed = server.hash_password(password)

    assert hashed != password
    assert server.is_hashed_password(hashed)
    assert server.verify_password(password, hashed)
    assert not server.verify_password("wrong-password", hashed)


def test_plaintext_passwords_are_still_verifiable_for_upgrade():
    assert server.verify_password("legacy-pass", "legacy-pass")
    assert not server.verify_password("wrong-pass", "legacy-pass")


class FakeInspectionProgress:
    def __init__(self, progress):
        self.progress = progress
        self.update_calls = []

    async def find_one(self, query, projection):
        if query == {"inspection_id": self.progress["inspection_id"]}:
            return self.progress
        return None

    async def update_one(self, query, update):
        self.update_calls.append((query, update))
        matched = 1 if query.get("inspection_id") == self.progress["inspection_id"] else 0

        if "steps.step_name" in query:
            matched = int(any(step["step_name"] == query["steps.step_name"] for step in self.progress["steps"]))
            if matched and "$set" in update:
                for step in self.progress["steps"]:
                    if step["step_name"] == query["steps.step_name"]:
                        step["completed"] = update["$set"]["steps.$.completed"]
                        step["notes"] = update["$set"]["steps.$.notes"]

        if "$set" in update and "current_step" in update["$set"]:
            self.progress["current_step"] = update["$set"]["current_step"]

        return SimpleNamespace(matched_count=matched)


def make_progress():
    return {
        "inspection_id": "inspection-1",
        "current_step": 0,
        "steps": [
            {
                "step_name": "exterior_front",
                "description": "Front view",
                "required_photos": 3,
                "completed": False,
                "photos": [],
                "notes": "",
            },
            {
                "step_name": "exterior_sides",
                "description": "Both sides",
                "required_photos": 4,
                "completed": False,
                "photos": [],
                "notes": "",
            },
        ],
    }


def test_complete_step_rejects_unknown_step_without_advancing(monkeypatch):
    fake_progress = FakeInspectionProgress(make_progress())
    monkeypatch.setattr(server, "db", SimpleNamespace(inspection_progress=fake_progress))

    with pytest.raises(server.HTTPException) as exc:
        asyncio.run(server.complete_step("inspection-1", "bogus_step"))

    assert exc.value.status_code == 400
    assert fake_progress.progress["current_step"] == 0
    assert len(fake_progress.update_calls) == 0


def test_complete_step_is_idempotent_for_already_completed_step(monkeypatch):
    progress = make_progress()
    progress["current_step"] = 1
    progress["steps"][0]["completed"] = True
    fake_progress = FakeInspectionProgress(progress)
    monkeypatch.setattr(server, "db", SimpleNamespace(inspection_progress=fake_progress))

    response = asyncio.run(server.complete_step("inspection-1", "exterior_front"))

    assert response == {"message": "Step already completed"}
    assert fake_progress.progress["current_step"] == 1
    assert len(fake_progress.update_calls) == 0


def test_complete_step_advances_only_current_step(monkeypatch):
    fake_progress = FakeInspectionProgress(make_progress())
    monkeypatch.setattr(server, "db", SimpleNamespace(inspection_progress=fake_progress))

    asyncio.run(server.complete_step("inspection-1", "exterior_sides"))

    assert fake_progress.progress["steps"][1]["completed"]
    assert fake_progress.progress["current_step"] == 0

    asyncio.run(server.complete_step("inspection-1", "exterior_front"))

    assert fake_progress.progress["steps"][0]["completed"]
    assert fake_progress.progress["current_step"] == 1
