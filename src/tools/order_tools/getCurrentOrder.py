from src.utils.context import get_current_order

async def get_current_order_tool() -> dict:
    """
    Retrieves the current order draft.
    """
    order = get_current_order()
    if not order:
        return {"message": "Aucune commande en cours."}
    
    return {
        "order": order.model_dump(),
        "message": "Voici le contenu actuel de la commande."
    }
