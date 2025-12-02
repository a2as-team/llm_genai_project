"""
Centralized request context management.

Uses ContextVar for thread-safe and async-safe request data isolation.
Enables access to request-scoped variables across the application without
passing them through function parameters.
It is used especially to pass vars to tools used by the agents.
"""

from contextvars import ContextVar
from typing import Optional
from src.models.order_draft import DraftOrder

# Request context variables
_session_id_context: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
_user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

# The Order Draft Context
# Default is None, meaning no order is currently in progress for this request context
_current_order_context: ContextVar[Optional[DraftOrder]] = ContextVar('current_order', default=None)


# ===== SETTERS =====

def set_session_id(session_id: str) -> None:
    """Set session_id in request context."""
    _session_id_context.set(session_id)


def set_user_id(user_id: str) -> None:
    """Set user_id in request context."""
    _user_id_context.set(user_id)

def set_current_order(order: DraftOrder) -> None:
    """Set the current order draft in context."""
    _current_order_context.set(order)

def init_order() -> DraftOrder:
    """Initialize a new empty order in the context."""
    new_order = DraftOrder()
    _current_order_context.set(new_order)
    print(f"Initialized new order in context.\n{new_order}")
    return new_order

def set_request_context(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Set basic request context variables.
    """
    if session_id:
        set_session_id(session_id)
    if user_id:
        set_user_id(user_id)


# ===== GETTERS =====

def get_session_id() -> Optional[str]:
    """Get session_id from request context."""
    return _session_id_context.get()


def get_user_id() -> Optional[str]:
    """Get user_id from request context."""
    return _user_id_context.get()

def get_current_order() -> Optional[DraftOrder]:
    """
    Get the current order draft from context.
    Returns None if no order has been initialized.
    """
    return _current_order_context.get()

def get_or_create_order() -> DraftOrder:
    """
    Get the current order, or create a new one if it doesn't exist.
    Useful for tools that need to ensure an order exists.
    """
    order = _current_order_context.get()
    if order is None:
        return init_order()
    return order

# ===== CLEANUP =====

def clear_request_context() -> None:
    """
    Clear all request context variables.
    """
    _session_id_context.set(None)
    _user_id_context.set(None)
    _current_order_context.set(None)
