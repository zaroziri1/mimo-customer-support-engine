"""WebSocket handler for real-time dashboard updates."""
import json
import asyncio
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

connected_clients: Set[WebSocket] = set()


async def websocket_dashboard(websocket: WebSocket):
    """Handle WebSocket connections for the real-time dashboard."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"Dashboard client connected. Total: {len(connected_clients)}")

    try:
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg.get("type") == "subscribe":
                    await websocket.send_json({"type": "subscribed", "channel": msg.get("channel")})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        logger.info(f"Dashboard client disconnected. Total: {len(connected_clients)}")
    except Exception as e:
        connected_clients.discard(websocket)
        logger.error(f"WebSocket error: {e}")


async def broadcast_update(event_type: str, data: dict):
    """Broadcast an update to all connected dashboard clients."""
    message = json.dumps({"type": event_type, "data": data})
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.add(client)
    connected_clients.difference_update(disconnected)
