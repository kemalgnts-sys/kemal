import asyncio
import copy
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server  # noqa: E402


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


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

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    def find(self, query, projection=None):
        return FakeCursor([self._project(doc, projection) for doc in self.docs if self._matches(doc, query)])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                self._apply_update(doc, query, update)
                return FakeUpdateResult(1)
        return FakeUpdateResult(0)

    def _matches(self, doc, query):
        for key, expected in query.items():
            actual = self._get(doc, key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
            elif isinstance(actual, list):
                if expected not in actual:
                    return False
            elif actual != expected:
                return False
        return True

    def _project(self, doc, projection):
        projected = copy.deepcopy(doc)
        if projection:
            for key, include in projection.items():
                if include == 0:
                    projected.pop(key, None)
        return projected

    def _apply_update(self, doc, query, update):
        for key, value in update.get("$set", {}).items():
            if ".$." in key:
                list_key, child_key = key.split(".$.", 1)
                matched_name = query.get(f"{list_key}.step_name")
                for item in doc.get(list_key, []):
                    if item.get("step_name") == matched_name:
                        item[child_key] = value
                        break
            else:
                doc[key] = value

        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value

        for key, value in update.get("$push", {}).items():
            if ".$." in key:
                list_key, child_key = key.split(".$.", 1)
                matched_name = query.get(f"{list_key}.step_name")
                for item in doc.get(list_key, []):
                    if item.get("step_name") == matched_name:
                        item.setdefault(child_key, []).append(value)
                        break
            else:
                doc.setdefault(key, []).append(value)

    def _get(self, doc, dotted_key):
        value = doc
        parts = dotted_key.split(".")
        for index, part in enumerate(parts):
            if isinstance(value, list):
                remaining_key = ".".join(parts[index:])
                return [self._get(item, remaining_key) for item in value]
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value


def install_fake_db(**collections):
    fake_db = SimpleNamespace(
        inspections=FakeCollection(collections.get("inspections")),
        users=FakeCollection(collections.get("users")),
        inspector_profiles=FakeCollection(collections.get("inspector_profiles")),
        inspection_progress=FakeCollection(collections.get("inspection_progress")),
        reports=FakeCollection(collections.get("reports")),
        notifications=FakeCollection(collections.get("notifications")),
    )
    server.db = fake_db
    return fake_db


def test_available_inspections_do_not_expose_security_codes():
    install_fake_db(
        inspections=[
            {
                "id": "inspection-1",
                "status": "pending",
                "security_code": "123456",
                "seller": {"lat": 41.8781, "lng": -87.6298},
            }
        ]
    )

    jobs = asyncio.run(server.get_available_inspections(inspector_lat=41.8781, inspector_lng=-87.6298))

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]


def test_verify_code_cannot_reopen_completed_inspection():
    fake_db = install_fake_db(
        inspections=[
            {
                "id": "inspection-1",
                "status": "completed",
                "security_code": "123456",
            }
        ]
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.verify_security_code("inspection-1", "123456"))

    assert exc.value.status_code == 400
    assert fake_db.inspections.docs[0]["status"] == "completed"


def test_submit_report_only_pays_once():
    fake_db = install_fake_db(
        inspections=[
            {
                "id": "inspection-1",
                "status": "in_progress",
                "inspector_id": "inspector-1",
                "buyer_id": "buyer-1",
                "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
                "total_amount": 250,
            }
        ],
        inspector_profiles=[{"user_id": "inspector-1", "earnings": 0, "total_inspections": 0}],
    )
    report = server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )

    first = asyncio.run(server.submit_report("inspection-1", report))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.submit_report("inspection-1", report))

    assert first["report_id"]
    assert exc.value.status_code == 400
    assert len(fake_db.reports.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 200
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1


def test_upload_rejects_path_traversal_step_name():
    install_fake_db(inspection_progress=[{"inspection_id": "inspection-1", "steps": [], "current_step": 0}])
    upload = SimpleNamespace(filename="photo.jpg", file=None)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.upload_inspection_photo("inspection-1", "../evil", upload))

    assert exc.value.status_code == 400


def test_repeated_complete_step_does_not_skip_steps():
    fake_db = install_fake_db(inspection_progress=[server.build_initial_progress_doc("inspection-1")])

    asyncio.run(server.complete_step("inspection-1", "exterior_front", "ok"))
    asyncio.run(server.complete_step("inspection-1", "exterior_front", "ok"))

    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True
