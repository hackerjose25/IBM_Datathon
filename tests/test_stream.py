"""Tests for WebSocket feeds and synthetic stream control endpoints."""
import pytest
from backend.services.generator import stream_generator

def test_stream_controls(client):
    # Check initial status
    status_res = client.get("/api/stream/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "is_running" in status_data
    assert "execution_target" in status_data
    assert "latency_p50_ms" in status_data
    assert "latency_p95_ms" in status_data
    assert "latency_metrics" in status_data

    # Start stream with 5 claims and 0.1s delay
    start_res = client.post("/api/stream/start?count=5&delay=0.1")
    assert start_res.status_code == 200
    assert start_res.json()["status"] in ("started", "already_running")
    assert "execution_target" in start_res.json()

    # Stop stream
    stop_res = client.post("/api/stream/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "stopped"
    assert "execution_target" in stop_res.json()

def test_websocket_connection_and_ping(client):
    with client.websocket_connect("/ws/claims") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert '{"event": "pong"}' in data
