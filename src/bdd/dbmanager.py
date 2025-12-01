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
            result_items = await conn.execute(GET_MENU_ITEMS)
            result_formules = await conn.execute(GET_FORMULE_ITEMS)
            menu_items = result_items.fetchall()
            menu_formules = result_formules.fetchall()
        print("📋 Menu retrieved:", menu_items, menu_formules)
        return menu_items, menu_formules
    
    async def get_informations(self):
        """Retrieve the informations of the restaurant from the database."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_INFORMATIONS)
            informations = result.fetchall()
        print("📋 Informations retrieved:", informations)
        return informations
    
    async def get_item_price(self, name: str) -> Optional[float]:
        """Get price of a menu item by name."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_ITEM_PRICE, {"name": name})
            row = result.fetchone()
            return float(row[0]) if row else None

    async def get_formule_price(self, name: str) -> Optional[float]:
        """Get price of a menu formule by name."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_FORMULE_PRICE, {"name": name})
            row = result.fetchone()
            return float(row[0]) if row else None

    async def save_full_order(self, draft_order, customer_name: str, customer_phone: str) -> str:
        """
        Save a complete order to the database manually generating UUIDs.
        """
        # 1. Générer l'ID de la commande principale
        new_order_id = uuid4()

        async with self.engine.begin() as conn:
            # --- INSERTION COMMANDE ---
            await conn.execute(INSERT_ORDER, {
                "id": new_order_id,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "is_validated": True
            })
            
            # --- INSERTION ITEMS INDIVIDUELS ---
            for item in draft_order.items:
                # Récupération de l'ID du produit (Menu Item)
                res_item = await conn.execute(GET_ITEM_ID_BY_NAME, {"name": item.name})
                item_id_row = res_item.fetchone()
                if not item_id_row:
                    raise ValueError(f"Article inconnu: {item.name}")
                item_db_id = item_id_row[0]

                # Génération ID pour la ligne de commande
                order_item_uuid = uuid4()

                await conn.execute(INSERT_ORDER_ITEM, {
                    "id": order_item_uuid, # <--- Ici
                    "order_id": new_order_id,
                    "item_id": item_db_id,
                    "quantity": item.quantity,
                    "indications": item.indications
                })

            # --- INSERTION FORMULES ---
            for formule in draft_order.formules:
                res_formule = await conn.execute(GET_FORMULE_ID_BY_NAME, {"name": formule.name})
                formule_row = res_formule.fetchone()
                if not formule_row:
                    raise ValueError(f"Formule inconnue: {formule.name}")
                formule_db_id, formule_price = formule_row

                # Génération ID pour la ligne de formule
                order_formule_uuid = uuid4()

                await conn.execute(INSERT_ORDER_FORMULE, {
                    "id": order_formule_uuid, # <--- Ici
                    "order_id": new_order_id,
                    "formule_id": formule_db_id,
                    "formule_name": formule.name,
                    "formula_base_price": formule_price,
                    "quantity": 1
                })

                # --- INSERTION ITEMS DANS LA FORMULE ---
                for f_item in formule.items:
                    res_f_item = await conn.execute(GET_ITEM_ID_BY_NAME, {"name": f_item.item_name})
                    f_item_row = res_f_item.fetchone()
                    if not f_item_row:
                        raise ValueError(f"Article de formule inconnu: {f_item.item_name}")
                    f_item_db_id = f_item_row[0]

                    # Génération ID pour la ligne d'item de formule
                    order_formule_item_uuid = uuid4()

                    await conn.execute(INSERT_ORDER_FORMULE_ITEM, {
                        "id": order_formule_item_uuid, # <--- Ici
                        "order_formule_id": order_formule_uuid, # Lien avec la formule créée juste avant
                        "item_id": f_item_db_id,
                        "indications": f_item.indications
                    })

            return str(new_order_id)

    # -----------------------------------------------------
    # BOOKING / RESERVATION METHODS
    # -----------------------------------------------------

    async def get_all_tables(self) -> list[dict]:
        """Get all tables with their info."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_ALL_TABLES)
            rows = result.fetchall()
        return [{"id": row[0], "name": row[1], "capacity": row[2], "location": row[3]} for row in rows]

    async def get_tables_by_location(self, location: str) -> list[dict]:
        """Get tables filtered by location (indoor/outdoor)."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_TABLES_BY_LOCATION, {"location": location})
            rows = result.fetchall()
        return [{"id": row[0], "name": row[1], "capacity": row[2], "location": row[3]} for row in rows]

    async def get_table_combinations(self) -> list[tuple]:
        """Get all table combination pairs."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_TABLE_COMBINATIONS)
            rows = result.fetchall()
        return [(row[0], row[1]) for row in rows]

    async def get_restaurant_settings(self) -> dict:
        """Get restaurant settings (duration, buffer, time slot)."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_RESTAURANT_SETTINGS)
            row = result.fetchone()
        if row:
            return {
                "average_duration_minutes": row[0],
                "buffer_time_minutes": row[1],
                "reservation_time_slot": row[2]
            }
        # Defaults if not found
        return {"average_duration_minutes": 120, "buffer_time_minutes": 15, "reservation_time_slot": 15}

    async def get_restaurant_hours(self) -> dict:
        """Get restaurant opening hours."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_RESTAURANT_HOURS)
            row = result.fetchone()
        if row:
            return {
                "lunch_open": row[0],
                "lunch_close": row[1],
                "dinner_open": row[2],
                "dinner_close": row[3]
            }
        return {"lunch_open": "11h30", "lunch_close": "14h30", "dinner_open": "18h30", "dinner_close": "23h00"}

    async def get_reservations_for_date(self, target_date: datetime) -> list[dict]:
        """Get all reservations for a specific date with their assigned tables."""
        async with self.engine.begin() as conn:
            result = await conn.execute(GET_RESERVATIONS_FOR_DATE, {"target_date": target_date})
            rows = result.fetchall()
        
        reservations = {}
        for row in rows:
            res_id = row[0]
            if res_id not in reservations:
                reservations[res_id] = {
                    "id": res_id,
                    "reservation_datetime": row[1],
                    "number_of_guests": row[2],
                    "table_ids": []
                }
            reservations[res_id]["table_ids"].append(row[3])
        
        return list(reservations.values())

    async def save_reservation(
        self,
        customer_name: str,
        customer_phone: str,
        reservation_datetime: datetime,
        number_of_guests: int,
        table_ids: list,
        extra_infos: Optional[str] = None
    ) -> str:
        """Save a new reservation with its assigned tables."""
        new_reservation_id = uuid4()

        async with self.engine.begin() as conn:
            await conn.execute(INSERT_RESERVATION, {
                "id": new_reservation_id,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "reservation_datetime": reservation_datetime,
                "number_of_guests": number_of_guests,
                "extra_infos": extra_infos
            })

            for table_id in table_ids:
                await conn.execute(INSERT_RESERVATION_TABLE, {
                    "reservation_id": new_reservation_id,
                    "table_id": table_id
                })

        return str(new_reservation_id)

