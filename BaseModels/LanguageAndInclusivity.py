from typing import List
from pydantic import BaseModel, Field

class LanguageAndInclusivity(BaseModel):
    """Evaluation of language requirements, sponsorship capabilities, and international accessibility."""
    
    language_friction: str = Field(
        min_length=5,
        description=(
            "CRITICAL: If the job ONLY requires English, this is ALWAYS 'Low: English-only environment'. NEVER label English as 'High' friction.\n"
            "Job-level friction for non-local/international applicants (IGNORE CANDIDATE CV):\n"
            "- 'Low: English-only environment' -> Job is in English or explicitly accepts English speakers.\n"
            "- 'High: [Language] required' -> Job description is in a non-English language or explicitly requires local language fluency."
        )
    )

    # UPGRADE: Added min_length to prevent empty language lists
    language_llm: List[str] = Field(
        min_length=1,
        description=(
            "List ALL SPOKEN human languages (e.g., English, Spanish, German) required or implied by the Job Description (IGNORE CANDIDATE CV). DO NOT list programming languages.\n"
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
    
    # UPGRADE: Added Regex pattern to strictly enforce the requested format
    foreign_friendly_reasons: str = Field(
        pattern=r"^Language Requirements:.*; Visa Sponsorship:.*; Cultural Inclusivity:.*$",
        description="Must strictly follow format: 'Language Requirements: <details>; Visa Sponsorship: <details>; Cultural Inclusivity: <details>'."
    )
