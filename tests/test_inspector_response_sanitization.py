import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_database")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import server  # noqa: E402


class FakeCursor:
    def __init__(self, items):
        self.items = items

    async def to_list(self, _limit):
        return self.items


class FakeInspectionCollection:
    def __init__(self, items):
        self.items = items

    def find(self, _query, _projection):
        return FakeCursor(self.items)


def test_inspector_inspection_response_removes_security_code_without_mutating():
    inspection = {
        "_id": "mongo-id",
        "id": "inspection-1",
        "status": "pending",
        "security_code": "123456",
    }

    sanitized = server.inspector_inspection_response(inspection)

    assert sanitized == {"id": "inspection-1", "status": "pending"}
    assert inspection["security_code"] == "123456"


def test_available_inspections_do_not_expose_security_code(monkeypatch):
    inspection = {
        "id": "inspection-1",
        "status": "pending",
        "security_code": "654321",
        "seller": {"lat": 41.8781, "lng": -87.6298},
    }
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(inspections=FakeInspectionCollection([inspection])),
    )

    result = asyncio.run(
        server.get_available_inspections(
            inspector_lat=41.8781,
            inspector_lng=-87.6298,
            radius=50,
        )
    )

    assert len(result) == 1
    assert "security_code" not in result[0]
    assert result[0]["distance_miles"] == 0.0
    assert inspection["security_code"] == "654321"


def test_inspector_jobs_do_not_expose_security_code(monkeypatch):
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            inspections=FakeInspectionCollection(
                [
                    {
                        "id": "inspection-1",
                        "inspector_id": "inspector-1",
                        "status": "accepted",
                        "security_code": "111222",
                    }
                ]
            )
        ),
    )

    result = asyncio.run(server.get_inspector_jobs("inspector-1"))

    assert result == [
        {
            "id": "inspection-1",
            "inspector_id": "inspector-1",
            "status": "accepted",
        }
    ]


def test_accept_inspection_response_does_not_expose_security_code(monkeypatch):
    class FakeAcceptInspections:
        def __init__(self):
            self.find_one_calls = 0

        async def find_one(self, _query, _projection):
            self.find_one_calls += 1
            inspection = {
                "id": "inspection-1",
                "buyer_id": "buyer-1",
                "status": "pending",
                "security_code": "333444",
            }
            if self.find_one_calls > 1:
                return {
                    **inspection,
                    "status": "accepted",
                    "inspector_id": "inspector-1",
                    "inspector_name": "Inspector One",
                }
            return inspection

        async def update_one(self, _query, _update):
            return SimpleNamespace(modified_count=1)

    class FakeUsers:
        async def find_one(self, _query, _projection):
            return {"id": "inspector-1", "full_name": "Inspector One"}

    class FakeNotifications:
        async def insert_one(self, _notification):
            return SimpleNamespace(inserted_id="notification-1")

    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            inspections=FakeAcceptInspections(),
            users=FakeUsers(),
            notifications=FakeNotifications(),
        ),
    )

    result = asyncio.run(server.accept_inspection("inspection-1", "inspector-1"))

    assert result["status"] == "accepted"
    assert "security_code" not in result
