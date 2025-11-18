from src.config import GeminiSettings

settings = GeminiSettings()
client = settings.CLIENT

if __name__ == "__main__":
    if client:
        print("Google GenAI Client initialized successfully.")