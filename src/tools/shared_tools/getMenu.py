from src.bdd import DBManager
from logging import getLogger

logger = getLogger(__name__)

async def get_menu()->str:
    """
    Return the complete menu of the restaurant.
    """
    try:
        db_manager = DBManager()
        menu_items, menu_formules = await db_manager.get_menu()
        menu="""Menu:\nItems Uniques:\n"""
        for item in menu_items:
            menu += f"- {item}\n"
        menu += "Formules:\n"
        for formule in menu_formules:
            menu += f"- {formule}\n"
        return menu


    except Exception as e:
        logger.error(f"Error getting menu: {e}")
        return f"Error getting menu: {str(e)}"

