from google.adk.agents import Agent
from src.config import gemini_settings
from src.prompts import get_root_prompt
from src.tools import (
    get_menu,
    get_informations,
    validate_order,
    validate_booking,
)


def create_root_agent() -> Agent:
    """
    Create the root agent with current restaurant configuration.
    
    Uses get_root_prompt() to inject cached restaurant hours and capacity.
    Should be called after RestaurantCache.initialize().
    """
    return Agent(
        name="rootAgent",
        model=gemini_settings.LIVE_MODEL_NAME,
        instruction=get_root_prompt(),
        tools=[
            get_menu,
            get_informations,
            validate_order,
            validate_booking,
        ],  
    )


# Create agent instance (will use fallback values if cache not initialized)
root_agent = create_root_agent()