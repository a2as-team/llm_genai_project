from dotenv import load_dotenv
load_dotenv() 
import os
from src.config import gemini_settings

if __name__ == "__main__":
    key=os.getenv("GOOGLE_API_KEY")
    print("GOOGLE_API_KEY:", key)
    print("Loaded from config:", gemini_settings.GOOGLE_API_KEY)