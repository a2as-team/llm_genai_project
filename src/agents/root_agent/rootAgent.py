from google.adk.agents import LlmAgent, Agent
from src.config import gemini_settings
from src.prompts import ROOT_PROMPT
from src.agents.sub_agents import booking_agent, order_agent
from src.tools.shared_tools import get_menu, get_informations
from src.tools.order_tools import (
    add_formule_to_order,
    add_item_to_order,
    get_price,
    update_item_order,
    validate_order,
    remove_formule,
    get_current_order_tool,
)


# root_agent = LlmAgent(
#     name="rootAgent",
#     model=gemini_settings.MODEL_NAME,
#     instruction=ROOT_PROMPT,
#     sub_agents=[booking_agent, order_agent],
# )

root_agent = Agent(
    name="rootAgent",
    model=gemini_settings.LIVE_MODEL_NAME,
    instruction=ROOT_PROMPT,
    # sub_agents=[booking_agent, order_agent],
    tools=[
        get_menu,
        get_informations,
        add_formule_to_order,
        add_item_to_order,
        get_price,
        remove_formule,
        update_item_order,
        validate_order,
        get_current_order_tool,
    ],  
)