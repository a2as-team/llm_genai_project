from typing import Optional, Literal
from pydantic import BaseModel
from src.utils.context import get_or_create_order
from src.tools.order_tools.addItemToOrder import AddItemRequest

class UpdateItemRequest(BaseModel):
    # Pour identifier l'item dans la commande (DOIT correspondre exactement à ce qui est dans la commande)
    itemName: str
    
    # Pour les modifications
    newQuantity: Optional[int] = None
    newIndications: Optional[str] = None
    newItem: Optional[AddItemRequest] = None  # Pour action "replace"
    
    action: Literal["update", "delete", "replace"] = "update"

async def update_item_order(update: UpdateItemRequest) -> dict:
    """
    Updates, deletes, or replaces a single item in the current order draft.
    
    IMPORTANT: itemName doit correspondre EXACTEMENT à ce qui est présent dans la commande actuelle.
    
    Parameters:
    - update: UpdateItemRequest
    
    class UpdateItemRequest(BaseModel):
        # Identification de l'item (EXACTEMENT comme dans la commande actuelle)
        itemName: str                          # Nom exact de l'item à modifier
        
        # Modifications à appliquer
        newQuantity: Optional[int] = None      # Nouvelle quantité (pour action "update")
        newIndications: Optional[str] = None   # Nouvelles indications (pour action "update")
        newItem: Optional[AddItemRequest] = None  # Nouvel item complet (pour action "replace")
        
        action: Literal["update", "delete", "replace"] = "update"
        
    Actions:
    - "update": Modifie quantity et/ou indications de l'item existant
    - "delete": Supprime l'item de la commande
    - "replace": Remplace l'item par newItem (un AddItemRequest complet)
    
    class AddItemRequest(BaseModel):
        itemName: str
        quantity: int = 1
        indications: Optional[str] = None
    """
    try:
        order = get_or_create_order()
        
        # Gestion défensive (dict vs objet)
        req = update if isinstance(update, UpdateItemRequest) else UpdateItemRequest(**update)
        
        # Trouver l'item par nom ET indications exactes
        found_index = -1
        for i, item in enumerate(order.items):
            if item.name == req.itemName :
                found_index = i
                break
        
        if found_index == -1:
            return {
                "success": False,
                "message": f"Article '{req.itemName}' non trouvé dans la commande.",
                "current_items": [i.model_dump() for i in order.items]
            }

        item = order.items[found_index]

        # ACTION: DELETE
        if req.action == "delete":
            removed = order.items.pop(found_index)
            return {
                "success": True,
                "message": f"Article '{removed.name}' supprimé du panier.",
                "current_items": [i.model_dump() for i in order.items]
            }

        # ACTION: UPDATE
        elif req.action == "update":
            changes = []
            
            if req.newQuantity is not None:
                if req.newQuantity > 0:
                    item.quantity = req.newQuantity
                    changes.append(f"quantité → {req.newQuantity}")
                else:
                    return {
                        "success": False,
                        "message": f"Quantité invalide ({req.newQuantity}). Utilisez action 'delete' pour supprimer.",
                        "current_items": [i.model_dump() for i in order.items]
                    }
            
            if req.newIndications is not None:
                item.indications = req.newIndications
                changes.append(f"indications → '{req.newIndications}'")
            
            if not changes:
                return {
                    "success": False,
                    "message": "Aucune modification spécifiée (newQuantity ou newIndications requis).",
                    "current_items": [i.model_dump() for i in order.items]
                }
            
            return {
                "success": True,
                "message": f"Article '{item.name}' mis à jour: {', '.join(changes)}.",
                "current_items": [i.model_dump() for i in order.items]
            }

        # ACTION: REPLACE
        elif req.action == "replace":
            if req.newItem is None:
                return {
                    "success": False,
                    "message": "newItem requis pour l'action 'replace'.",
                    "current_items": [i.model_dump() for i in order.items]
                }
            
            # Gestion défensive pour newItem
            new_item_req = req.newItem if isinstance(req.newItem, AddItemRequest) else AddItemRequest(**req.newItem)
            
            # Remplacer l'item
            item.name = new_item_req.itemName
            item.quantity = new_item_req.quantity
            item.indications = new_item_req.indications
            
            return {
                "success": True,
                "message": f"Article remplacé par '{new_item_req.itemName}' (qty: {new_item_req.quantity}).",
                "current_items": [i.model_dump() for i in order.items]
            }
        
        return {
            "success": False,
            "message": f"Action inconnue '{req.action}'.",
            "current_items": [i.model_dump() for i in order.items]
        }
    except Exception as e:
        print(f"[update_item_order] Exception: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification de l'article: {str(e)}",
            "current_items": []
        }
