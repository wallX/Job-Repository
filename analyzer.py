import sys
import time
from pathlib import Path
import instructor
import litellm
import config

# Path resolution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from schemas import JobEvaluation
from db import get_jobs_pending_llm, save_llm_evaluation

client = instructor.from_litellm(litellm.completion, mode=instructor.Mode.JSON)


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
    user_content = f"{user_template}\n\n--- Job Posting ---\nTitle: {title}\nCompany: {company}\n\nDescription:\n{description[:4000]}"

    return client.chat.completions.create(
        model=config.DEFAULT_MODEL,
        api_base=config.API_BASE,
        response_model=JobEvaluation,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=config.LLM_TEMPERATURE  # Low temperature for deterministic scoring
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

    print(f"Starting LLM Analysis for {len(jobs)} jobs using {config.DEFAULT_MODEL}...\n")

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
                status="Processed"
            )

            print(f"  Score: {eval_result.junior_score}/10 | Junior: {eval_result.is_junior}")
            print(f"  Stack Gap: {stack_gap_str}")
            print(f"  Language: {eval_result.language_friction}")
            print(f"  Summary: {eval_result.llm_summary}\n")


        except Exception as e:
            print(f"  Error processing job {job_id}: {e}\n")

        time.sleep(0.5)

if __name__ == "__main__":
    run_analysis_pipeline(batch_size=10)