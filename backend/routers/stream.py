"""Streaming router with WebSocket handler and synthetic stream controls."""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.services.stream_manager import stream_manager
from backend.services.generator import stream_generator
from backend.ml.inference import detector
from backend.config import settings

router = APIRouter(tags=["Streaming"])

@router.websocket("/ws/claims")
async def websocket_claims_feed(websocket: WebSocket):
    """Live WebSocket feed for claim arrivals, alerts, and reviewer actions."""
    await stream_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and accept optional ping/pong or client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception:
        stream_manager.disconnect(websocket)

@router.post("/api/stream/start")
async def start_stream(count: int = Query(100, ge=1, le=1000), delay: float = Query(1.0, ge=0.1, le=10.0)):
    """Start synthetic claim generation stream in the background."""
    if stream_generator.is_running:
        return {"status": "already_running", "message": "Stream is already active"}
    stream_generator.start(count=count, delay_seconds=delay)
    return {
        "status": "started",
        "claims_count": count,
        "delay_seconds": delay,
        "execution_target": settings.EXECUTION_TARGET,
    }

@router.post("/api/stream/stop")
async def stop_stream():
    """Stop the running synthetic claim stream."""
    stream_generator.stop()
    metrics = detector.get_latency_metrics()
    return {
        "status": "stopped",
        "execution_target": settings.EXECUTION_TARGET,
        "latency_metrics": metrics,
    }

@router.get("/api/stream/status")
async def stream_status():
    """Return current stream generation status, execution target, and latency percentiles."""
    metrics = detector.get_latency_metrics()
    return {
        "is_running": stream_generator.is_running,
        "active_clients": len(stream_manager.active_connections),
        "execution_target": settings.EXECUTION_TARGET,
        "latency_p50_ms": metrics["p50_ms"],
        "latency_p95_ms": metrics["p95_ms"],
        "latency_metrics": metrics,
    }
