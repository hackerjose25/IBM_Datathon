"""WebSocket streaming connection manager."""
import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket
from backend.schemas import WebSocketEnvelope

logger = logging.getLogger("claimguard.stream")

class StreamManager:
    """Manages active WebSocket connections and broadcasts real-time events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        if not self.active_connections:
            return

        envelope = WebSocketEnvelope(event=event_type, data=data)
        message_json = envelope.model_dump_json()

        stale_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error sending message to client: {e}")
                stale_connections.add(connection)

        for stale in stale_connections:
            self.active_connections.discard(stale)

stream_manager = StreamManager()
