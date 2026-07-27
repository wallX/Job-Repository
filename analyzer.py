import json
import sys
import time
from pathlib import Path
import instructor
import litellm
import config
from pypdf import PdfReader
from typing import TypeVar, Type
import tiktoken

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

def get_cleaned_jd(raw_jd: str, client, config, max_tokens_threshold: int = 800) -> str:
    """
    Checks JD length. If it exceeds threshold, uses a fast LLM pass to strip fluff 
    and return ONLY the requirements. Otherwise, returns raw_jd as-is.
    """
    # Quick token estimation (approx 4 chars per token)
    estimated_tokens = len(raw_jd) // 4
    
    if estimated_tokens <= max_tokens_threshold:
        print(f"JD length ({estimated_tokens} tokens) is within threshold ({max_tokens_threshold}). No cleaning needed.")
        return raw_jd  # No pre-processing needed! Saves latency and API calls.
    print(f"JD length ({estimated_tokens} tokens) exceeds threshold ({max_tokens_threshold}). Invoking LLM to clean and condense...")

    cleaner_system_prompt = (
        "You are an expert technical recruiter and data analyst. Your goal is to condense a job description "
        "into a structured, rich, yet concise summary. Retain crucial operational, business, team, and technical "
        "context while omitting repetitive corporate boilerplate."
    )

    # System prompt strictly instructing the model to condense the text
    cleaner_user_prompt = f"""Summarize and retain the key aspects from this job description. 

You MUST STRICTLY divide your response into two distinct sections: '=== SPECIFIC ROLE REQUIREMENTS ===' and '=== COMPANY CONTEXT & OPERATIONS ==='. 
This separation is MANDATORY to prevent confusing the company's general industry, broad tech stack, or daily business operations with the actual skills required for the candidate.

=== SPECIFIC ROLE REQUIREMENTS ===
Focus ONLY on what the candidate actually needs to do and know for this specific position:
1. Seniority & Required Experience: Seniority level, required YOE, education, or background.
2. Work Model & Logistics: Work model (Onsite, Hybrid, Remote), location/region, contract type (CDI, full-time, etc.).
3. Languages: Spoken human language requirements (e.g., English, French, German).
4. Role-Specific Skills & Tools: 
   - Mandatory / Must-have skills, tools, and technical knowledge explicitly tied to the daily responsibilities.
   - Nice-to-have / Optional skills for the role.
   (CRITICAL: Include skills, tools, or domain knowledge here ONLY if the candidate strictly needs them to perform this job. Do not include company industry knowledge unless explicitly required for the role itself.)
5. Role & Team Context: Core responsibilities, daily tasks, and team setup.
6. Critical Role Requirements: Key soft skills, autonomy expectations, or specific functional requirements.

=== COMPANY CONTEXT & OPERATIONS ===
Focus on background information that provides context but MUST NOT be treated as mandatory candidate requirements:
1. Company Industry & Business Domain: What the company does, its product, and overarching goals (e.g., "Agricultural company raising chickens", "SaaS Studio handling payments").
2. General Company Operations: Any tools, infrastructure, frameworks, or business practices mentioned as part of the company's broader operations that are NOT explicitly tied to the daily duties of this specific role.

OMIT ONLY: Multi-stage recruitment interview steps, generic employee benefits/perks (e.g., gym pass, offsite trips, coffee budget), standard corporate fluff, and legal disclaimer blocks.

RAW JOB POSTING:
{raw_jd}"""



    # Call the model without schema enforcement for maximum speed & minimal overhead
    # Note: Using a lightweight model like gpt-4o-mini / gemini-flash if available, or config.DEFAULT_ANALYSIS_MODEL
    cleaned_text: str = client.chat.completions.create(
        model=config.DEFAULT_CONVERSATION_MODEL,
        api_base=config.API_BASE,
        response_model=str,
        messages=[
            {"role": "system", "content": cleaner_system_prompt},
            {"role": "user", "content": cleaner_user_prompt}
        ],
        temperature=0.0,  # Zero temperature for deterministic extraction
        extra_body={"num_ctx": 16384, "keep_alive": config.KEEP_ALIVE}
    )

    return cleaned_text.strip()

def analyze_job(
    title: str, 
    company: str, 
    contract_type: str, 
    seniority_level: str, 
    industry: str, 
    description: str, 
    output_schema: Type[T] = JobEvaluation  # Defaults to JobEvaluation
) -> T:
    """Invokes LiteLLM to generate a structured evaluation using any Pydantic model schema."""

    system_prompt, user_template = load_prompts(
        config.SYSTEM_PROMPT_PATH, 
        config.USER_PROMPT_PATH
    )

    cv_text = extract_pdf_text(config.CV_PATH)

    processed_description = get_cleaned_jd(description, client, config, max_tokens_threshold=1200)

    user_content = f"""{user_template}
--- CANDIDATE CV / PROFILE ---
{cv_text}

--- JOB POSTING ---
Title: {title}
Company: {company}
Contract Type: {contract_type}
Seniority Level: {seniority_level}
Industry: {industry}

--- JOB DESCRIPTION ---
{processed_description}"""

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
        contract_type = job["contract_type"] or "Unknown Contract Type"
        seniority_level = job["seniority_level"] or "Unknown Seniority Level"
        industry = job["industry"] or "Unknown Industry"

        print(f"[{idx}/{len(jobs)}] Evaluating: {title} @ {company} (ID: {job_id})")

        try:
            eval_result: JobEvaluation = analyze_job(title, company, contract_type, seniority_level, industry, description, output_schema=JobEvaluation)

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