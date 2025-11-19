"""
Database connection pool management.

Handles creation and lifecycle of async PostgreSQL connection pools
using asyncpg and configuration from DatabaseSettings.
"""

import logging
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool

from src.config import database_settings

logger = logging.getLogger(__name__)


async def create_db_pool(min_size: int = 1, max_size: int = 10) -> Pool:
    """
    Create async PostgreSQL connection pool.

    Initializes connection pool with min/max size constraints from
    DatabaseSettings configuration.

    Args:
        min_size: Minimum connections in pool (default: 1)
        max_size: Maximum connections in pool (default: 10)

    Returns:
        Initialized asyncpg connection pool

    Raises:
        RuntimeError: If connection to database fails
    """
    try:
        pool: Pool = await asyncpg.create_pool(
            dsn=database_settings.dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
        )
        logger.info(f"✅ Database pool created: {min_size}-{max_size} connections")
        return pool

    except Exception as e:
        logger.exception("❌ Failed to create database pool")
        raise RuntimeError(f"Could not connect to database: {e}") from e


@asynccontextmanager
async def get_connection(pool: Pool):
    """
    Context manager for acquiring and releasing pool connections.

    Automatically acquires a connection from the pool on entry and
    releases it back on exit, even if an exception occurs.

    Args:
        pool: Connection pool from create_db_pool()

    Yields:
        asyncpg connection object

    Example:
        async with get_connection(app.state.db_pool) as conn:
            rows = await conn.fetch("SELECT * FROM users")
    """
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

