from src.utils.context import get_or_create_order

async def remove_formule(formuleIndex: int) -> dict:
    """
    Removes a formule from the current order draft by index.
    """
    order = get_or_create_order()
    
    if formuleIndex < 0 or formuleIndex >= len(order.formules):
        return {
            "success": False,
            "message": f"Index de formule invalide {formuleIndex}. Il y a {len(order.formules)} formules."
        }

    removed = order.formules.pop(formuleIndex)
    
    return {
        "success": True,
        "message": f"Formule '{removed.name}' retirée du panier.",
        "remaining_formules_count": len(order.formules)
    }
