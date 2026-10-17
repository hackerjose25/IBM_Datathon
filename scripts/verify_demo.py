"""Measure a synthetic workload and verify the 100-event stream and review persistence.

Run from the repo root: python -m scripts.verify_demo
Writes only synthetic claims and one explicitly identified verification disposition.
"""
import asyncio
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time
import uuid
import httpx
import numpy as np
import websockets


def stats(values):
    return {"count": len(values), "mean_ms": round(float(np.mean(values)), 3),
            "median_ms": round(float(np.median(values)), 3),
            "p95_ms": round(float(np.percentile(values, 95)), 3)}


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="evidence/local-verification.json")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    run = uuid.uuid4().hex[:8]
    request_times, inference_times, records = [], [], []
    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        health = (await client.get("/health")).json()
        assert health["status"] == "HEALTHY" and health["model_loaded_from_disk"]
        started = time.perf_counter()
        # Serial HTTP load; 100 deterministic synthetic normal-shaped inputs.
        for i in range(100):
            payload = dict(claim_id=f"VERIFY-{run}-{i:03}", patient_id=f"SYN-{run}-{i}",
                           provider_id="PRV-001", service_date="2026-10-14",
                           submission_timestamp=datetime.now(timezone.utc).isoformat(),
                           diagnosis_code="E11.9", procedure_code="99213", claim_amount=350+i,
                           service_lines_count=1, injected_scenario="normal")
            before = time.perf_counter()
            response = await client.post("/api/claims", json=payload)
            request_times.append((time.perf_counter()-before)*1000)
            response.raise_for_status()
            record = response.json()
            assert record["processing_status"] == "PROCESSED"
            inference_times.append(record["anomaly_evidence"]["inference_latency_ms"])
            records.append(record)
        http_elapsed = time.perf_counter()-started

        # Actual generator endpoint and actual WebSocket delivery, not a mocked loop.
        stream_records = {}
        websocket_url = base.replace("https://", "wss://").replace("http://", "ws://")+"/ws/claims"
        async with websockets.connect(websocket_url) as socket:
            started = time.perf_counter()
            response = await client.post("/api/stream/start?count=100&delay=0.1")
            response.raise_for_status()
            assert response.json()["status"] == "started", "Another stream is already active"
            while True:
                event = json.loads(await asyncio.wait_for(socket.recv(), timeout=60))
                if event["event"] == "CLAIM_SCORED":
                    stream_records[event["data"]["claim_id"]] = event["data"]
                if event["event"] == "STREAM_METRICS" and event["data"].get("status") == "completed":
                    break
            stream_elapsed = time.perf_counter()-started
        assert len(stream_records) == 100, f"Expected 100 claims, received {len(stream_records)}"
        assert all(c["processing_status"] == "PROCESSED" for c in stream_records.values())
        unusual = next(c for c in stream_records.values() if c["injected_scenario"] == "high_amount")
        action = dict(action="RESOLVE", disposition="REVIEW", reviewer_id="SYN-VERIFICATION",
                      notes="Synthetic workflow verification; human investigation remains required")
        response = await client.post(f"/api/claims/{unusual['claim_id']}/action", json=action)
        response.raise_for_status()
    # New connection simulates reloading state from the persisted API.
    async with httpx.AsyncClient(base_url=base, timeout=30) as fresh:
        detail = (await fresh.get(f"/api/claims/{unusual['claim_id']}")).json()
        assert detail["claim"]["reviewer_decision"]["decision"] == "REVIEW"
        assert detail["claim"]["review_state"] == "RESOLVED"
        assert any(a["action"] == "RESOLVE" and a["reviewer_id"] == "SYN-VERIFICATION" for a in detail["audit_events"])
    result = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), environment=health,
                  client_platform=platform.platform(),
                  workload="Serial HTTP to the measured server: 100 claims, amounts 350..449, one provider/procedure, unique patients; no warmup; concurrency 1. Separate generator stream: 100 synthetic claims, random seed 42, 0.1s pacing; timestamps and run IDs vary.",
                  inference=stats(inference_times), end_to_end_http=stats(request_times),
                  http_throughput_claims_per_second=round(100/http_elapsed,3),
                  stream=dict(received=len(stream_records), seconds=round(stream_elapsed,3),
                              claims_per_second=round(100/stream_elapsed,3),
                              categories=dict(Counter(c["category"] for c in stream_records.values()))),
                  reviewed_claim_id=unusual["claim_id"], review_persisted=True,
                  limitations=f"Measured on {platform.system()} {platform.machine()}. End-to-end includes HTTP, validation, inference, persistence and broadcast; inference timing includes preprocessing and evidence generation. Deployment attribution also requires provisioning and SSH/architecture evidence. No real-world quality or fraud accuracy claim.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
