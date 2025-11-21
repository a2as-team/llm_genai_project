from typing import List, Optional
from pydantic import BaseModel, Field
from src.utils.context import get_or_create_order
from src.models.order_draft import DraftOrderFormule, DraftFormuleItem

class FormuleItemRequest(BaseModel):
    itemName: str
    quantity: int = 1
    indications: Optional[str] = None

class AddFormuleRequest(BaseModel):
    formuleName: str
    items: List[FormuleItemRequest]
    quantity: int = 1

async def add_formule_to_order(formules: List[AddFormuleRequest]) -> dict:
    """
    Adds one or multiple formules to the current order draft.
    """
    order = get_or_create_order()
    added_count = 0

    for formule_req in formules:
        # Convert request items to DraftFormuleItem
        draft_items = [
            DraftFormuleItem(
                item_name=item.itemName,
                quantity=item.quantity,
                indications=item.indications
            ) for item in formule_req.items
        ]

        # Add the formule n times
        for _ in range(formule_req.quantity):
            new_formule = DraftOrderFormule(
                name=formule_req.formuleName,
                items=draft_items # Note: shared reference if we don't copy, but for now it's fine as they are immutable-ish
            )
            # Deep copy items to avoid shared reference issues if modified later
            new_formule.items = [
                DraftFormuleItem(
                    item_name=item.itemName,
                    quantity=item.quantity,
                    indications=item.indications
                ) for item in formule_req.items
            ]
            
            order.formules.append(new_formule)
            added_count += 1

    return {
        "success": True,
        "message": f"{added_count} formules ajoutées au panier.",
        "current_formules": [f.model_dump() for f in order.formules]
    }
