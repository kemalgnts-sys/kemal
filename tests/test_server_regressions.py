import asyncio
import importlib
import os

import pytest
from fastapi import HTTPException


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_db")

server = importlib.import_module("backend.server")


def test_available_inspection_payload_does_not_expose_security_code_or_private_fields():
    inspection = {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer Name",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {
            "name": "Seller Name",
            "phone": "+15555550123",
            "address": "123 Main St",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601",
            "lat": 41.8781,
            "lng": -87.6298,
        },
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
        "security_code": "123456",
        "status": "pending",
        "inspector_id": None,
        "inspector_name": None,
        "created_at": "2026-05-02T11:00:00+00:00",
        "accepted_at": None,
        "completed_at": None,
        "preferred_date": None,
        "notes": "Gate code is 9876",
    }

    payload = server.available_inspection_payload(inspection, 3.2)

    assert payload["distance_miles"] == 3.2
    assert "security_code" not in payload
    assert "buyer_id" not in payload
    assert "buyer_name" not in payload
    assert "phone" not in payload["seller"]
    assert "address" not in payload["seller"]
    assert "zip_code" not in payload["seller"]


class _UpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count


class _Collection:
    def __init__(self, docs=None):
        self.docs = docs or []

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return dict(doc)
        return None

    async def update_one(self, query, update):
        for doc in self.docs:
            if not self._matches(doc, query):
                continue
            if "$set" in update:
                doc.update(update["$set"])
            if "$inc" in update:
                for key, value in update["$inc"].items():
                    doc[key] = doc.get(key, 0) + value
            return _UpdateResult(1)
        return _UpdateResult(0)

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return object()

    def _matches(self, doc, query):
        for key, expected in query.items():
            if isinstance(expected, dict) and "$ne" in expected:
                if doc.get(key) == expected["$ne"]:
                    return False
            elif doc.get(key) != expected:
                return False
        return True


class _FakeDB:
    def __init__(self, inspection_status="in_progress"):
        self.inspections = _Collection([
            {
                "id": "inspection-1",
                "buyer_id": "buyer-1",
                "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
                "status": inspection_status,
                "inspector_id": "inspector-1",
                "total_amount": 270.0,
            }
        ])
        self.reports = _Collection()
        self.inspector_profiles = _Collection([
            {"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}
        ])
        self.notifications = _Collection()


def test_submit_report_rejects_duplicate_submission_without_duplicate_earnings(monkeypatch):
    fake_db = _FakeDB()
    monkeypatch.setattr(server, "db", fake_db)
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )

    first_response = asyncio.run(server.submit_report("inspection-1", report))
    assert first_response["report_id"]

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(server.submit_report("inspection-1", report))

    assert exc_info.value.status_code == 409
    assert len(fake_db.reports.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 216.0
