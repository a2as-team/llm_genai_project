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

from src.bdd.dbmanager import DBManager
from src.bdd.schema import Order, Reservation, OrderFormule, OrderItem, MenuItem, RestaurantTable
from src.utils.sse_manager import sse_manager, EventType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Orders & Reservations"], prefix="/data")

db_manager = DBManager()


async def get_db() -> AsyncSession:
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
# CLIENT ROUTES - Simple endpoints for customers
# ============================================================================


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
            selectinload(Order.formules),
            selectinload(Order.items)
        )
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
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
                "tables_count": len(reservation.tables),
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
        
        # Publish SSE event
        await sse_manager.publish_order_event(
            EventType.ORDER_UPDATED,
            {
                "id": str(order.id),
                "customer_name": order.customer_name,
                "is_validated": order.is_validated,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
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
