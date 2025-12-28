"""API routes router.

Aggregates all API endpoint routers into a single main router.
"""

from fastapi import APIRouter
from .health import router as health_router
from .livechat import router as livechat_router
from .orders_reservations import router as orders_reservations_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(livechat_router)
api_router.include_router(orders_reservations_router)
__all__ = [

    "health_router",
    "livechat_router",
    "orders_reservations_router",
]

