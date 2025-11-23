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
        self.client_queues = []  # List of queues, one per connected client

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Broadcasting event: {event_type} to {len(self.client_queues)} clients")

        # Put event in all client queues
        for queue in self.client_queues[:]:  # Create a copy to avoid modification during iteration
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Error broadcasting to client queue: {e}")

    async def event_generator(self):
        """Generate SSE events for a single client"""
        # Create a new queue for this client
        client_queue = asyncio.Queue()
        self.client_queues.append(client_queue)
        logger.info(f"New SSE client connected. Total clients: {len(self.client_queues)}")

        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'message': 'SSE connection established'})}\n\n"

        try:
            while True:
                # Check event queue
                try:
                    event = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    # Send event with proper SSE format: event type + data
                    event_type = event.get('type', 'message')
                    event_data = event.get('data', {})

                    # Include timestamp in the data payload
                    event_data['_timestamp'] = event.get('timestamp')

                    # Format: event: type\ndata: payload\n\n
                    yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                except Exception as e:
                    logger.error(f"Error in event stream: {e}")
                    break
        except asyncio.CancelledError:
            logger.info("Client disconnected from event stream")
        finally:
            # Remove this client's queue when they disconnect
            if client_queue in self.client_queues:
                self.client_queues.remove(client_queue)
            logger.info(f"SSE client disconnected. Remaining clients: {len(self.client_queues)}")

# Global broadcaster instance
broadcaster = EventBroadcaster()
