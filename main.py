import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import GeminiSettings

settings = GeminiSettings()
client = settings.CLIENT

if __name__ == "__main__":
    if client:
        print("Google GenAI Client initialized successfully.")