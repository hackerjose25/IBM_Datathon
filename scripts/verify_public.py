"""Observe a public demo stream started in the UI and verify proxy boundaries."""
import argparse
import asyncio
import json
from pathlib import Path
import time
import httpx
import websockets


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--output", default="evidence/public-verification.json")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    headers = {"Origin": args.origin}
    async with httpx.AsyncClient(base_url=base, headers=headers, timeout=30) as client:
        health = await client.get("/health")
        health.raise_for_status()
        assert health.json()["machine_architecture"] == "s390x"
        assert health.headers["access-control-allow-origin"] == args.origin
        preflight = await client.options("/api/stream/start", headers={"Access-Control-Request-Method": "POST"})
        assert preflight.status_code == 204
        assert (await client.post("/api/claims", json={})).status_code == 403
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/health", headers={"Origin": "https://invalid.example"})).status_code == 403
        url = base.replace("https://", "wss://") + "/ws/claims"
        records = {}
        async with websockets.connect(url, origin=args.origin) as socket:
            print("LISTENING: start the synthetic stream in the public dashboard", flush=True)
            started = time.perf_counter()
            while True:
                event = json.loads(await asyncio.wait_for(socket.recv(), timeout=120))
                if event["event"] == "CLAIM_SCORED":
                    records[event["data"]["claim_id"]] = event["data"]
                if event["event"] == "STREAM_METRICS" and event["data"].get("status") == "completed":
                    break
            elapsed = time.perf_counter() - started
        assert len(records) == 100, len(records)
        assert all(c["processing_status"] == "PROCESSED" for c in records.values())
        unusual = next(c for c in records.values() if c["injected_scenario"] == "high_amount")
        action = dict(action="RESOLVE", disposition="REVIEW", reviewer_id="SYN-PUBLIC-VERIFY",
                      notes="Public synthetic integration verification; no real claim disposition")
        saved = await client.post(f"/api/claims/{unusual['claim_id']}/action", json=action)
        saved.raise_for_status()
    async with httpx.AsyncClient(base_url=base, headers=headers, timeout=30) as fresh:
        response = await fresh.get("/api/claims?limit=500")
        response.raise_for_status()
        restored = next(c for c in response.json() if c["claim_id"] == unusual["claim_id"])
        assert restored["reviewer_decision"]["decision"] == "REVIEW"
    report = dict(https_verified=True, cors_origin=args.origin, websocket_events=len(records),
                  all_processed=True, wait_and_stream_seconds=round(elapsed, 3),
                  reviewed_claim_id=unusual["claim_id"], saved_review_restored=True,
                  blocked_direct_ingestion=True, blocked_docs=True, rejected_other_browser_origin=True,
                  environment=health.json(),
                  limitations="Public shared synthetic demo; no authenticated reviewer identity. Elapsed time includes waiting for the human/UI start action and paced streaming; not a throughput benchmark.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
