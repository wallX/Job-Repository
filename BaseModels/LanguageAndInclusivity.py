from typing import List, Literal
from pydantic import BaseModel, Field

class LanguageAndInclusivity(BaseModel):
    """Evaluation of language requirements, sponsorship capabilities, and international accessibility."""
    
    language_friction: str = Field(
        description=(
            "Job-level friction for non-local/international applicants (IGNORE CANDIDATE CV):\n"
            "- 'Low: English-only environment' -> Job is in English or explicitly accepts English speakers.\n"
            "- 'High: [Language] required' -> Job description is in a non-English language or explicitly requires local language fluency."
        )
    )


    language_llm: List[str] = Field(
    description=(
        "List ALL human languages required or implied by the Job Description (IGNORE CANDIDATE CV).\n"
        "RULES:\n"
        "1. Include the language the Job Description itself is written in.\n"
        "2. DO NOT use 2-letter ISO codes (e.g., 'pt', 'en'). Use full English names.\n"
        "3. DO NOT include meta-tags (e.g., 'language_proficiency').\n"
        "FORMAT: '[Full Language Name] [Level if specified]'\n"
        "Examples: ['Portuguese Native/Fluent', 'English B2'], ['German C1 Required'], ['English']."
        )
    )

    language_llm_only_english: bool = Field(
        description="True ONLY if English is the sole mandatory language. False if any local or other language is required or mandatory."
    )
    foreign_friendly_score: float = Field(
        ge=0.0, le=100.0,
        description=(
            "Calculated score based on 3 criteria (Start at 100.0): "
            "- Deduct 50 if local language (non-English) is explicitly MANDATORY/C1+. "
            "- Deduct 20 if local language is 'Preferred/B2'. "
            "- Deduct 30 if JD explicitly states 'No Visa Sponsorship' or 'Must reside/have work permit in country'. "
            "- Add 20 (cap 100) if 'Visa Sponsorship Available' or 'International applicants welcome' is explicitly stated. "
            "- If fully Remote (Global), score is 100 unless restricted by timezone/legal residency."
        )
    )
    foreign_friendly_reasons: str = Field(
        description="Must strictly follow format: 'Language Requirements: <details>; Visa Sponsorship: <details>; Cultural Inclusivity: <details>'."
    )




