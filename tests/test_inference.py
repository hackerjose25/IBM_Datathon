"""Unit tests for ML anomaly detector, artifact loading, and latency tracking."""
import tempfile
from pathlib import Path
from backend.schemas import ClaimInput
from backend.ml.inference import detector, ClaimAnomalyDetector

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
    assert evidence.latency_p50_ms >= 0.0
    assert evidence.latency_p95_ms >= 0.0

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

def test_pretrained_model_loaded_from_disk():
    """Verify that detector loads the pre-trained model artifact when present on disk."""
    assert detector.model_loaded_from_disk is True
    assert detector.model is not None
    assert detector.model_version == "1.0.0"

def test_fallback_to_in_memory_when_model_missing():
    """Verify graceful fallback to fitting in-memory baseline when model file is missing."""
    non_existent_path = "/tmp/non_existent_model_file_12345.joblib"
    custom_detector = ClaimAnomalyDetector(model_path=non_existent_path)
    assert custom_detector.model_loaded_from_disk is False
    assert custom_detector.model_version == "in-memory-baseline"
    assert custom_detector.model is not None

    # Verify that prediction works even under in-memory fallback
    claim = ClaimInput(
        claim_id="CLM-FALLBACK-1",
        patient_id="PAT-FB",
        provider_id="PRV-FB",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=500.0,
        service_lines_count=1,
    )
    evidence = custom_detector.predict(claim)
    assert evidence.normalized_score >= 0.0
    assert evidence.inference_latency_ms >= 0.0

def test_latency_tracking_percentiles():
    """Verify that LatencyTracker accurately calculates p50, p95, and count."""
    detector.latency_tracker.clear()
    claim = ClaimInput(
        claim_id="CLM-LATENCY",
        patient_id="PAT-LAT",
        provider_id="PRV-LAT",
        service_date="2026-10-15",
        submission_timestamp="2026-10-17T10:00:00Z",
        diagnosis_code="E11.9",
        procedure_code="99213",
        claim_amount=200.0,
        service_lines_count=1,
    )

    for _ in range(10):
        detector.predict(claim)

    metrics = detector.get_latency_metrics()
    assert metrics["count"] >= 10
    assert metrics["p50_ms"] >= 0.0
    assert metrics["p95_ms"] >= metrics["p50_ms"]
    assert metrics["execution_target"] in ("LOCAL_MOCK", "IBM_LINUXONE")

def test_model_save_and_reload():
    """Verify model can be saved to a versioned artifact and reloaded cleanly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_model_file = Path(tmpdir) / "test_model.joblib"
        detector.save_model(tmp_model_file, version="2.0.0-test")

        new_detector = ClaimAnomalyDetector(model_path=tmp_model_file)
        assert new_detector.model_loaded_from_disk is True
        assert new_detector.model_version == "2.0.0-test"
