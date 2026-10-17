"""Synthetic claim stream generator for realistic testing and the 100-claim demo stream."""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from backend.schemas import ClaimInput
from backend.services.claim_service import ClaimService
from backend.services.stream_manager import stream_manager
from backend.ml.inference import detector
from backend.config import settings
from backend.database import SessionLocal

DIAGNOSIS_CODES = ["E11.9", "I10", "M54.5", "J45.909", "F41.1", "K21.9"]
PROCEDURE_CODES = ["99213", "99214", "80053", "36415", "71045", "99203"]

class ClaimStreamGenerator:
    """Simulates real-time ingestion of synthetic claims."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._claim_counter = 1000
        self._random = random.Random(42)
        self._run_id = uuid.uuid4().hex[:8].upper()

    @property
    def is_running(self) -> bool:
        return self._running

    def generate_single_claim(self, scenario: str = "normal") -> ClaimInput:
        self._claim_counter += 1
        claim_id = f"CLM-{self._run_id}-{self._claim_counter:04d}"
        patient_id = f"PAT-{self._random.randint(1000, 9999)}"
        provider_id = f"PRV-{self._random.randint(100, 999)}"
        now = datetime.now(timezone.utc)
        service_date = (now - timedelta(days=self._random.randint(1, 14))).strftime("%Y-%m-%d")
        submission_timestamp = now.isoformat()

        diag = self._random.choice(DIAGNOSIS_CODES)
        proc = self._random.choice(PROCEDURE_CODES)
        lines = self._random.randint(1, 3)

        if scenario == "high_amount":
            amount = round(self._random.uniform(18000.0, 45000.0), 2)
            lines = self._random.randint(5, 12)
        elif scenario == "missing_field":
            diag = None
            amount = round(self._random.uniform(150.0, 900.0), 2)
        elif scenario == "invalid_amount":
            amount = -50.00
        else: # normal
            amount = round(self._random.uniform(85.0, 1850.0), 2)

        return ClaimInput(
            claim_id=claim_id,
            patient_id=patient_id,
            provider_id=provider_id,
            service_date=service_date,
            submission_timestamp=submission_timestamp,
            diagnosis_code=diag,
            procedure_code=proc,
            claim_amount=amount,
            service_lines_count=lines,
            injected_scenario=scenario,
        )

    async def run_stream(self, count: int = 100, delay_seconds: float = 1.0):
        """Streams a defined batch of synthetic claims with realistic distributions."""
        self._running = True
        try:
            for i in range(count):
                if not self._running:
                    break

                # 85% normal, 7% high amount, 5% missing field, 3% invalid amount
                roll = self._random.random()
                if roll < 0.85:
                    scenario = "normal"
                elif roll < 0.92:
                    scenario = "high_amount"
                elif roll < 0.97:
                    scenario = "missing_field"
                else:
                    scenario = "invalid_amount"

                claim = self.generate_single_claim(scenario=scenario)
                db = SessionLocal()
                try:
                    await ClaimService.process_claim(claim, db)
                finally:
                    db.close()

                # Periodically broadcast stream metrics (every 10 claims or on last claim)
                if (i + 1) % 10 == 0 or (i + 1) == count:
                    metrics = detector.get_latency_metrics()
                    await stream_manager.broadcast("STREAM_METRICS", {
                        "execution_target": settings.EXECUTION_TARGET,
                        "claims_streamed": i + 1,
                        "total_target": count,
                        "latency_p50_ms": metrics["p50_ms"],
                        "latency_p95_ms": metrics["p95_ms"],
                        "latency_metrics": metrics,
                    })

                await asyncio.sleep(delay_seconds)
        finally:
            self._running = False
            # Final stream metrics broadcast
            metrics = detector.get_latency_metrics()
            await stream_manager.broadcast("STREAM_METRICS", {
                "execution_target": settings.EXECUTION_TARGET,
                "status": "completed",
                "latency_p50_ms": metrics["p50_ms"],
                "latency_p95_ms": metrics["p95_ms"],
                "latency_metrics": metrics,
            })

    def start(self, count: int = 100, delay_seconds: float = 1.0):
        if not self._running:
            self._running = True
            self._random.seed(42)
            self._run_id = uuid.uuid4().hex[:8].upper()
            self._task = asyncio.create_task(self.run_stream(count=count, delay_seconds=delay_seconds))

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

stream_generator = ClaimStreamGenerator()
