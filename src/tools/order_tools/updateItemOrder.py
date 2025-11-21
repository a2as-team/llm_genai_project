from typing import List, Optional, Literal
from pydantic import BaseModel
from src.utils.context import get_or_create_order

class UpdateItemRequest(BaseModel):
    itemName: str
    quantity: Optional[int] = None
    indications: Optional[str] = None
    new_indications: Optional[str] = None
    action: Literal["update", "remove", "replace"] = "update"  # "update", "remove", or "replace"

async def update_item_order(updates: List[UpdateItemRequest]) -> dict:
    """
    Updates, removes, or replaces items in the current order draft.

    class UpdateItemRequest(BaseModel):
        itemName: str
        quantity: Optional[int] = None
        indications: Optional[str] = None
        new_indications: Optional[str] = None
        action: Literal["update", "remove", "replace"] = "update"
    """
    order = get_or_create_order()
    result = {
        "success": True,
        "updates_performed": [],
        "errors": []
    }

    for update in updates:
        # Find item by name and indications
        # We iterate backwards to safely remove if needed, or just find first match
        # For simplicity, let's find the first match
        found_index = -1
        for i, item in enumerate(order.items):
            if item.name == update.itemName and item.indications == update.indications:
                found_index = i
                break
        
        if found_index == -1:
            result["errors"].append(f"Article '{update.itemName}' avec indications '{update.indications}' non trouvé.")
            continue

        item = order.items[found_index]

        if update.action == "update":
            if update.quantity is not None and update.quantity > 0:
                item.quantity = update.quantity
                result["updates_performed"].append(f"Quantité de '{item.name}' mise à jour à {item.quantity}.")
            else:
                result["errors"].append(f"Quantité invalide pour '{item.name}'.")

        elif update.action == "remove":
            removed = order.items.pop(found_index)
            result["updates_performed"].append(f"Article '{removed.name}' retiré.")

        elif update.action == "replace":
            if update.new_indications is not None:
                # Check if target variant exists to merge
                existing_variant_index = -1
                for i, existing in enumerate(order.items):
                    if i != found_index and existing.name == item.name and existing.indications == update.new_indications:
                        existing_variant_index = i
                        break
                
                if existing_variant_index != -1:
                    # Merge
                    order.items[existing_variant_index].quantity += item.quantity
                    order.items.pop(found_index)
                    result["updates_performed"].append(f"Article '{item.name}' fusionné avec la variante existante.")
                else:
                    # Update indications
                    item.indications = update.new_indications
                    result["updates_performed"].append(f"Indications de '{item.name}' modifiées en '{update.new_indications}'.")
            else:
                result["errors"].append(f"Nouvelles indications manquantes pour '{item.name}'.")
        
        else:
            result["errors"].append(f"Action inconnue '{update.action}' pour '{item.name}'.")

    return result
