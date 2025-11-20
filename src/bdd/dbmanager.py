"""Asynchronous database manager for backend operations.

Handles all database operations using SQLAlchemy async engine with PostgreSQL.
Manages initialization, CRUD operations for documents, chapters, and deep courses.

Some functions are created but not yet used in the codebase.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import uuid4
import json
from google.adk.sessions import DatabaseSessionService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.config import database_settings
from src.bdd.query import *
from src.bdd.schema import Base
from src.models.order import Order

# Database URL configuration
DATABASE_URL_SYNC = database_settings.dsn

# Convert sync DSN to async DSN
if "+asyncpg" not in DATABASE_URL_SYNC:
    if "+psycopg2" in DATABASE_URL_SYNC:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace("+psycopg2", "+asyncpg")
    else:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
else:
    DATABASE_URL_ASYNC = DATABASE_URL_SYNC

print("🧩 Async DSN:", DATABASE_URL_ASYNC)


class DBManager:
    """
    Asynchronous database manager.

    Handles all database operations with async/await pattern.
    Uses ADK's sync engine for initial schema creation, then manages
    all backend operations through an async SQLAlchemy engine.
    """

    def __init__(self):
        """Initialize async engine and session factory."""
        # Async engine for all backend operations
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("⚙️  Async engine initialized (backend).")

    # -----------------------------------------------------
    # CRÉATION COMPLÈTE DE LA BASE VIA ADK
    # -----------------------------------------------------
    async def create_db(self):
        """
        Initialize complete database.

        - Uses ADK (sync) to create its core tables (sessions, events, states)
        - Creates business logic tables on the same engine
        - Recreates async engine for backend
        """
        print("🚀 Complete database initialization via ADK...")

        # 1. Launch ADK (sync) → creates its own tables
        adk_service = DatabaseSessionService(db_url=DATABASE_URL_SYNC)
        adk_engine = adk_service.db_engine

        # 2. Create business logic tables on ADK engine
        Base.metadata.create_all(bind=adk_engine)
        print("✅ ADK + business logic tables created (via ADK sync engine).")

        # 3. Recreate async engine for backend
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("🔄 Async engine restored for backend.")

    async def get_db(self):
        """Context manager for async database session."""
        async with self.SessionLocal() as session:
            yield session

    async def clear_tables(self):
        """Clear all tables without dropping them."""
        async with self.engine.begin() as conn:
            await conn.execute(CLEAR_ALL_TABLES)
        print("🧹 Tables cleared.")

    async def clear_db(self):
        """Drop all tables (ADK + business logic)."""
        async with self.engine.begin() as conn:
            await conn.execute(DROP_ALL_TABLES)
        print("💣 All tables dropped.")

    async def test_db(self):
        """Test database connection and list existing tables."""
        async with self.engine.begin() as conn:
            result = await conn.execute(CHECK_TABLES)
            tables = [row[0] for row in result.fetchall()]
        print("📋 Existing tables:", tables)
        return tables
    
    async def populate_initial_data(self):
        """Populate initial data into the database."""
        async with self.engine.begin() as conn:
            await conn.execute(ENABLE_PGCRYPTO)
            await conn.execute(POPULATE_TABLES)
            await conn.execute(POPULATE_FORMULES)
            await conn.execute(POPULATE_MENU_ITEMS)
            await conn.execute(POPULATE_RESTAURANT_SETTINGS)
            await conn.execute(POPULATE_RESTAURANT_INFOS)
        print("🌱 Initial data populated.")

# -----------------------------------------------------

    async def get_menu(self):
        """Retrieve the menu from the database."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_MENU)
            menu_items = result.fetchall()
        print("📋 Menu retrieved:", menu_items)
        return menu_items
    
    async def get_informations(self):
        """Retrieve the informations of the restaurant from the database."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_INFORMATIONS)
            informations = result.fetchall()
        print("📋 Informations retrieved:", informations)
        return informations
    
    # async def save_order(self, order: Order):
    #     """Save an order to the database."""
    #     async with self.engine.begin() as conn:
    #         await conn.execute(SAVE_ORDER, {
    #             'order_id': str(order.orderId),
    #             'customer_name': order.customerName,
    #             'formules': json.dumps([formule.dict() for formule in order.formules]),
    #             'items': json.dumps([item.dict() for item in order.items]),
    #             'is_validated': order.isValidated
    #         })
    #     print(f"💾 Order {order.orderId} saved.")

