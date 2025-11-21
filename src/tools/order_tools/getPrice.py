from src.utils.context import get_current_order
from src.bdd.dbmanager import DBManager
from logging import getLogger

logger = getLogger(__name__)

async def get_price() -> dict:
    """
    Calculates the estimated total price of the current order draft.
    Fetches prices from the database based on item/formule names.
    """
    try:
        order = get_current_order()
        if not order:
            return {"total_price": 0.0, "message": "Panier vide."}

        db_manager = DBManager()
        total_price = 0.0
        details = []

        # 1. Calculate Items Price
        for item in order.items:
            price = await db_manager.get_item_price(item.name)
            
            if price is not None:
                item_total = price * item.quantity
                total_price += item_total
                details.append(f"{item.quantity}x {item.name}: {item_total:.2f}€")
            else:
                details.append(f"{item.quantity}x {item.name}: Prix inconnu")

        # 2. Calculate Formules Price
        for formule in order.formules:
            price = await db_manager.get_formule_price(formule.name)
            
            if price is not None:
                total_price += price
                details.append(f"Formule {formule.name}: {price:.2f}€")
            else:
                details.append(f"Formule {formule.name}: Prix inconnu")

        return {
            "total_price": round(total_price, 2),
            "details": details,
            "currency": "EUR"
        }
    except Exception as e:
        logger.error(f"Error calculating price: {e}")
        return {"total_price": 0.0, "message": f"Erreur lors du calcul du prix: {str(e)}"}
