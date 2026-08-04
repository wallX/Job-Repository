from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LanguageRequirement(BaseModel):
    language: str = Field(
        description=(
            "Full English name of the spoken human language (e.g., 'English', 'Spanish', 'Portuguese').\n"
            "STRICT RULES:\n"
            "1. DO NOT use 2-letter ISO codes (e.g., 'en', 'pt', 'es'). Use full names.\n"
            "2. DO NOT include meta-tags or generic keys (e.g., 'language_proficiency', 'spoken_language').\n"
            "3. DO NOT include programming languages (e.g., 'Python', 'JavaScript')."
        )
    )
    
    level: Optional[str] = Field(
        default=None,
        description=(
            "The proficiency level OR qualifying descriptor/adjective stated in the job offer.\n"
            "EXAMPLES:\n"
            "- Proficiency levels: 'A1', 'B2', 'C1', 'Native', 'Fluent', 'Conversational'\n"
            "- Requirement descriptors: 'Is a plus', 'Optional', 'Preferred', 'Nice to have', 'Bonus'\n"
            "- Combined (if both exist): 'Fluent / Is a plus'\n"
            "Set to null ONLY if no level, adjective, or status descriptor is mentioned."
        )
    )

    @property
    def formatted(self) -> str:
        """Helper to get standardized string output like 'English C1' or 'English'."""
        return f"{self.language} {self.level}".strip() if self.level else self.language

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
    language_llm: List[LanguageRequirement] = Field(
        min_length=1,
        description=(
            "List all spoken human languages required or implied by the Job Description "
            "(including the language the job posting itself is written in).\n\n"
            "CRITICAL INSTRUCTION:\n"
            "The input context contains both a Candidate CV and a Job Description. "
            "You MUST IGNORE the Candidate CV entirely. Extract ONLY language requirements requested by the employer."
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

    @field_validator("language_llm", mode="after")
    @classmethod
    def convert_to_string_list(cls, v):
        formatted_list = []
        for item in v:
            if isinstance(item, LanguageRequirement):
                formatted_list.append(item.formatted)
            else:
                formatted_list.append(str(item))
        return formatted_list
