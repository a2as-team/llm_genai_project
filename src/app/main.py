"""FastAPI application factory and server configuration.

Handles app initialization, CORS setup, database connection management,
and both development and production server modes.
"""

import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api import api_router
from src.config import app_settings
from src.bdd.get_db_url import create_db_pool
from src.utils.restaurant_cache import RestaurantCache

# Configure logging: INFO for our code, WARNING for Google libs (to hide prompts)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)

# Silence verbose Google libraries (they log prompts at INFO/DEBUG level)
logging.getLogger("google.adk").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("google.api_core").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=app_settings.APP_NAME,
        debug=app_settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=["http://localhost:3000"],
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "ok": True,
            "app": app_settings.APP_NAME,
            "env": app_settings.ENV,
        }

    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    async def on_startup():
        """Initialize database connection and caches on application startup."""
        logger.info("Starting FastAPI application...")

        if os.getenv("SKIP_DB_INIT", "false").lower() == "true":
            app.state.db_pool = None
            logger.warning("DB init skipped (SKIP_DB_INIT=true).")
            return

        try:
            timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "30"))
            app.state.db_pool = await asyncio.wait_for(
                create_db_pool(), timeout=timeout
            )
            logger.info("Database pool initialized and ready.")
            
            # Initialize restaurant cache (hours, capacity)
            await RestaurantCache.initialize()
            logger.info("Restaurant cache initialized.")
        except Exception as e:
            logger.exception("DB init failed; starting without DB.")
            app.state.db_pool = None

    @app.on_event("shutdown")
    async def on_shutdown():
        """Close database connections on application shutdown."""
        logger.info("Shutting down FastAPI application...")
        await app.state.db_pool.close()
        logger.info("Database pool closed successfully.")

    return app


app = create_app()


def dev_server():
    """Start server in development mode with auto-reload."""
    uvicorn.run(
        "src.app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=True,
        log_level="info",
        timeout_keep_alive=65,
    )


def prod_server():
    """Start server in production mode without auto-reload."""
    uvicorn.run(
        "src.app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=False,
        log_level="info",
        timeout_keep_alive=240,
        timeout_graceful_shutdown=240,
    )


if __name__ == "__main__":
    mode = "development" if app_settings.DEBUG else "production"
    logger.info(f"Running FastAPI in {mode} mode")
    if app_settings.DEBUG:
        dev_server()
    else:
        prod_server()
