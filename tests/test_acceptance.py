"""Synthetic workflow acceptance scenarios, never real-world fraud labels."""
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from backend.models import AuditEventModel
from backend.ml.inference import detector


def payload(claim_id="ACCEPT-1", **changes):
    return dict(claim_id=claim_id, patient_id="SYN-ACCEPT", provider_id="PRV-001",
                service_date="2026-10-14", submission_timestamp=datetime.now(timezone.utc).isoformat(),
                diagnosis_code="E11.9", procedure_code="99213", claim_amount=350,
                service_lines_count=1, **changes)


@pytest.mark.parametrize("changes,category", [
    ({}, "READY"), ({"diagnosis_code": None}, "CORRECTION"),
    ({"claim_amount": -1}, "CORRECTION"), ({"claim_amount": 0}, "CORRECTION"),
    ({"service_date": "bad-date"}, "CORRECTION"),
    ({"claim_amount": 35000, "service_lines_count": 8}, "REVIEW"),
    ({"claim_amount": 35000, "diagnosis_code": None}, "CORRECTION"),
])
def test_scenario_routes(client, changes, category):
    claim = payload()
    claim.update(changes)
    with client.websocket_connect("/ws/claims") as ws:
        result = client.post("/api/claims", json=claim)
        assert result.status_code == 201
        scored = result.json()
        assert scored["processing_status"] == "PROCESSED"
        assert scored["category"] == category
        event = ws.receive_json()
        assert event["event"] == "CLAIM_SCORED"
        assert event["data"]["claim_id"] == claim["claim_id"]


def test_inference_failure_is_explicit_and_persisted(client, monkeypatch):
    def broken(*args):
        raise RuntimeError("simulated scoring outage")
    monkeypatch.setattr(detector.model, "decision_function", broken)
    result = client.post("/api/claims", json=payload()).json()
    assert result["processing_status"] == "ERROR"
    assert result["category"] != "READY"
    assert result["anomaly_evidence"]["inference_error"] == "simulated scoring outage"
    assert client.get("/api/claims").json()[0]["processing_status"] == "ERROR"


def test_duplicate_and_replay_preserve_review(client, db_session):
    original = payload()
    assert client.post("/api/claims", json=original).status_code == 201
    duplicate = {**original, "claim_id": "ACCEPT-DUP"}
    result = client.post("/api/claims", json=duplicate).json()
    assert result["category"] == "REVIEW"
    assert any(f["rule_id"] == "VAL_DUPLICATE_CLAIM" for f in result["validation_findings"])
    action = dict(action="RESOLVE", disposition="CORRECTION", reviewer_id="SYN-REVIEWER", notes="Synthetic verification")
    assert client.post("/api/claims/ACCEPT-1/action", json=action).status_code == 200
    assert client.post("/api/claims", json=original).status_code == 400
    db_session.expire_all()
    record = client.get("/api/claims").json()[1]
    assert record["review_state"] == "RESOLVED"
    assert record["reviewer_decision"]["decision"] == "CORRECTION"
    assert record["category"] == "READY"  # model recommendation remains separate
    with Session(db_session.bind) as fresh_session:
        actions = fresh_session.query(AuditEventModel).filter_by(claim_id="ACCEPT-1").all()
        assert [a.action for a in actions] == ["INGEST_AND_SCORE", "RESOLVE"]


def test_duplicate_window_excludes_later_and_old_events(client):
    original = payload()
    original["submission_timestamp"] = "2026-10-17T12:00:00Z"
    assert client.post("/api/claims", json=original).status_code == 201
    earlier = {**original, "claim_id": "EARLIER", "submission_timestamp": "2026-10-16T12:00:00Z"}
    result = client.post("/api/claims", json=earlier).json()
    assert not any(f["rule_id"] == "VAL_DUPLICATE_CLAIM" for f in result["validation_findings"])
    outside = {**original, "claim_id": "OUTSIDE", "submission_timestamp": "2026-12-17T12:00:00Z"}
    result = client.post("/api/claims", json=outside).json()
    assert not any(f["rule_id"] == "VAL_DUPLICATE_CLAIM" for f in result["validation_findings"])


def test_required_identifiers_rejected(client):
    claim = payload()
    del claim["patient_id"]
    assert client.post("/api/claims", json=claim).status_code == 422
