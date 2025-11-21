from src.utils.context import get_current_order, clear_request_context
from src.bdd.dbmanager import DBManager
from logging import getLogger

logger = getLogger(__name__)

async def validate_order(customerName: str, customerPhone: str = "") -> dict:
    """
    Validates the current order draft and persists it to the database.
    """
    try:
        draft_order = get_current_order()
        if not draft_order:
            return {"success": False, "message": "Aucune commande à valider."}

        if not draft_order.items and not draft_order.formules:
            return {"success": False, "message": "Le panier est vide."}

        db_manager = DBManager()
        
        await db_manager.save_full_order(draft_order, customerName, customerPhone)

        return {
            "success": True, 
            "message": "Commande validée avec succès!",
        }

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return {"success": False, "message": f"Erreur de validation: {str(e)}"}
    except Exception as e:
        logger.error(f"Technical error during validation: {e}")
        return {"success": False, "message": f"Erreur technique lors de la validation: {str(e)}"}
