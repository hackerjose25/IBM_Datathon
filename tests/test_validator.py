"""Unit tests for deterministic validation rules and duplicate detection."""
from datetime import datetime, date, timedelta, timezone
from backend.schemas import ClaimInput
from backend.rules.validator import ClaimValidator
from backend.models import ClaimModel

def test_valid_claim_validation(db_session):
    claim = ClaimInput(
        claim_id="CLM-001",
        patient_id="PAT-100",
        provider_id="PRV-200",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=250.0,
        service_lines_count=1,
    )
    findings, has_error, is_duplicate = ClaimValidator.validate_claim(claim, db=db_session)
    assert has_error is False
    assert is_duplicate is False
    assert len(findings) > 0

def test_missing_diagnosis_validation(db_session):
    claim = ClaimInput(
        claim_id="CLM-002",
        patient_id="PAT-100",
        provider_id="PRV-200",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code=None,
        procedure_code="99213",
        claim_amount=250.0,
        service_lines_count=1,
    )
    findings, has_error, is_duplicate = ClaimValidator.validate_claim(claim, db=db_session)
    assert has_error is True
    diag_findings = [f for f in findings if f.rule_id == "VAL_REQ_DIAG"]
    assert len(diag_findings) == 1
    assert diag_findings[0].passed is False

def test_invalid_negative_amount_validation(db_session):
    claim = ClaimInput(
        claim_id="CLM-003",
        patient_id="PAT-100",
        provider_id="PRV-200",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=-50.0,
        service_lines_count=1,
    )
    findings, has_error, is_duplicate = ClaimValidator.validate_claim(claim, db=db_session)
    assert has_error is True
    amount_findings = [f for f in findings if f.rule_id == "VAL_INVALID_AMOUNT"]
    assert len(amount_findings) == 1
    assert amount_findings[0].passed is False

def test_future_service_date_validation(db_session):
    future_date = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
    claim = ClaimInput(
        claim_id="CLM-004",
        patient_id="PAT-100",
        provider_id="PRV-200",
        service_date=future_date,
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=150.0,
        service_lines_count=1,
    )
    findings, has_error, is_duplicate = ClaimValidator.validate_claim(claim, db=db_session)
    assert has_error is True
    date_findings = [f for f in findings if f.rule_id == "VAL_FUTURE_DATE"]
    assert len(date_findings) == 1
    assert date_findings[0].passed is False

def test_duplicate_claim_detection(db_session):
    now_iso = datetime.now(timezone.utc).isoformat()
    # Insert existing claim in DB
    existing = ClaimModel(
        claim_id="CLM-ORIGINAL",
        patient_id="PAT-DUPE",
        provider_id="PRV-DUPE",
        service_date="2026-10-10",
        submission_timestamp=now_iso,
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=300.0,
        service_lines_count=1,
        processing_status="PROCESSED",
        category="READY",
        triage_score=15.0,
        review_state="PENDING",
    )
    db_session.add(existing)
    db_session.commit()

    # Submit duplicate matching claim
    dupe_claim = ClaimInput(
        claim_id="CLM-NEW",
        patient_id="PAT-DUPE",
        provider_id="PRV-DUPE",
        service_date="2026-10-10",
        submission_timestamp=now_iso,
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=300.0,
        service_lines_count=1,
    )
    findings, has_error, is_duplicate = ClaimValidator.validate_claim(dupe_claim, db=db_session)
    assert is_duplicate is True
    dupe_finding = [f for f in findings if f.rule_id == "VAL_DUPLICATE_CLAIM"]
    assert len(dupe_finding) == 1
    assert dupe_finding[0].passed is False
