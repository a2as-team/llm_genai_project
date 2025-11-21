from typing import List, Optional
from pydantic import BaseModel
from src.utils.context import get_or_create_order, get_current_order
from src.models.order_draft import DraftOrderItem

class AddItemRequest(BaseModel):
    itemName: str
    quantity: int = 1
    indications: Optional[str] = None

async def add_item_to_order(item: AddItemRequest) -> dict:
    """
    Adds a single item to the current order draft.
    
    Parameters:
    - item: AddItemRequest - The item to add.

    class AddItemRequest(BaseModel):
        itemName: str
        quantity: int = 1
        indications: Optional[str] = None
    """
    # Récupération de la commande (supposons que c'est synchrone ici selon ton code)
    order = get_or_create_order()
    
    # Gestion défensive (dict vs objet)
    item_req = item if isinstance(item, AddItemRequest) else AddItemRequest(**item)

    # Recherche d'un article existant (Même nom ET mêmes indications)
    # On utilise item_req.itemName pour mapper vers DraftOrderItem.name
    existing = next(
        (i for i in order.items if i.name == item_req.itemName and i.indications == item_req.indications), 
        None
    )

    if existing:
        # On incrémente seulement si ça existe déjà
        existing.quantity += item_req.quantity
    else:
        # Sinon on crée la nouvelle ligne
        new_item = DraftOrderItem(
            name=item_req.itemName, 
            quantity=item_req.quantity, 
            indications=item_req.indications
        )
        order.items.append(new_item)
        
    return {
        "success": True, 
        "message": f"{item_req.quantity} article(s) ajouté(s) au panier.", 
        "current_items": [i.model_dump() for i in order.items]
    }