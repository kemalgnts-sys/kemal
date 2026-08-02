import asyncio
import copy
import os

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, length):
        return [copy.deepcopy(doc) for doc in self.docs[:length]]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [copy.deepcopy(doc) for doc in (docs or [])]
        self.inserted = []

    def find(self, query=None, projection=None):
        query = query or {}
        return FakeCursor([doc for doc in self.docs if self._matches(doc, query)])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return copy.deepcopy(doc)
        return None

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                for key, value in update.get("$set", {}).items():
                    doc[key] = value
                return

    async def insert_one(self, doc):
        self.inserted.append(copy.deepcopy(doc))

    def _matches(self, doc, query):
        return all(doc.get(key) == value for key, value in query.items())


class FakeDb:
    def __init__(self, inspections, users=None):
        self.inspections = FakeCollection(inspections)
        self.users = FakeCollection(users)
        self.notifications = FakeCollection()


def make_inspection(**overrides):
    inspection = {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298, "city": "Chicago", "state": "IL"},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
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


def test_available_inspections_do_not_expose_security_code(monkeypatch):
    fake_db = FakeDb([make_inspection()])
    monkeypatch.setattr(server, "db", fake_db)

    response = asyncio.run(server.get_available_inspections(41.8781, -87.6298, 50))

    assert len(response) == 1
    assert "security_code" not in response[0]
    assert response[0]["distance_miles"] == 0


def test_accept_inspection_does_not_expose_security_code(monkeypatch):
    fake_db = FakeDb(
        [make_inspection()],
        [{"id": "inspector-1", "full_name": "Inspector One"}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    response = asyncio.run(server.accept_inspection("inspection-1", "inspector-1"))

    assert response["status"] == "accepted"
    assert response["inspector_id"] == "inspector-1"
    assert "security_code" not in response
    stored = fake_db.inspections.docs[0]
    assert stored["security_code"] == "123456"


def test_inspector_jobs_do_not_expose_security_code(monkeypatch):
    fake_db = FakeDb([
        make_inspection(status="accepted", inspector_id="inspector-1"),
    ])
    monkeypatch.setattr(server, "db", fake_db)

    response = asyncio.run(server.get_inspector_jobs("inspector-1"))

    assert len(response) == 1
    assert response[0]["id"] == "inspection-1"
    assert "security_code" not in response[0]


def test_buyer_inspections_still_include_security_code(monkeypatch):
    fake_db = FakeDb([make_inspection()])
    monkeypatch.setattr(server, "db", fake_db)

    response = asyncio.run(server.get_buyer_inspections("buyer-1"))

    assert response[0]["security_code"] == "123456"
