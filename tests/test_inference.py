"""Unit tests for ML anomaly detector, artifact loading, and latency tracking."""
import tempfile
import warnings
import joblib
import numpy as np
from sklearn.exceptions import InconsistentVersionWarning
from pathlib import Path
from backend.schemas import ClaimInput
from backend.ml.inference import detector, ClaimAnomalyDetector
from backend.ml.train import train_and_save_model
from backend.ml.contract import runtime_versions, FEATURE_NAMES, PREPROCESSING


def test_training_and_reloaded_inference_are_repeatable(tmp_path):
    paths = [train_and_save_model(tmp_path / f"model-{i}.joblib") for i in range(2)]
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        engines = [ClaimAnomalyDetector(path) for path in paths]
    claim = ClaimInput(claim_id="REPEAT-1", patient_id="SYN-1", provider_id="PRV-20",
                       procedure_code="99213", diagnosis_code="E11.9", service_date="2026-10-15",
                       submission_timestamp="2026-10-17T10:00:00Z", claim_amount=450, service_lines_count=1)
    results = [engine.predict(claim) for engine in engines for _ in range(3)]
    assert all(engine.model_loaded_from_disk for engine in engines)
    assert all(result.model_score == results[0].model_score for result in results)
    assert all(result.normalized_score == results[0].normalized_score for result in results)
    assert not any("failure" in factor.lower() for result in results for factor in result.factors)
    artifact = joblib.load(paths[0])
    assert artifact["runtime_versions"] == runtime_versions()
    assert artifact["feature_names"] == FEATURE_NAMES
    assert artifact["preprocessing"] == PREPROCESSING
    np.testing.assert_array_equal(engines[0].extract_features(claim), engines[1].extract_features(claim))


def test_incompatible_artifact_is_rejected(tmp_path):
    path = train_and_save_model(tmp_path / "incompatible.joblib")
    artifact = joblib.load(path)
    artifact["runtime_versions"]["scikit_learn"] = "unsupported-version"
    joblib.dump(artifact, path)
    engine = ClaimAnomalyDetector(path)
    assert engine.model is None
    assert not engine.model_loaded_from_disk
    assert engine.model_version == "unavailable"


def test_scenario_label_does_not_influence_inference():
    claim = ClaimInput(claim_id="LABEL-1", patient_id="SYN-1", provider_id="PRV-001",
                       procedure_code="99213", diagnosis_code="E11.9", service_date="2026-10-15",
                       submission_timestamp="2026-10-17T10:00:00Z", claim_amount=350)
    normal = detector.predict(claim)
    labelled = detector.predict(claim.model_copy(update={"injected_scenario": "high_amount"}))
    assert normal.model_score == labelled.model_score
    assert normal.is_anomaly == labelled.is_anomaly


def test_linuxone_missing_artifact_does_not_silently_fit(monkeypatch, tmp_path):
    from backend.config import settings
    monkeypatch.setattr(settings, "EXECUTION_TARGET", "IBM_LINUXONE")
    engine = ClaimAnomalyDetector(tmp_path / "missing.joblib")
    assert engine.model is None
    assert not engine.model_loaded_from_disk

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
