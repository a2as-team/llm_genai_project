from src.utils.context import get_or_create_order

async def remove_formule(formuleIndex: int) -> dict:
    """
    Supprime une formule de la commande par son index.
    
    Pour modifier une formule: supprimez-la avec ce tool puis recréez-la avec add_formule_to_order.
    
    Parameters:
    - formuleIndex: int - Index de la formule à supprimer (0 = première formule)
    
    Utilisez get_current_order pour voir les formules actuelles et leurs index.
    """
    try:
        order = get_or_create_order()
        
        if formuleIndex < 0 or formuleIndex >= len(order.formules):
            return {
                "success": False,
                "message": f"Index de formule invalide ({formuleIndex}). Il y a {len(order.formules)} formule(s).",
                "current_formules": [f.model_dump() for f in order.formules]
            }

        removed = order.formules.pop(formuleIndex)
        
        return {
            "success": True,
            "message": f"Formule '{removed.name}' supprimée du panier.",
            "current_formules": [f.model_dump() for f in order.formules]
        }
    except Exception as e:
        print(f"[remove_formule] Exception: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la suppression de la formule: {str(e)}",
            "current_formules": []
        }
