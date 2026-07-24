import sys
import time
from pathlib import Path
import instructor
import litellm

# Path resolution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from schemas import JobEvaluation
from db import get_jobs_pending_llm, save_llm_evaluation

