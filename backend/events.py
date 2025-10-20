"""
Server-Sent Events (SSE) module for real-time updates
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EventBroadcaster:
    """Manages SSE connections and broadcasts events to all connected clients"""

    def __init__(self):
        self.clients = set()
        self.event_queue = asyncio.Queue()

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Broadcasting event: {event_type}")
        await self.event_queue.put(event)

    async def event_generator(self):
        """Generate SSE events for a single client"""
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connection established'})}\n\n"

        try:
            while True:
                # Check event queue
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                except Exception as e:
                    logger.error(f"Error in event stream: {e}")
                    break
        except asyncio.CancelledError:
            logger.info("Client disconnected from event stream")

# Global broadcaster instance
broadcaster = EventBroadcaster()
