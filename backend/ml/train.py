"""Model training script to produce versioned Isolation Forest artifact."""
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

def train_and_save_model(output_path: Optional[Union[str, Path]] = None) -> Path:
    """Trains a baseline Isolation Forest model on synthetic claim features and saves to disk."""
    if output_path is None:
        target_path = Path(__file__).resolve().parent / "model.joblib"
    else:
        target_path = Path(output_path)

    np.random.seed(42)
    n_samples = 1000

    # Synthetic baseline feature generation:
    # Features: [log_amount, service_lines_count, provider_hash, procedure_hash]
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

    model = IsolationForest(
        n_estimators=100,
        contamination=0.08,
        random_state=42
    )
    model.fit(X_train)

    artifact = {
        "model": model,
        "version": "1.0.0",
        "algorithm": "IsolationForest",
        "target_platform": "IBM LinuxONE (s390x) & x86_64 compatible",
        "feature_names": ["log_amount", "service_lines_count", "provider_hash", "procedure_hash"],
        "parameters": {
            "n_estimators": 100,
            "contamination": 0.08,
            "random_state": 42,
            "n_samples": n_samples,
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    target_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, target_path, compress=3)
    print(f"Versioned model artifact successfully saved to: {target_path}")
    return target_path

if __name__ == "__main__":
    train_and_save_model()
