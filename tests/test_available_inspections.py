import asyncio
import os
from types import SimpleNamespace

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server  # noqa: E402


class FakeCursor:
    def __init__(self, documents, projection):
        self.documents = documents
        self.projection = projection or {}

    async def to_list(self, length):
        projected = []
        for document in self.documents[:length]:
            copy = dict(document)
            if self.projection.get("_id") == 0:
                copy.pop("_id", None)
            if self.projection.get("security_code") == 0:
                copy.pop("security_code", None)
            projected.append(copy)
        return projected


class FakeInspectionsCollection:
    def __init__(self, documents):
        self.documents = documents
        self.last_query = None
        self.last_projection = None

    def find(self, query, projection=None):
        self.last_query = query
        self.last_projection = projection
        matching = [
            document
            for document in self.documents
            if all(document.get(key) == value for key, value in query.items())
        ]
        return FakeCursor(matching, projection)


def test_available_inspections_does_not_expose_security_code(monkeypatch):
    inspections = FakeInspectionsCollection([
        {
            "_id": "mongo-id",
            "id": "near-pending",
            "status": "pending",
            "security_code": "123456",
            "seller": {"lat": 41.8781, "lng": -87.6298},
        },
        {
            "id": "accepted",
            "status": "accepted",
            "security_code": "654321",
            "seller": {"lat": 41.8781, "lng": -87.6298},
        },
    ])
    monkeypatch.setattr(server, "db", SimpleNamespace(inspections=inspections))

    result = asyncio.run(server.get_available_inspections(
        inspector_lat=41.8781,
        inspector_lng=-87.6298,
        radius=50,
    ))

    assert inspections.last_query == {"status": "pending"}
    assert inspections.last_projection == {"_id": 0, "security_code": 0}
    assert result == [{
        "id": "near-pending",
        "status": "pending",
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "distance_miles": 0.0,
    }]
