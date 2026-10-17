"""Unit tests for ML anomaly detector and feature extraction."""
from backend.schemas import ClaimInput
from backend.ml.inference import detector

def test_feature_extraction():
    claim = ClaimInput(
        claim_id="CLM-F1",
        patient_id="PAT-10",
        provider_id="PRV-20",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=1500.0,
        service_lines_count=3,
    )
    features = detector.extract_features(claim)
    assert features.shape == (1, 4)
    assert features[0, 1] == 3

def test_inference_latency_and_score():
    claim = ClaimInput(
        claim_id="CLM-F2",
        patient_id="PAT-10",
        provider_id="PRV-20",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=450.0,
        service_lines_count=1,
    )
    evidence = detector.predict(claim)
    assert evidence.inference_latency_ms >= 0.0
    assert 0.0 <= evidence.normalized_score <= 100.0
    assert len(evidence.factors) > 0
    assert evidence.execution_target in ("LOCAL_MOCK", "IBM_LINUXONE")

def test_high_amount_scenario_anomaly():
    claim = ClaimInput(
        claim_id="CLM-F3",
        patient_id="PAT-99",
        provider_id="PRV-99",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=35000.0,
        service_lines_count=8,
        injected_scenario="high_amount",
    )
    evidence = detector.predict(claim)
    assert evidence.is_anomaly is True
    assert any("High billed amount" in f for f in evidence.factors)
