from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from uuid import UUID
from datetime import datetime, time

class Table(BaseModel):
    id: UUID
    name: str
    capacity: int
    location: Literal["indoor", "outdoor"]
    combinable_with: List[UUID] = Field(default_factory=list)

class Reservation(BaseModel):
    reservationId: UUID
    customerName: str
    reservationDatetime: datetime 
    numberOfGuests: int
    tableIds: List[UUID] = Field(default_factory=list)
    extraInfos: Optional[str] = None

class ServicePeriod(BaseModel):
    name: Literal["lunch", "dinner"]
    openingHour: time
    closingHour: time

class RestaurantSettings(BaseModel):
    servicePeriods: List[ServicePeriod] = Field(default_factory=list)
    averageDurationMinutes: int = 120
    bufferTimeMinutes: int = 15

class GetTableAvailabilityRequest(BaseModel):
    reservationDatetime: datetime
    numberOfPeople: int = Field(..., gt=0)
    location: Optional[Literal["indoor", "outdoor"]] = None

