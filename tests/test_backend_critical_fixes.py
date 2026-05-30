import asyncio
import copy
import io
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "autocheck_test")

from backend import server


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, _limit):
        return copy.deepcopy(self.docs)


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [copy.deepcopy(doc) for doc in docs or []]

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if matches(doc, query):
                return project(doc, projection)
        return None

    def find(self, query, projection=None):
        return FakeCursor([project(doc, projection) for doc in self.docs if matches(doc, query)])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def update_one(self, query, update):
        for doc in self.docs:
            if matches(doc, query):
                apply_update(doc, query, update)
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)


class FakeDb:
    def __init__(self, **collections):
        self.inspections = FakeCollection(collections.get("inspections"))
        self.users = FakeCollection(collections.get("users"))
        self.inspection_progress = FakeCollection(collections.get("inspection_progress"))
        self.reports = FakeCollection(collections.get("reports"))
        self.inspector_profiles = FakeCollection(collections.get("inspector_profiles"))
        self.notifications = FakeCollection(collections.get("notifications"))


def matches(doc, query):
    return all(match_value(doc, key, expected) for key, expected in query.items())


def match_value(doc, key, expected):
    actual = get_value(doc, key)
    if isinstance(expected, dict) and "$ne" in expected:
        return actual != expected["$ne"]
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


def get_value(doc, dotted_key):
    value = doc
    for part in dotted_key.split("."):
        if isinstance(value, list):
            return [item.get(part) for item in value if isinstance(item, dict)]
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def project(doc, projection):
    doc = copy.deepcopy(doc)
    if not projection:
        return doc

    included = {key for key, value in projection.items() if value}
    excluded = {key for key, value in projection.items() if not value}
    if included:
        return {key: copy.deepcopy(doc[key]) for key in included if key in doc}
    for key in excluded:
        doc.pop(key, None)
    return doc


def apply_update(doc, query, update):
    for key, value in update.get("$set", {}).items():
        set_value(doc, query, key, value)
    for key, value in update.get("$push", {}).items():
        target = get_positional_target(doc, query, key)
        target.append(value)
    for key, value in update.get("$inc", {}).items():
        doc[key] = doc.get(key, 0) + value


def set_value(doc, query, key, value):
    if ".$." in key:
        prefix, field = key.split(".$.", 1)
        target_name = query[f"{prefix}.step_name"]
        for item in doc[prefix]:
            if item["step_name"] == target_name:
                item[field] = value
                return
    doc[key] = value


def get_positional_target(doc, query, key):
    prefix, field = key.split(".$.", 1)
    target_name = query[f"{prefix}.step_name"]
    for item in doc[prefix]:
        if item["step_name"] == target_name:
            return item[field]
    raise AssertionError("No positional target matched")


def sample_inspection(status="pending"):
    return {
        "id": "inspection-1",
        "buyer_id": "buyer-1",
        "buyer_name": "Buyer One",
        "vehicle": {"year": 2020, "make": "Toyota", "model": "Camry"},
        "seller": {"lat": 41.8781, "lng": -87.6298},
        "package_type": "premium",
        "package_price": 250.0,
        "tip_amount": 20.0,
        "total_amount": 270.0,
        "security_code": "123456",
        "status": status,
        "inspector_id": "inspector-1" if status != "pending" else None,
        "inspector_name": "Inspector One" if status != "pending" else None,
        "created_at": "2026-05-30T00:00:00+00:00",
        "accepted_at": "2026-05-30T00:01:00+00:00" if status != "pending" else None,
        "completed_at": None,
    }


def sample_progress(completed=False, current_step=0):
    steps = [
        server.InspectionStep(
            step_name=step["step_name"],
            description=step["description"],
            required_photos=step["required_photos"],
            completed=completed if index == 0 else False,
        ).model_dump()
        for index, step in enumerate(server.INSPECTION_STEPS)
    ]
    return {
        "inspection_id": "inspection-1",
        "steps": steps,
        "current_step": current_step,
        "started_at": "2026-05-30T00:02:00+00:00",
    }


