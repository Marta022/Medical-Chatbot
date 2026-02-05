from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

# Load llm.txt as system prompt
BASE_DIR = Path(__file__).parent.parent
LLM_TXT_PATH = BASE_DIR / "llm.txt"

with open(LLM_TXT_PATH, "r", encoding="utf-8") as f:
    BASE_SYSTEM_PROMPT = f.read().strip()


    
