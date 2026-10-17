"""Versioned preprocessing contract shared by training and inference."""
import platform
import joblib
import numpy as np
import sklearn

FEATURE_NAMES = ["log_amount", "service_lines_count", "provider_hash", "procedure_hash"]
PREPROCESSING = {
    "version": 1,
    "amount": "log1p(max(0, amount))",
    "lines": "max(1, service_lines_count)",
    "provider": "crc32(utf8(provider_id)) modulo 100",
    "procedure": "crc32(utf8(procedure_code or NONE)) modulo 50",
}

def runtime_versions():
    return {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
            "numpy": np.__version__, "joblib": joblib.__version__}
