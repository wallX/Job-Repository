import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "pipeline.db"
SYSTEM_PROMPT_PATH = BASE_DIR / "data" / "system.md"
CHAT_SYSTEM_PROMPT_PATH = BASE_DIR / "data" / "chat_system.md"
USER_PROMPT_PATH = BASE_DIR / "data" / "user.md"
CV_BASE_PATH =  BASE_DIR / "data" / "cv.pdf"

# LLM Configurations
API_BASE = os.getenv("API_BASE", "http://localhost:11434")
DEFAULT_ANALYSIS_MODEL = os.getenv("DEFAULT_ANALYSIS_MODEL", "ollama/qwen2.5:14b")
DEFAULT_CONVERSATION_MODEL = os.getenv("DEFAULT_CONVERSATION_MODEL", "ollama/qwen2.5:7b")
KEEP_ALIVE = int(os.getenv("KEEP_ALIVE", 0))
LLM_TEMPERATURE = 0.1  # Low temperature for consistent JSON extraction
MAX_TOKENS = 1500

# CV Path
CV_PATH = Path(os.getenv("CV_PATH", CV_BASE_PATH))