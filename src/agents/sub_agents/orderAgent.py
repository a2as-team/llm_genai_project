from google.adk.agents import LlmAgent,Agent
from src.config import gemini_settings
from src.prompts import ORDER_PROMPT
from src.tools import (
    add_item_to_order,
    get_menu,
    validate_order,
    get_price,
    update_item_order,
    add_formule_to_order,
    remove_formule,
)

order_agent = Agent(
    name="orderAgent",
    model=gemini_settings.LIVE_MODEL_NAME,
    instruction=ORDER_PROMPT,
    tools=[
        add_item_to_order,
        add_formule_to_order,
        remove_formule,
        get_menu,
        validate_order,
        get_price,
        update_item_order,
    ],
)
