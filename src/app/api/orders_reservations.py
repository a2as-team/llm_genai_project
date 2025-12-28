"""Orders and Reservations API routes - Client and Admin endpoints."""

import logging
from typing import List, Optional
from uuid import UUID
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, Date, cast, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from pydantic import BaseModel
from typing import AsyncGenerator

from src.bdd.dbmanager import DBManager
from src.bdd.schema import Order, Reservation, OrderFormule, OrderItem, OrderFormuleItem, MenuItem, RestaurantTable
from src.utils.sse_manager import sse_manager, EventType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders & Reservations"], prefix="/data")

db_manager = DBManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with db_manager.SessionLocal() as session:
        yield session


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class OrderUpdateRequest(BaseModel):
    """Request model for updating order fields."""
    is_validated: Optional[bool] = None


class ReservationUpdateRequest(BaseModel):
    """Request model for updating reservation fields."""
    pass


# ============================================================================
# ADMIN ROUTES - Modular endpoints with filters
# ============================================================================


@router.get("/admin/orders", response_model=List[dict])
async def get_orders_admin(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name (case-insensitive)"),
    is_validated: Optional[bool] = Query(None, description="Filter by validation status"),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get orders with optional filters for admin panel.
    
    Query parameters:
    - date: Filter by creation date (YYYY-MM-DD)
    - customer_name: Filter by customer name (case-insensitive, partial match)
    - is_validated: Filter by validation status (true/false)
    - skip: Pagination offset
    - limit: Pagination limit
    """
    try:
        # Build the query dynamically based on filters
        filters = []
        
        # Date filter
        if date:
            try:
                filter_date = datetime.strptime(date, "%Y-%m-%d").date()
                filters.append(cast(Order.created_at, Date) == filter_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Customer name filter (case-insensitive, partial match)
        if customer_name:
            filters.append(func.lower(Order.customer_name).contains(customer_name.lower()))
        
        # Validation status filter
        if is_validated is not None:
            filters.append(Order.is_validated == is_validated)
        
        # Combine all filters with AND
        query = select(Order).options(
            selectinload(Order.formules).selectinload(OrderFormule.items).selectinload(OrderFormuleItem.item),
            selectinload(Order.items).selectinload(OrderItem.item)
        )
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        orders = result.scalars().all()
        
        def calculate_order_total(order: Order) -> float:
            """Calculate total price of an order."""
            total = 0.0
            # Sum formules prices
            for formule in order.formules:
                total += float(formule.formula_base_price) * formule.quantity
            # Sum individual items prices
            for order_item in order.items:
                if order_item.item:
                    total += float(order_item.item.price) * order_item.quantity
            return round(total, 2)
        
        def serialize_order_items(order: Order) -> list:
            """Serialize order items with details."""
            return [
                {
                    "id": str(oi.id),
                    "name": oi.item.name if oi.item else "Unknown",
                    "quantity": oi.quantity,
                    "unit_price": float(oi.item.price) if oi.item else 0,
                    "indications": oi.indications,
                }
                for oi in order.items
            ]
        
        def serialize_order_formules(order: Order) -> list:
            """Serialize order formules with their items."""
            return [
                {
                    "id": str(of.id),
                    "name": of.formule_name,
                    "quantity": of.quantity,
                    "base_price": float(of.formula_base_price),
                    "items": [
                        {
                            "name": ofi.item.name if ofi.item else "Unknown",
                            "indications": ofi.indications,
                        }
                        for ofi in of.items
                    ] if of.items else [],
                }
                for of in order.formules
            ]
        
        return [
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "is_validated": order.is_validated,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "total_price": calculate_order_total(order),
                "formules": serialize_order_formules(order),
                "items": serialize_order_items(order),
            }
            for order in orders
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders with filters: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching orders")


@router.get("/admin/reservations", response_model=List[dict])
async def get_reservations_admin(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name (case-insensitive)"),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get reservations with optional filters for admin panel.
    
    Query parameters:
    - date: Filter by reservation date (YYYY-MM-DD)
    - customer_name: Filter by customer name (case-insensitive, partial match)
    - skip: Pagination offset
    - limit: Pagination limit
    """
    try:
        # Build the query dynamically based on filters
        filters = []
        
        # Date filter (reservation_datetime)
        if date:
            try:
                filter_date = datetime.strptime(date, "%Y-%m-%d").date()
                filters.append(cast(Reservation.reservation_datetime, Date) == filter_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Customer name filter (case-insensitive, partial match)
        if customer_name:
            filters.append(func.lower(Reservation.customer_name).contains(customer_name.lower()))
        
        # Combine all filters with AND
        query = select(Reservation).options(
            selectinload(Reservation.tables)
        )
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
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
                "tables": [
                    {
                        "id": str(table.id),
                        "name": table.name,
                        "capacity": table.capacity,
                        "location": table.location,
                    }
                    for table in reservation.tables
                ],
            }
            for reservation in reservations
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservations with filters: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching reservations")


# ============================================================================
# ADMIN UPDATE ENDPOINTS
# ============================================================================


@router.patch("/admin/orders/{order_id}")
async def update_order(
    order_id: UUID,
    request: OrderUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an order (is_validated).
    
    Publishes an order_updated event via SSE.
    """
    try:
        # Fetch the order
        query = select(Order).where(Order.id == order_id).options(
            selectinload(Order.formules),
            selectinload(Order.items)
        )
        result = await db.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update fields if provided
        if request.is_validated is not None:
            order.is_validated = request.is_validated
        
        # Commit changes
        await db.commit()
        await db.refresh(order)
        
        # Publish SSE event with complete order data (same fields as GET endpoint)
        await sse_manager.publish_order_event(
            EventType.ORDER_UPDATED,
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
        )
        
        return {
            "id": str(order.id),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "is_validated": order.is_validated,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "formules_count": len(order.formules),
            "items_count": len(order.items),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error updating order")


@router.delete("/admin/orders/{order_id}")
async def delete_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an order (hard delete).
    
    Publishes an order_deleted event via SSE.
    """
    try:
        # Fetch the order
        query = select(Order).where(Order.id == order_id)
        result = await db.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Store info before deletion for SSE event
        order_info = {
            "id": str(order.id),
            "customer_name": order.customer_name,
        }
        
        # Delete the order
        await db.delete(order)
        await db.commit()
        
        # Publish SSE event
        await sse_manager.publish_order_event(
            EventType.ORDER_DELETED,
            order_info
        )
        
        return {"message": "Order deleted successfully", "id": str(order_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting order")


@router.delete("/admin/reservations/{reservation_id}")
async def delete_reservation(
    reservation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a reservation (hard delete).
    
    Publishes a reservation_deleted event via SSE.
    """
    try:
        # Fetch the reservation
        query = select(Reservation).where(Reservation.id == reservation_id)
        result = await db.execute(query)
        reservation = result.scalar_one_or_none()
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        # Store info before deletion for SSE event
        reservation_info = {
            "id": str(reservation.id),
            "customer_name": reservation.customer_name,
        }
        
        # Delete the reservation
        await db.delete(reservation)
        await db.commit()
        
        # Publish SSE event
        await sse_manager.publish_reservation_event(
            EventType.RESERVATION_DELETED,
            reservation_info
        )
        
        return {"message": "Reservation deleted successfully", "id": str(reservation_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reservation {reservation_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting reservation")


# ============================================================================
# SSE ENDPOINTS - REAL-TIME UPDATES
# ============================================================================


@router.get("/admin/orders/stream")
async def orders_stream():
    """
    SSE endpoint for real-time order updates.
    
    Clients should connect to this endpoint and listen for events:
    - order_created: New order created
    - order_updated: Order updated
    - order_deleted: Order deleted
    """
    async def event_generator():
        queue = await sse_manager.subscribe_orders()
        try:
            # Send initial connection message
            yield "data: {\"message\": \"Connected to orders stream\"}\n\n"
            
            while True:
                # Wait for next event with timeout to detect disconnections
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse_format()
                except asyncio.TimeoutError:
                    # Send keep-alive comment every 30 seconds
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            await sse_manager.unsubscribe_orders(queue)
            logger.info("Orders stream client disconnected")
        except Exception as e:
            logger.error(f"Error in orders stream: {e}")
            await sse_manager.unsubscribe_orders(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@router.get("/admin/reservations/stream")
async def reservations_stream():
    """
    SSE endpoint for real-time reservation updates.
    
    Clients should connect to this endpoint and listen for events:
    - reservation_created: New reservation created
    - reservation_updated: Reservation updated
    - reservation_deleted: Reservation deleted
    """
    async def event_generator():
        queue = await sse_manager.subscribe_reservations()
        try:
            # Send initial connection message
            yield "data: {\"message\": \"Connected to reservations stream\"}\n\n"
            
            while True:
                # Wait for next event with timeout to detect disconnections
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse_format()
                except asyncio.TimeoutError:
                    # Send keep-alive comment every 30 seconds
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            await sse_manager.unsubscribe_reservations(queue)
            logger.info("Reservations stream client disconnected")
        except Exception as e:
            logger.error(f"Error in reservations stream: {e}")
            await sse_manager.unsubscribe_reservations(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
