import sys
import time
from pathlib import Path
import instructor
import litellm
import config
from pypdf import PdfReader

# Path resolution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from schemas import JobEvaluation
from db import get_jobs_pending_llm, save_llm_evaluation

#client = instructor.from_litellm(litellm.completion, mode=instructor.Mode.JSON)
client = instructor.from_litellm(litellm.completion,  mode=instructor.Mode.JSON_SCHEMA)

def extract_pdf_text(pdf_path: str) -> str:
    full_path = Path(pdf_path).expanduser()
    
    reader = PdfReader(full_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def load_prompts(system_path: str = "data/system.md", user_path: str = "data/user.md") -> tuple[str, str]:
    """
    Reads markdown files and returns (system_prompt, user_prompt) as strings.
    """
    system_file = Path(system_path)
    user_file = Path(user_path)

    if not system_file.exists():
        raise FileNotFoundError(f"System prompt file not found at: {system_file.resolve()}")
    if not user_file.exists():
        raise FileNotFoundError(f"User prompt file not found at: {user_file.resolve()}")

    system_prompt = system_file.read_text(encoding="utf-8").strip()
    user_prompt = user_file.read_text(encoding="utf-8").strip()

    return system_prompt, user_prompt


def analyze_job(title: str, company: str, description: str) -> JobEvaluation:
    """Invokes LiteLLM to generate structured job evaluation."""

    system_prompt, user_template = load_prompts(
        config.SYSTEM_PROMPT_PATH, 
        config.USER_PROMPT_PATH
    )

    cv_text = extract_pdf_text(config.CV_PATH)
    user_content = f"""{user_template}
        --- CANDIDATE CV / PROFILE ---
        {cv_text}

        --- JOB POSTING ---
        Title: {title}
        Company: {company}

        Description:
        {description[:20000]}"""

    return client.chat.completions.create(
        model=config.DEFAULT_ANALYSIS_MODEL,
        api_base=config.API_BASE,
        response_model=JobEvaluation,
        max_retries=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={
            "type": "json_object",
            "schema": JobEvaluation.model_json_schema(),
            "strict": True
        },
        temperature=config.LLM_TEMPERATURE,  # Low temperature for deterministic scoring
        extra_body={"num_ctx": 16384, "keep_alive": config.KEEP_ALIVE}  # Ensure context window is sufficient for long job descriptions
    )


def run_analysis_pipeline(batch_size: int = 10):
    """Fetches extracted jobs from DB, runs LLM scoring, and updates pipeline.db."""
    jobs = get_jobs_pending_llm(limit=batch_size)

    if not jobs:
        print(" No jobs pending LLM evaluation.")
        return

    if not config.SYSTEM_PROMPT_PATH or not config.USER_PROMPT_PATH:
        system_prompt, user_template = load_prompts(
                config.SYSTEM_PROMPT_PATH, 
                config.USER_PROMPT_PATH
            )
        if not system_prompt or not user_template:
            raise ValueError("System and user prompts must be provided for LLM evaluation.")
        raise ValueError("System and user prompts path must be provided for LLM evaluation.")

    print(f"Starting LLM Analysis for {len(jobs)} jobs using {config.DEFAULT_ANALYSIS_MODEL}...\n")

    for idx, job in enumerate(jobs, 1):
        job_id = job["job_id"]
        title = job["title"] or "Unknown Title"
        company = job["company"] or "Unknown Company"
        description = job["full_description"]

        print(f"[{idx}/{len(jobs)}] Evaluating: {title} @ {company} (ID: {job_id})")

        try:
            eval_result: JobEvaluation = analyze_job(title, company, description)

            # Format stack gap list into a clean comma-separated string for SQLite
            stack_gap_str = ", ".join(eval_result.stack_gap) if eval_result.stack_gap else "None"

            #Format language_llm list into a clean comma-separated string for SQLite
            language_llm_str = ", ".join(eval_result.language_llm) if eval_result.language_llm else "None"

            # Format LLM tags into a clean comma-separated string for SQLite
            llm_tags_str = ", ".join(eval_result.llm_tags) if eval_result.llm_tags else "None"

            save_llm_evaluation(
                job_id=job_id,
                is_junior=eval_result.is_junior,
                junior_score=eval_result.junior_score,
                stack_gap=stack_gap_str,
                language_friction=eval_result.language_friction,
                llm_summary=eval_result.llm_summary,
                language_llm=language_llm_str,
                language_llm_only_english=eval_result.language_llm_only_english,
                work_model=eval_result.work_model,
                required_yoe=eval_result.required_yoe,
                foreign_friendly_score=eval_result.foreign_friendly_score,
                foreign_friendly_reasons=eval_result.foreign_friendly_reasons,
                llm_tags=llm_tags_str,
                cv_match_rank=eval_result.cv_match_rank,
                cv_match_reasons=eval_result.cv_match_reasons,
                status="Processed"
            )

            print(f"  Score: {eval_result.junior_score}/100 | Junior: {eval_result.is_junior}")
            print(f"  Stack Gap: {stack_gap_str}")
            print(f"  Language: {eval_result.language_friction}")
            print(f"  Summary: {eval_result.llm_summary}")
            print(f"  Foreign Friendly Score: {eval_result.foreign_friendly_score}/100")
            print(f"  Foreign Friendly Reasons: {eval_result.foreign_friendly_reasons}")
            print(f"  LLM Tags: {llm_tags_str}")
            print(f"  CV Match Rank: {eval_result.cv_match_rank}")
            print(f"  CV Match Reasons: {eval_result.cv_match_reasons}\n")



        except Exception as e:
            print(f"  Error processing job {job_id}: {e}\n")

        time.sleep(0.5)

if __name__ == "__main__":
    run_analysis_pipeline(batch_size=10)