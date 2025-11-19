"""API routes router.

Aggregates all API endpoint routers into a single main router.
"""

from fastapi import APIRouter
from .health import router as health_router
from .chat import router as chat_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
__all__ = [

    "health_router",
    "chat_router",
]

