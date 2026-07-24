from typing import List
from pydantic import BaseModel, Field

class JobEvaluation(BaseModel):    
    reasoning_analysis: str = Field(
        description="Internal step-by-step evaluation: 1) Extract explicit YOE/titles, 2) Identify foreign/language barriers, 3) Contrast candidate stack against JD stack."
    )
    is_junior: bool = Field(
        description="True ONLY if explicit YOE is <= 2 OR title explicitly contains ('Junior', 'Associate', 'Graduate', 'Intern'). Set to False if YOE requirement is >= 3, or if title contains 'Senior', 'Lead', 'Staff', 'Principal', or 'Manager'."
    )
    
    junior_score: float = Field(
        ge=0.0, le=10.0,
        description=(
            "Score from 0.0 to 10.0 based strictly on this formula: "
            "10.0 = Explicitly says 'Junior/No experience required' & 0 YOE. "
            "7.0-9.0 = 1-2 YOE required, standard tech stack. "
            "4.0-6.0 = 3 YOE or ambiguous mid-level requirements. "
            "1.0-3.0 = 4-5 YOE or Senior title without lead duties. "
            "0.0 = Lead/Senior title, >5 YOE required, or niche legacy architecture."
        )
    )
    stack_gap: List[str] = Field(
        description="List of required technologies, frameworks, domain knowledge, or tools mentioned in the JD that are MISSING or NOT explicitly mentioned in the Candidate Profile. If no candidate profile is provided, list all specialized required tech stacks as gaps."
    )
    language_friction: str = Field(
        description="Assessment of language requirements (e.g., 'None: English is sufficient', 'High: Native German C1 required', 'Flexible: English is enough but German is preferred')."
    )
    language_llm: List[str] = Field(
        description="Extracted required languages and levels from the job description (e.g., ['English B2', 'German C1'])."
    )
    language_llm_only_english: bool = Field(
        description="True ONLY if English is the sole mandatory language. False if any local or other language is required or mandatory."
    )
    work_model: str = Field(
        description="The work model for the role: 'Remote', 'On-site', 'Hybrid', or 'Flexible'."
    )
    required_yoe: int = Field(
        description=(
            "Extract required years of experience as an integer. "
            "Rules: 1) Use lower bound if range (e.g., '3-5 years' -> 3). "
            "2) If explicit YOE is missing: 'Junior/Entry' -> 0, 'Mid' -> 3, 'Senior' -> 5, 'Lead/Principal' -> 8. "
            "3) If 'X+ years', use X."
        )
    )
    llm_tags: List[str] = Field(
        description="Key technologies, hard skills, domains, or industry tools extracted directly from the job description."
    )
    foreign_friendly_score: float = Field(
        ge=0.0, le=10.0,
        description=(
            "Calculated score based on 3 criteria (Start at 10.0): "
            "- Deduct 5.0 if local language (non-English) is explicitly MANDATORY/C1+. "
            "- Deduct 2.0 if local language is 'Preferred/B2'. "
            "- Deduct 3.0 if JD explicitly states 'No Visa Sponsorship' or 'Must reside/have work permit in country'. "
            "- Add 2.0 (cap 10) if 'Visa Sponsorship Available' or 'International applicants welcome' is explicitly stated. "
            "- If fully Remote (Global), score is 10.0 unless restricted by timezone/legal residency."
        )
    )
    foreign_friendly_reasons: str = Field(
        description="Must strictly follow format: 'Language Requirements: <details>; Visa Sponsorship: <details>; Cultural Inclusivity: <details>'."
    )
    llm_summary: str = Field(
        description=(
            "A comprehensive English summary of the position. "
            "IF THE ORIGINAL JD IS IN ENGLISH: Provide a concise summary (3-4 sentences) highlighting key responsibilities, tech stack, and notable expectations. "
            "IF THE ORIGINAL JD IS NOT IN ENGLISH: Do NOT translate verbatim. Instead, provide an IN-DEPTH, highly detailed English summary breaking down: "
            "1) Core Responsibilities, 2) Hard/Soft Requirements, 3) Company Context/Benefits, and 4) Any implicit expectations or nuances."
        )
    )