from google.adk.agents import LlmAgent
from config import gemini_settings
from prompts import ORDER_PROMPT
from tools import (
    add_item_to_order,
    create_order,
    get_menu,
    validate_order,
    get_price,
    get_current_order,
    update_item_order,
    add_formule_to_order,
    update_formule_item,
    remove_formule,
)

order_agent = LlmAgent(
    name="orderAgent",
    model=gemini_settings.MODEL_NAME,
    instruction=ORDER_PROMPT,
    tools=[
        create_order,
        add_item_to_order,
        add_formule_to_order,
        update_formule_item,
        remove_formule,
        get_menu,
        validate_order,
        get_price,
        get_current_order,
        update_item_order,
    ],
)
