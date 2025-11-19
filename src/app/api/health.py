"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
