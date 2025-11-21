from typing import List, Optional
from pydantic import BaseModel
from src.utils.context import get_or_create_order

class UpdateFormuleItemRequest(BaseModel):
    itemName: str
    quantity: Optional[int] = None
    indications: Optional[str] = None
    new_indications: Optional[str] = None
    action: str = "update"  # "update", "remove", or "replace"

async def update_formule_item(formuleIndex: int, updates: List[UpdateFormuleItemRequest]) -> dict:
    """
    Updates items within a specific formule in the order draft.
    """
    order = get_or_create_order()
    
    if formuleIndex < 0 or formuleIndex >= len(order.formules):
        return {"success": False, "message": "Index de formule invalide."}

    formule = order.formules[formuleIndex] 
    result = {
        "success": True,
        "updates_performed": [],
        "errors": []
    }

    for update in updates:
        found_index = -1
        for i, item in enumerate(formule.items):
            if item.item_name == update.itemName and item.indications == update.indications:
                found_index = i
                break
        
        if found_index == -1:
            result["errors"].append(f"Article '{update.itemName}' non trouvé dans la formule.")
            continue

        item = formule.items[found_index]

        if update.action == "update":
            if update.quantity is not None and update.quantity > 0:
                item.quantity = update.quantity
                result["updates_performed"].append(f"Quantité de '{item.item_name}' mise à jour.")
            else:
                result["errors"].append("Quantité invalide.")

        elif update.action == "remove":
            formule.items.pop(found_index)
            result["updates_performed"].append(f"Article '{item.item_name}' retiré de la formule.")

        elif update.action == "replace":
            if update.new_indications is not None:
                item.indications = update.new_indications
                result["updates_performed"].append(f"Indications de '{item.item_name}' modifiées.")
            else:
                result["errors"].append("Nouvelles indications manquantes.")

    return result
