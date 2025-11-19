from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Literal


# -----------------------------
# Menu Items (static menu)
# -----------------------------
class MenuItem(BaseModel):
    id: UUID
    name: str
    price: float
    description: Optional[str] = None
    type: Literal["entrée", "plat", "dessert", "boisson"]
    vegetarian: bool 


# -----------------------------
# Order Items (items inside an order)
# -----------------------------
class OrderItem(BaseModel):
    id: UUID
    itemId: UUID        # FK → MenuItem
    name: str
    quantity: int = 1
    price: float
    indications: Optional[str] = None


# -----------------------------
# Formule (menu)
# -----------------------------
class Formule(BaseModel):
    id: UUID
    name: str
    price: float
    description: str
    items: List[MenuItem] = Field(default_factory=list)


# -----------------------------
# OrderFormule (instance in order)
# -----------------------------
class OrderFormule(BaseModel):
    id: UUID                    # PK côté commande
    formuleId: UUID            # FK → Formule
    formuleName: str
    formulaBasePrice: float
    quantity: int = 1
    items: List[OrderItem] = Field(default_factory=list)


# -----------------------------
# Order
# -----------------------------
class Order(BaseModel):
    orderId: UUID
    customerName: Optional[str] = None
    formules: List[OrderFormule] = Field(default_factory=list)
    items: List[OrderItem] = Field(default_factory=list)
    isValidated: bool = False

