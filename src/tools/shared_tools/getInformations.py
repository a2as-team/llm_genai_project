from src.bdd import DBManager
from logging import getLogger

logger = getLogger(__name__)

async def get_informations()->str:
    """
    Return the complete informations of the restaurant such as location, opening hours, rules, website and all of these kind of infos.
    """
    try:
        db_manager = DBManager()
        informations = await db_manager.get_informations()
        info_retour="""Informations:\n"""
        for info in informations:
            info_retour += f"- {info}\n"
        return info_retour


    except Exception as e:
        logger.error(f"Error getting informations: {e}")
        return f"Error getting informations: {str(e)}"
