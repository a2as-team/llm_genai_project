from src.bdd import DBManager
from logging import getLogger

logger = getLogger(__name__)

async def get_menu()->str:
    """
    Returns the menu string.
    """
    try:
        db_manager = DBManager()
        menu_items = await db_manager.get_menu()
        menu="""Menu:\n"""
        for item in menu_items:
            menu += f"- {item}\n"
        return menu


    except Exception as e:
        logger.error(f"Error getting menu: {e}")
        return f"Error getting menu: {str(e)}"

