from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai

class GeminiSettings(BaseSettings):
    GOOGLE_API_KEY: str
    MODEL_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        )
    
    def __init__(self, **data):
        super().__init__(**data)
        self.CLIENT=genai.Client(api_key=self.GOOGLE_API_KEY)

gemini_settings = GeminiSettings()
