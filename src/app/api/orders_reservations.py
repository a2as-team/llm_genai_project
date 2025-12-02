"""Orders and Reservations API routes.

Provides endpoints to retrieve orders and reservations data from the database.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.bdd.dbmanager import DBManager
from src.bdd.schema import Order, Reservation, OrderFormule, OrderItem, OrderFormuleItem, MenuItem, RestaurantTable

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders & Reservations"], prefix="/data")

db_manager = DBManager()


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with db_manager.SessionLocal() as session:
        yield session


# ============================================================================
# ORDERS ENDPOINTS
# ============================================================================


@router.get("/orders", response_model=List[dict])
async def get_all_orders(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Get all orders with pagination."""
    try:
        query = select(Order).options(
            selectinload(Order.formules),
            selectinload(Order.items)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        orders = result.scalars().all()

        return [
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "is_validated": order.is_validated,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "formules_count": len(order.formules),
                "items_count": len(order.items),
            }
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching orders")


# ⚠️ IMPORTANT: These specific routes MUST come before /{order_id}
# Otherwise /validated, /pending, /customer/{name} will be interpreted as order IDs

@router.get("/orders/validated", response_model=List[dict])
async def get_validated_orders(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Get all validated orders."""
    try:
        query = select(Order).where(Order.is_validated == True).options(
            selectinload(Order.formules),
            selectinload(Order.items)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        orders = result.scalars().all()

        return [
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "is_validated": order.is_validated,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "formules_count": len(order.formules),
                "items_count": len(order.items),
            }
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error fetching validated orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching validated orders")


@router.get("/orders/pending", response_model=List[dict])
async def get_pending_orders(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Get all pending (not validated) orders."""
    try:
        query = select(Order).where(Order.is_validated == False).options(
            selectinload(Order.formules),
            selectinload(Order.items)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        orders = result.scalars().all()

        return [
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "is_validated": order.is_validated,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "formules_count": len(order.formules),
                "items_count": len(order.items),
            }
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error fetching pending orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching pending orders")


@router.get("/orders/customer/{customer_name}", response_model=List[dict])
async def get_orders_by_customer(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """Get all orders for a specific customer by name (case-insensitive)."""
    try:
        # Use LOWER for case-insensitive search
        query = select(Order).where(
            func.lower(Order.customer_name) == customer_name.lower()
        ).options(
            selectinload(Order.formules),
            selectinload(Order.items)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        orders = result.scalars().all()

        return [
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "is_validated": order.is_validated,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "formules_count": len(order.formules),
                "items_count": len(order.items),
            }
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error fetching orders for customer {customer_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching customer orders")


# Generic {order_id} route MUST come LAST
@router.get("/orders/{order_id}", response_model=dict)
async def get_order_details(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific order."""
    try:
        # Load order with all related formules and items
        query = select(Order).where(Order.id == order_id).options(
            selectinload(Order.formules).selectinload(OrderFormule.items).selectinload(OrderFormuleItem.item),
            selectinload(Order.items).selectinload(OrderItem.item)
        )
        result = await db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Build formules data
        formules = []
        for formule in order.formules:
            formule_items = []
            for item in formule.items:
                formule_items.append({
                    "id": str(item.id),
                    "item_id": str(item.item_id),
                    "item_name": item.item.name if item.item else None,
                    "indications": item.indications,
                })

            formules.append({
                "id": str(formule.id),
                "formule_name": formule.formule_name,
                "formula_base_price": float(formule.formula_base_price),
                "quantity": formule.quantity,
                "created_at": formule.created_at.isoformat() if formule.created_at else None,
                "items": formule_items,
            })

        # Build items data
        items = []
        for item in order.items:
            items.append({
                "id": str(item.id),
                "item_id": str(item.item_id),
                "item_name": item.item.name if item.item else None,
                "quantity": item.quantity,
                "price": float(item.item.price) if item.item else None,
                "indications": item.indications,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            })

        return {
            "id": str(order.id),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "is_validated": order.is_validated,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "formules": formules,
            "items": items,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching order")


# ============================================================================
# RESERVATIONS ENDPOINTS
# ============================================================================


@router.get("/reservations", response_model=List[dict])
async def get_all_reservations(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Get all reservations with pagination."""
    try:
        query = select(Reservation).options(
            selectinload(Reservation.tables)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        reservations = result.scalars().all()

        return [
            {
                "id": str(reservation.id),
                "customer_name": reservation.customer_name,
                "customer_phone": reservation.customer_phone,
                "reservation_datetime": reservation.reservation_datetime.isoformat() if reservation.reservation_datetime else None,
                "number_of_guests": reservation.number_of_guests,
                "extra_infos": reservation.extra_infos,
                "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
                "updated_at": reservation.updated_at.isoformat() if reservation.updated_at else None,
                "tables_count": len(reservation.tables),
            }
            for reservation in reservations
        ]
    except Exception as e:
        logger.error(f"Error fetching reservations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching reservations")


# ⚠️ IMPORTANT: These specific routes MUST come before /{reservation_id}

@router.get("/reservations/upcoming", response_model=List[dict])
async def get_upcoming_reservations(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """Get all upcoming reservations (from now onwards)."""
    try:
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        query = select(Reservation).where(
            Reservation.reservation_datetime >= now
        ).options(
            selectinload(Reservation.tables)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        reservations = result.scalars().all()

        return [
            {
                "id": str(reservation.id),
                "customer_name": reservation.customer_name,
                "customer_phone": reservation.customer_phone,
                "reservation_datetime": reservation.reservation_datetime.isoformat() if reservation.reservation_datetime else None,
                "number_of_guests": reservation.number_of_guests,
                "extra_infos": reservation.extra_infos,
                "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
                "updated_at": reservation.updated_at.isoformat() if reservation.updated_at else None,
                "tables_count": len(reservation.tables),
            }
            for reservation in reservations
        ]
    except Exception as e:
        logger.error(f"Error fetching upcoming reservations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching upcoming reservations")


@router.get("/reservations/customer/{customer_name}", response_model=List[dict])
async def get_reservations_by_customer(
    customer_name: str,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """Get all reservations for a specific customer by name (case-insensitive)."""
    try:
        # Use LOWER for case-insensitive search
        query = select(Reservation).where(
            func.lower(Reservation.customer_name) == customer_name.lower()
        ).options(
            selectinload(Reservation.tables)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        reservations = result.scalars().all()

        return [
            {
                "id": str(reservation.id),
                "customer_name": reservation.customer_name,
                "customer_phone": reservation.customer_phone,
                "reservation_datetime": reservation.reservation_datetime.isoformat() if reservation.reservation_datetime else None,
                "number_of_guests": reservation.number_of_guests,
                "extra_infos": reservation.extra_infos,
                "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
                "updated_at": reservation.updated_at.isoformat() if reservation.updated_at else None,
                "tables_count": len(reservation.tables),
            }
            for reservation in reservations
        ]
    except Exception as e:
        logger.error(f"Error fetching reservations for customer {customer_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching customer reservations")


@router.get("/reservations/date/{date}", response_model=List[dict])
async def get_reservations_by_date(
    date: str,  # Format: YYYY-MM-DD
    db: AsyncSession = Depends(get_db),
):
    """Get all reservations for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
    """
    try:
        from datetime import datetime
        from sqlalchemy import cast, Date
        
        # Parse the date string
        reservation_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Query reservations on that date - cast TIMESTAMP to DATE for comparison
        query = select(Reservation).where(
            cast(Reservation.reservation_datetime, Date) == reservation_date
        ).options(
            selectinload(Reservation.tables)
        )
        result = await db.execute(query)
        reservations = result.scalars().all()

        return [
            {
                "id": str(reservation.id),
                "customer_name": reservation.customer_name,
                "customer_phone": reservation.customer_phone,
                "reservation_datetime": reservation.reservation_datetime.isoformat() if reservation.reservation_datetime else None,
                "number_of_guests": reservation.number_of_guests,
                "extra_infos": reservation.extra_infos,
                "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
                "updated_at": reservation.updated_at.isoformat() if reservation.updated_at else None,
                "tables_count": len(reservation.tables),
            }
            for reservation in reservations
        ]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error fetching reservations for date {date}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching reservations by date")


# Generic {reservation_id} route MUST come LAST
@router.get("/reservations/{reservation_id}", response_model=dict)
async def get_reservation_details(
    reservation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific reservation."""
    try:
        # Load reservation with all related data
        query = select(Reservation).where(Reservation.id == reservation_id).options(
            selectinload(Reservation.tables)
        )
        result = await db.execute(query)
        reservation = result.scalar_one_or_none()

        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        # Build tables data
        tables = []
        for table in reservation.tables:
            tables.append({
                "id": str(table.id),
                "name": table.name,
                "capacity": table.capacity,
                "location": table.location,
            })

        return {
            "id": str(reservation.id),
            "customer_name": reservation.customer_name,
            "customer_phone": reservation.customer_phone,
            "reservation_datetime": reservation.reservation_datetime.isoformat() if reservation.reservation_datetime else None,
            "number_of_guests": reservation.number_of_guests,
            "extra_infos": reservation.extra_infos,
            "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
            "updated_at": reservation.updated_at.isoformat() if reservation.updated_at else None,
            "tables": tables,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservation {reservation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching reservation")
