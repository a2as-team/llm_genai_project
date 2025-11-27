from google.adk.agents import LlmAgent, Agent
from src.config import gemini_settings
from src.prompts import ROOT_PROMPT
from src.tools.shared_tools import get_menu, get_informations
from src.tools.order_tools import (
    validate_order,
)

root_agent = Agent(
    name="rootAgent",
    model=gemini_settings.LIVE_MODEL_NAME,
    instruction=ROOT_PROMPT,
    tools=[
        get_menu,
        get_informations,
        validate_order,
    ],  
)