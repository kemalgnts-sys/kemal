import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, modified_count=1, matched_count=1):
        self.modified_count = modified_count
        self.matched_count = matched_count


def run(coro):
    return asyncio.run(coro)


def test_accept_inspection_claims_pending_job_atomically(monkeypatch):
    async def scenario():
        db = SimpleNamespace(
            users=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={
                        "id": "inspector-1",
                        "user_type": "inspector",
                        "full_name": "Verified Inspector",
                    }
                )
            ),
            inspector_profiles=SimpleNamespace(
                find_one=AsyncMock(return_value={"user_id": "inspector-1", "id_verified": True})
            ),
            inspections=SimpleNamespace(
                find_one_and_update=AsyncMock(
                    return_value={
                        "id": "inspection-1",
                        "buyer_id": "buyer-1",
                        "status": "accepted",
                        "inspector_id": "inspector-1",
                    }
                ),
                find_one=AsyncMock(),
            ),
            notifications=SimpleNamespace(insert_one=AsyncMock()),
        )
        monkeypatch.setattr(server, "db", db)

        result = await server.accept_inspection("inspection-1", "inspector-1")

        assert result["inspector_id"] == "inspector-1"
        claim_filter = db.inspections.find_one_and_update.call_args.args[0]
        assert claim_filter == {"id": "inspection-1", "status": "pending"}
        db.notifications.insert_one.assert_awaited_once()

    run(scenario())


def test_accept_inspection_rejects_lost_accept_race(monkeypatch):
    async def scenario():
        db = SimpleNamespace(
            users=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={
                        "id": "inspector-2",
                        "user_type": "inspector",
                        "full_name": "Second Inspector",
                    }
                )
            ),
            inspector_profiles=SimpleNamespace(
                find_one=AsyncMock(return_value={"user_id": "inspector-2", "id_verified": True})
            ),
            inspections=SimpleNamespace(
                find_one_and_update=AsyncMock(return_value=None),
                find_one=AsyncMock(return_value={"status": "accepted"}),
            ),
            notifications=SimpleNamespace(insert_one=AsyncMock()),
        )
        monkeypatch.setattr(server, "db", db)

        with pytest.raises(HTTPException) as exc:
            await server.accept_inspection("inspection-1", "inspector-2")

        assert exc.value.status_code == 400
        db.notifications.insert_one.assert_not_awaited()

    run(scenario())


def test_verify_security_code_does_not_create_duplicate_progress(monkeypatch):
    async def scenario():
        db = SimpleNamespace(
            inspections=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={
                        "id": "inspection-1",
                        "status": "in_progress",
                        "security_code": "123456",
                    }
                ),
                update_one=AsyncMock(),
            ),
            inspection_progress=SimpleNamespace(update_one=AsyncMock()),
        )
        monkeypatch.setattr(server, "db", db)

        with pytest.raises(HTTPException) as exc:
            await server.verify_security_code("inspection-1", "123456")

        assert exc.value.status_code == 400
        assert exc.value.detail == "Inspection already started"
        db.inspection_progress.update_one.assert_not_awaited()

    run(scenario())


def test_complete_step_retry_does_not_advance_progress_again(monkeypatch):
    async def scenario():
        db = SimpleNamespace(
            inspection_progress=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={
                        "inspection_id": "inspection-1",
                        "current_step": 1,
                        "steps": [
                            {"step_name": "exterior_front", "completed": True},
                            {"step_name": "exterior_sides", "completed": False},
                        ],
                    }
                ),
                update_one=AsyncMock(),
            )
        )
        monkeypatch.setattr(server, "db", db)

        result = await server.complete_step("inspection-1", "exterior_front", "retry")

        assert result == {"message": "Step completed"}
        db.inspection_progress.update_one.assert_not_awaited()

    run(scenario())


def test_submit_report_uses_server_progress_and_blocks_duplicate_payout(monkeypatch):
    async def scenario():
        progress_steps = [
            {"step_name": step["step_name"], "completed": True, "photos": [], "notes": ""}
            for step in server.INSPECTION_STEPS
        ]
        db = SimpleNamespace(
            inspection_progress=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={"inspection_id": "inspection-1", "steps": progress_steps}
                )
            ),
            reports=SimpleNamespace(find_one=AsyncMock(return_value=None), insert_one=AsyncMock()),
            inspections=SimpleNamespace(
                find_one=AsyncMock(return_value={"status": "in_progress"}),
                find_one_and_update=AsyncMock(
                    return_value={
                        "id": "inspection-1",
                        "buyer_id": "buyer-1",
                        "inspector_id": "inspector-1",
                        "vehicle": {"make": "Toyota", "model": "Camry", "year": 2020},
                        "total_amount": 120.0,
                        "status": "completed",
                    }
                ),
            ),
            inspector_profiles=SimpleNamespace(update_one=AsyncMock()),
            notifications=SimpleNamespace(insert_one=AsyncMock()),
        )
        monkeypatch.setattr(server, "db", db)

        report = server.InspectionReportCreate(
            inspection_id="inspection-1",
            steps=[],
            overall_notes="Looks good",
            recommendation="buy",
        )
        await server.submit_report("inspection-1", report)

        inserted_report = db.reports.insert_one.call_args.args[0]
        assert inserted_report["steps"] == progress_steps
        db.inspector_profiles.update_one.assert_awaited_once()

        db.reports.find_one.return_value = {"id": inserted_report["id"]}
        with pytest.raises(HTTPException) as exc:
            await server.submit_report("inspection-1", report)

        assert exc.value.status_code == 400
        assert exc.value.detail == "Inspection report already submitted"
        db.inspector_profiles.update_one.assert_awaited_once()

    run(scenario())
