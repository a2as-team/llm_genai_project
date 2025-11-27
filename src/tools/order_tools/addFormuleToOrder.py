from typing import List, Optional
from pydantic import BaseModel
from src.utils.context import get_or_create_order
from src.models.order_draft import DraftOrderFormule, DraftFormuleItem
from src.tools.order_tools.addItemToOrder import AddItemRequest

class AddFormuleRequest(BaseModel):
    formuleName: str
    items: List[AddItemRequest]
    quantity: int = 1

async def add_formule_to_order(formule: AddFormuleRequest) -> dict:
    """
    Adds a single formule to the current order draft.
    
    Parameters:
    - formule: AddFormuleRequest - The formule to add.
    
    class AddFormuleRequest(BaseModel):
        formuleName: str                    # Nom de la formule (ex: "Menu Midi")
        items: List[AddItemRequest]         # Liste des items composant la formule
        quantity: int = 1                   # Nombre de fois à ajouter cette formule
    
    class AddItemRequest(BaseModel):
        itemName: str                       # Nom de l'item dans la formule
        quantity: int = 1
        indications: Optional[str] = None   # Indications spécifiques (ex: "sans oignons")
    """
    try:
        order = get_or_create_order()
        
        # Gestion défensive (dict vs objet)
        req = formule if isinstance(formule, AddFormuleRequest) else AddFormuleRequest(**formule)
        
        # Normaliser les items (dict vs objet)
        normalized_items = []
        for item in req.items:
            item_req = item if isinstance(item, AddItemRequest) else AddItemRequest(**item)
            normalized_items.append(item_req)
        
        added_count = 0
        
        # Add the formule n times (quantity)
        for _ in range(req.quantity):
            # Deep copy items pour chaque formule
            draft_items = [
                DraftFormuleItem(
                    item_name=item.itemName,
                    quantity=item.quantity,
                    indications=item.indications
                ) for item in normalized_items
            ]
            
            new_formule = DraftOrderFormule(
                name=req.formuleName,
                items=draft_items
            )
            
            order.formules.append(new_formule)
            added_count += 1
        print(order.model_dump())
        return {
            "success": True,
            "message": f"{added_count} formule(s) '{req.formuleName}' ajoutée(s) au panier.",
            "current_formules": [f.model_dump() for f in order.formules]
        }
    except Exception as e:
        print(f"[add_formule_to_order] Exception: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de l'ajout de la formule: {str(e)}",
            "current_formules": []
        }