def sample_report():
    return server.InspectionReportCreate(
        inspection_id="inspection-1",
        steps=[],
        overall_notes="Looks good",
        recommendation="buy",
    )


def run(coro):
    return asyncio.run(coro)


def test_available_jobs_do_not_leak_security_codes(monkeypatch):
    monkeypatch.setattr(server, "db", FakeDb(inspections=[sample_inspection("pending")]))

    jobs = run(server.get_available_inspections())

    assert len(jobs) == 1
    assert "security_code" not in jobs[0]
    assert jobs[0]["distance_miles"] == 0.0


def test_accept_response_is_sanitized_and_duplicate_accept_does_not_notify(monkeypatch):
    fake_db = FakeDb(
        inspections=[sample_inspection("pending")],
        users=[{"id": "inspector-1", "full_name": "Inspector One"}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    accepted = run(server.accept_inspection("inspection-1", "inspector-1"))

    assert accepted["status"] == "accepted"
    assert "security_code" not in accepted
    assert len(fake_db.notifications.docs) == 1
    with pytest.raises(HTTPException) as error:
        run(server.accept_inspection("inspection-1", "inspector-1"))
    assert error.value.status_code == 400
    assert len(fake_db.notifications.docs) == 1


def test_verify_code_is_idempotent_and_never_reopens_completed_jobs(monkeypatch):
    fake_db = FakeDb(inspections=[sample_inspection("accepted")])
    monkeypatch.setattr(server, "db", fake_db)

    run(server.verify_security_code("inspection-1", "123456"))
    run(server.verify_security_code("inspection-1", "123456"))

    assert fake_db.inspections.docs[0]["status"] == "in_progress"
    assert len(fake_db.inspection_progress.docs) == 1

    fake_db.inspections.docs[0]["status"] = "completed"
    with pytest.raises(HTTPException) as error:
        run(server.verify_security_code("inspection-1", "123456"))
    assert error.value.status_code == 400
    assert fake_db.inspections.docs[0]["status"] == "completed"


def test_complete_step_requires_progress_and_is_idempotent(monkeypatch):
    fake_db = FakeDb(inspections=[sample_inspection("in_progress")])
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as error:
        run(server.complete_step("inspection-1", "exterior_front"))
    assert error.value.status_code == 404

    fake_db.inspection_progress.docs.append(sample_progress())
    run(server.complete_step("inspection-1", "exterior_front", "front checked"))
    run(server.complete_step("inspection-1", "exterior_front", "front checked again"))

    progress = fake_db.inspection_progress.docs[0]
    assert progress["current_step"] == 1
    assert progress["steps"][0]["completed"] is True
    assert progress["steps"][0]["notes"] == "front checked"


def test_upload_photo_rejects_path_traversal_step_before_writing(monkeypatch, tmp_path):
    fake_db = FakeDb(inspection_progress=[sample_progress()])
    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)
    upload = SimpleNamespace(filename="photo.jpg", file=io.BytesIO(b"image"))

    with pytest.raises(HTTPException) as error:
        run(server.upload_inspection_photo("inspection-1", "../../../tmp/payload", upload))

    assert error.value.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_submit_report_retry_does_not_duplicate_report_payout_or_notification(monkeypatch):
    fake_db = FakeDb(
        inspections=[sample_inspection("in_progress")],
        inspector_profiles=[{"user_id": "inspector-1", "total_inspections": 0, "earnings": 0.0}],
    )
    monkeypatch.setattr(server, "db", fake_db)

    first = run(server.submit_report("inspection-1", sample_report()))
    second = run(server.submit_report("inspection-1", sample_report()))

    assert second["report_id"] == first["report_id"]
    assert len(fake_db.reports.docs) == 1
    assert len(fake_db.notifications.docs) == 1
    assert fake_db.inspector_profiles.docs[0]["total_inspections"] == 1
    assert fake_db.inspector_profiles.docs[0]["earnings"] == 216.0
