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
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = 0.1  # Low temperature for consistent JSON extraction
MAX_TOKENS = 1500