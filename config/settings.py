from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

# Guardrail LLM toggle (default: on)
GUARDRAIL_LLM_ENABLED = os.getenv("GUARDRAIL_LLM_ENABLED", "true").strip().lower() == "true"

# Load llm.txt as system prompt (see llm.txt)
LLM_TXT_PATH = "llm.txt"

with open(LLM_TXT_PATH, "r", encoding="utf-8") as f:
    BASE_SYSTEM_PROMPT = f.read().strip()


    
