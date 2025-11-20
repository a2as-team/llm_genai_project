from google.adk.agents import LlmAgent, Agent
from src.config import gemini_settings
from src.prompts import ROOT_PROMPT
from src.agents.sub_agents import booking_agent, order_agent
from src.tools import (
    get_menu,
    get_informations,
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
    tools=[get_menu,get_informations],  
)