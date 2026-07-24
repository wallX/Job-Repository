import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "pipeline.db"
SYSTEM_PROMPT_PATH = BASE_DIR / "data" / "system.md"
USER_PROMPT_PATH = BASE_DIR / "data" / "user.md"

# LLM Configurations
API_BASE = os.getenv("API_BASE", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "ollama/llama3.2")
LLM_TEMPERATURE = 0.1  # Low temperature for consistent JSON extraction
MAX_TOKENS = 1500