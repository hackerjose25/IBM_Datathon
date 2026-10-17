"""Integration tests for FastAPI REST routes, triage routing, and reviewer workflow."""

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "ClaimGuard"

def test_ingest_normal_claim(client):
    payload = {
        "claim_id": "CLM-TEST-001",
        "patient_id": "PAT-001",
        "provider_id": "PRV-001",
        "service_date": "2026-10-14",
        "submission_timestamp": "2026-10-17T12:00:00Z",
        "diagnosis_code": "E11.9",
        "procedure_code": "99213",
        "claim_amount": 350.0,
        "service_lines_count": 1,
        "injected_scenario": "normal",
    }
    response = client.post("/api/claims", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == "CLM-TEST-001"
    assert data["category"] == "READY"
    assert data["triage_score"] <= 50.0
    assert data["review_state"] == "PENDING"

def test_ingest_missing_field_routes_to_correction(client):
    payload = {
        "claim_id": "CLM-TEST-002",
        "patient_id": "PAT-002",
        "provider_id": "PRV-002",
        "service_date": "2026-10-14",
        "submission_timestamp": "2026-10-17T12:00:00Z",
        "diagnosis_code": None,  # Missing field
        "procedure_code": "99213",
        "claim_amount": 350.0,
        "service_lines_count": 1,
        "injected_scenario": "missing_field",
    }
    response = client.post("/api/claims", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "CORRECTION"
    assert any(not f["passed"] for f in data["validation_findings"])

def test_ingest_high_amount_routes_to_review(client):
    payload = {
        "claim_id": "CLM-TEST-003",
        "patient_id": "PAT-003",
        "provider_id": "PRV-003",
        "service_date": "2026-10-14",
        "submission_timestamp": "2026-10-17T12:00:00Z",
        "diagnosis_code": "E11.9",
        "procedure_code": "99213",
        "claim_amount": 25000.0,
        "service_lines_count": 8,
        "injected_scenario": "high_amount",
    }
    response = client.post("/api/claims", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "REVIEW"
    assert data["triage_score"] >= 60.0

def test_reviewer_action_workflow(client):
    # Ingest claim first
    payload = {
        "claim_id": "CLM-TEST-004",
        "patient_id": "PAT-004",
        "provider_id": "PRV-004",
        "service_date": "2026-10-14",
        "submission_timestamp": "2026-10-17T12:00:00Z",
        "diagnosis_code": "E11.9",
        "procedure_code": "99213",
        "claim_amount": 18000.0,
        "service_lines_count": 6,
        "injected_scenario": "high_amount",
    }
    ingest_res = client.post("/api/claims", json=payload)
    assert ingest_res.status_code == 201

    # Acknowledge claim
    ack_res = client.post(
        "/api/claims/CLM-TEST-004/action",
        json={
            "action": "ACKNOWLEDGE",
            "reviewer_id": "REV-TEST",
            "notes": "Under review by specialist"
        }
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["review_state"] == "ACKNOWLEDGED"

    # Resolve claim disposition
    resolve_res = client.post(
        "/api/claims/CLM-TEST-004/action",
        json={
            "action": "RESOLVE",
            "disposition": "READY",
            "reviewer_id": "REV-TEST",
            "notes": "Prior authorization verified, approved to submit"
        }
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["review_state"] == "RESOLVED"
    assert resolve_res.json()["disposition"] == "READY"

    # Check detail endpoint and audit trail
    detail_res = client.get("/api/claims/CLM-TEST-004")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["claim"]["review_state"] == "RESOLVED"
    assert len(detail["audit_events"]) >= 3  # INGEST, ACKNOWLEDGE, RESOLVE
