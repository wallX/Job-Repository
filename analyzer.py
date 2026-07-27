import sys
import time
from pathlib import Path
import instructor
import litellm
import config
from pypdf import PdfReader
from typing import TypeVar, Type

# Path resolution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db import get_jobs_pending_llm, save_llm_evaluation
from BaseModels.JobEvaluation import JobEvaluation
from BaseModels.CandidateEvaluation import CandidateEvaluation
from BaseModels.LanguageAndInclusivity import LanguageAndInclusivity
from BaseModels.RoleClassification import RoleClassification


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

T = TypeVar("T", bound=litellm.BaseModel)

def analyze_job(
    title: str, 
    company: str, 
    description: str, 
    output_schema: Type[T] = JobEvaluation  # Defaults to JobEvaluation
) -> T:
    """Invokes LiteLLM to generate a structured evaluation using any Pydantic model schema."""

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
        {description}"""

    # Extract JSON schema directly from the passed-in model class
    return client.chat.completions.create(
        model=config.DEFAULT_ANALYSIS_MODEL,
        api_base=config.API_BASE,
        response_model=output_schema,
        max_retries=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={
            "type": "json_object",
            "schema": output_schema.model_json_schema(),
            "strict": True
        },
        temperature=config.LLM_TEMPERATURE,
        extra_body={"num_ctx": 16384, "keep_alive": config.KEEP_ALIVE}
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
            eval_result: JobEvaluation = analyze_job(title, company, description, output_schema=JobEvaluation)

            role: RoleClassification = eval_result.role_classification
            inclusivity: LanguageAndInclusivity = eval_result.inclusivity
            candidate: CandidateEvaluation = eval_result.candidate_match

            # 2. Extract nested models for cleaner access
            role = eval_result.role_classification
            inclusivity = eval_result.inclusivity
            candidate = eval_result.candidate_match

            # Format stack gap list into a clean comma-separated string for SQLite
            stack_gap_str = ", ".join(candidate.stack_gap) if candidate.stack_gap else "None"
            language_llm_str = ", ".join(inclusivity.language_llm) if isinstance(inclusivity.language_llm, list) else (inclusivity.language_llm or "None")
            llm_tags_str = ", ".join(eval_result.llm_tags) if eval_result.llm_tags else "None"

            #print(eval_result.model_dump_json(indent=3))

            save_llm_evaluation(
                job_id=job_id,
                
                # Role Classification
                is_junior=role.is_junior,
                junior_score=role.junior_score,
                required_yoe=role.required_yoe,
                work_model=role.work_model,
                
                # Candidate Matching
                stack_gap=stack_gap_str,
                cv_match_rank=candidate.cv_match_rank,
                cv_match_reasons=candidate.cv_match_reasons,
                
                # Inclusivity & Language
                language_friction=inclusivity.language_friction,
                language_llm=language_llm_str,  # Passed directly as List[str]
                language_llm_only_english=inclusivity.language_llm_only_english,
                foreign_friendly_score=inclusivity.foreign_friendly_score,
                foreign_friendly_reasons=inclusivity.foreign_friendly_reasons,
                
                # Root level attributes
                llm_summary=eval_result.llm_summary,
                llm_tags=llm_tags_str,
                
                status="Processed"
            )
            try:
                print(f"  Score: {role.junior_score}/100 | Junior: {role.is_junior}")
                print(f"  Stack Gap: {stack_gap_str}")
                print(f"  Language: {inclusivity.language_friction}")
                print(f"  Summary: {eval_result.llm_summary}")
                print(f"  Foreign Friendly Score: {inclusivity.foreign_friendly_score}/100")
                print(f"  Foreign Friendly Reasons: {inclusivity.foreign_friendly_reasons}")
                print(f"  LLM Tags: {llm_tags_str}")
                print(f"  CV Match Rank: {candidate.cv_match_rank}")
                print(f"  CV Match Reasons: {candidate.cv_match_reasons}\n")
            except Exception as e:
                print(f"  Error printing evaluation details for job {job_id} maybe forgot to change field names: {e}\n")



        except Exception as e:
            print(f"  Error processing job {job_id}: {e}\n")

        time.sleep(0.5)

if __name__ == "__main__":
    run_analysis_pipeline(batch_size=10)