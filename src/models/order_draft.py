from typing import List, Optional
from pydantic import BaseModel, Field

class DraftOrderItem(BaseModel):
    """Represents a single item in the cart (e.g., 1 Pizza Margherita)."""
    name: str
    quantity: int = 1
    indications: Optional[str] = None # e.g., "Sans oignons"

class DraftFormuleItem(BaseModel):
    """Represents an item chosen within a formula."""
    item_name: str
    quantity: int = 1
    indications: Optional[str] = None

class DraftOrderFormule(BaseModel):
    """Represents a selected formula (e.g., Menu Duo)."""
    name: str 
    items: List[DraftFormuleItem] = Field(default_factory=list)

class DraftOrder(BaseModel):
    """
    The in-memory representation of the order being built.
    This is what the LLM manipulates indirectly via tools.
    """
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    
    items: List[DraftOrderItem] = Field(default_factory=list)
    formules: List[DraftOrderFormule] = Field(default_factory=list)

    error_message:str | None = None

    def total_item_count(self) -> int:
        return sum(item.quantity for item in self.items) + len(self.formules)
