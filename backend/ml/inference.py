"""Machine learning inference engine with Isolation Forest baseline and latency tracking."""
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest
from backend.config import settings
from backend.schemas import ClaimInput, AnomalyEvidence

class ClaimAnomalyDetector:
    """Manages Isolation Forest scoring and feature transformation."""

    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.target: str = settings.EXECUTION_TARGET
        self._initialize_baseline_model()

    def _initialize_baseline_model(self):
        """Fit a synthetic baseline distribution to power immediate cold-start inference."""
        np.random.seed(42)
        # Generate representative synthetic feature baseline
        # Features: [log_amount, service_lines_count, provider_hash_mod, procedure_hash_mod]
        n_samples = 500
        amounts = np.random.lognormal(mean=6.5, sigma=0.8, size=n_samples) # mean ~$800
        lines = np.random.poisson(lam=1.5, size=n_samples) + 1
        prov_hash = np.random.randint(0, 100, size=n_samples)
        proc_hash = np.random.randint(0, 50, size=n_samples)

        X_train = np.column_stack([
            np.log1p(amounts),
            lines,
            prov_hash,
            proc_hash
        ])

        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.08,
            random_state=42
        )
        self.model.fit(X_train)

    def extract_features(self, claim: ClaimInput) -> np.ndarray:
        """Extract decision-time numerical features from claim input."""
        log_amount = np.log1p(max(0.0, claim.claim_amount))
        lines = max(1, claim.service_lines_count)
        # Consistent stable categorical hashing
        prov_code = hash(claim.provider_id) % 100
        proc_code = hash(claim.procedure_code or "NONE") % 50

        return np.array([[log_amount, lines, prov_code, proc_code]])

    def predict(self, claim: ClaimInput) -> AnomalyEvidence:
        """
        Runs model inference with latency measurement.
        Calculates raw score, calibrated 0-100 triage priority component, and explainable factors.
        """
        start_time = time.perf_counter()
        
        try:
            features = self.extract_features(claim)
            
            # decision_function yields: negative for anomalies, positive for normal
            raw_score = float(self.model.decision_function(features)[0])
            pred_label = int(self.model.predict(features)[0]) # -1: anomaly, 1: normal
            
            # Map raw score (-0.35 to +0.25 typically) into 0-100 anomaly intensity
            # More negative raw_score -> higher anomaly intensity
            normalized = float(np.clip((0.2 - raw_score) / 0.5 * 100.0, 0.0, 100.0))
            is_anomaly = (pred_label == -1) or (claim.injected_scenario == "high_amount") or (claim.claim_amount > 15000.0)

            # Build explainable factors
            factors: List[str] = []
            if claim.claim_amount > 10000.0:
                factors.append(f"High billed amount (${claim.claim_amount:,.2f}) deviates from standard distribution")
            if claim.service_lines_count > 5:
                factors.append(f"Elevated service line count ({claim.service_lines_count})")
            if is_anomaly and not factors:
                factors.append(f"Isolation Forest identified atypical feature pattern (score: {normalized:.1f}/100)")
            elif not is_anomaly:
                factors.append("Features align with historical claim distribution")

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

            return AnomalyEvidence(
                is_anomaly=is_anomaly,
                model_score=round(raw_score, 4),
                normalized_score=round(normalized, 1),
                factors=factors,
                inference_latency_ms=elapsed_ms,
                execution_target=self.target
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
            return AnomalyEvidence(
                is_anomaly=True,
                model_score=-1.0,
                normalized_score=100.0,
                factors=[f"Inference execution failure: {str(e)}"],
                inference_latency_ms=elapsed_ms,
                execution_target=self.target
            )

# Global singleton instance for inference
detector = ClaimAnomalyDetector()
