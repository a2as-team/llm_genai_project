"""SSE (Server-Sent Events) Manager for real-time updates."""

import asyncio
import json
import logging
from typing import Dict, Set, Callable, Any, Optional
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for SSE notifications."""
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_DELETED = "order_deleted"
    RESERVATION_CREATED = "reservation_created"
    RESERVATION_UPDATED = "reservation_updated"
    RESERVATION_DELETED = "reservation_deleted"


class SSEEvent:
    """Represents a single SSE event."""
    
    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        event_id: str = None,
    ):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id or datetime.utcnow().isoformat()
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_sse_format(self) -> str:
        """Convert event to SSE format."""
        return (
            f"id: {self.event_id}\n"
            f"event: {self.event_type.value}\n"
            f"data: {json.dumps({'timestamp': self.timestamp, 'data': self.data})}\n\n"
        )


class SSEManager:
    """Manages SSE connections and broadcasts events."""
    
    def __init__(self):
        self._orders_subscribers: Set[asyncio.Queue] = set()
        self._reservations_subscribers: Set[asyncio.Queue] = set()
        self._lock: Optional[asyncio.Lock] = None
        self._thread_lock = threading.Lock()  # Pour la sécurité thread lors de l'accès à _lock
    
    async def _get_lock(self) -> asyncio.Lock:
        """Get or create the asyncio lock lazily."""
        if self._lock is None:
            with self._thread_lock:
                if self._lock is None:
                    self._lock = asyncio.Lock()
        return self._lock
    
    async def subscribe_orders(self) -> asyncio.Queue:
        """Subscribe to orders events."""
        queue = asyncio.Queue()
        lock = await self._get_lock()
        async with lock:
            self._orders_subscribers.add(queue)
        logger.info(f"New orders subscriber. Total: {len(self._orders_subscribers)}")
        return queue
    
    async def subscribe_reservations(self) -> asyncio.Queue:
        """Subscribe to reservations events."""
        queue = asyncio.Queue()
        lock = await self._get_lock()
        async with lock:
            self._reservations_subscribers.add(queue)
        logger.info(f"New reservations subscriber. Total: {len(self._reservations_subscribers)}")
        return queue
    
    async def unsubscribe_orders(self, queue: asyncio.Queue):
        """Unsubscribe from orders events."""
        lock = await self._get_lock()
        async with lock:
            self._orders_subscribers.discard(queue)
        logger.info(f"Orders subscriber disconnected. Total: {len(self._orders_subscribers)}")
    
    async def unsubscribe_reservations(self, queue: asyncio.Queue):
        """Unsubscribe from reservations events."""
        lock = await self._get_lock()
        async with lock:
            self._reservations_subscribers.discard(queue)
        logger.info(f"Reservations subscriber disconnected. Total: {len(self._reservations_subscribers)}")
    
    async def publish_order_event(self, event_type: EventType, data: Dict[str, Any]):
        """Publish an order event to all subscribers."""
        if event_type.value.startswith("order_"):
            event = SSEEvent(event_type, data)
            lock = await self._get_lock()
            async with lock:
                subscribers = self._orders_subscribers.copy()
            
            for queue in subscribers:
                try:
                    await queue.put(event)
                except Exception as e:
                    logger.error(f"Error publishing order event to subscriber: {e}")
    
    async def publish_reservation_event(self, event_type: EventType, data: Dict[str, Any]):
        """Publish a reservation event to all subscribers."""
        if event_type.value.startswith("reservation_"):
            event = SSEEvent(event_type, data)
            lock = await self._get_lock()
            async with lock:
                subscribers = self._reservations_subscribers.copy()
            
            for queue in subscribers:
                try:
                    await queue.put(event)
                except Exception as e:
                    logger.error(f"Error publishing reservation event to subscriber: {e}")
    
    def get_orders_subscribers_count(self) -> int:
        """Get number of active orders subscribers."""
        return len(self._orders_subscribers)
    
    def get_reservations_subscribers_count(self) -> int:
        """Get number of active reservations subscribers."""
        return len(self._reservations_subscribers)


# Global instance
sse_manager = SSEManager()
