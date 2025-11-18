from google.adk.agents import LlmAgent
from config import gemini_settings
from prompts import BOOKING_PROMPT

booking_agent = LlmAgent(
    name="bookingAgent",
    model=gemini_settings.MODEL_NAME,
    instruction=BOOKING_PROMPT,
)