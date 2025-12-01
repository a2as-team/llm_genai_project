"""
Pydantic models for booking/reservation management.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class BookingRequest(BaseModel):
    """Input model for a booking request from the agent."""
    reservation_datetime: str = Field(
        ..., 
        description="Date et heure de la réservation au format ISO 8601 ou format lisible. "
                    "Exemples: '2025-12-15T20:00:00', '2025-12-15 20:00', '15/12/2025 20h00'"
    )
    number_of_guests: int = Field(..., ge=1, description="Nombre de personnes")
    location: str = Field(..., pattern="^(indoor|outdoor)$", description="Emplacement souhaité: indoor ou outdoor")
    customer_name: str = Field(..., min_length=1, description="Nom du client")
    customer_phone: str = Field(..., min_length=1, description="Numéro de téléphone du client")
    extra_infos: Optional[str] = Field(default=None, description="Informations supplémentaires (anniversaire, etc.)")


class TableInfo(BaseModel):
    """Information about a table."""
    id: UUID
    name: str
    capacity: int
    location: str


class AlternativeSlot(BaseModel):
    """An alternative time slot proposal."""
    datetime: datetime
    location: str
    tables: list[TableInfo]
    total_capacity: int


class BookingResponse(BaseModel):
    """Output model returned by the validate_booking tool."""
    success: bool = Field(..., description="True si la réservation a été créée")
    message: str = Field(..., description="Message explicatif pour l'agent")
    reservation_id: Optional[UUID] = Field(default=None, description="ID de la réservation si créée")
    assigned_tables: Optional[list[TableInfo]] = Field(default=None, description="Tables assignées si succès")
    alternatives: Optional[list[AlternativeSlot]] = Field(default=None, description="Alternatives si échec")
