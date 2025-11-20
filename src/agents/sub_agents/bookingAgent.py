from google.adk.agents import LlmAgent,Agent
from src.config import gemini_settings
from src.prompts import BOOKING_PROMPT

booking_agent = Agent(
    name="bookingAgent",
    model=gemini_settings.LIVE_MODEL_NAME,
    instruction=BOOKING_PROMPT,
)