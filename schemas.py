from typing import List, Optional

from pydantic import BaseModel, Field

class JobEvaluation(BaseModel):    
    is_junior: bool = Field(
        description="True if suitable for early-career/junior developers (0-2 YOE or explicit junior/intern titles). False if senior, lead, or >3 YOE required."
    )
    junior_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Overall suitability score from 0.0 (Unsuitable / Senior) to 10.0 (Perfect Junior Match)."
    )
    stack_gap: List[str] = Field(
        description="List of technologies, frameworks, or tools required by the job that the candidate lacks or needs to learn."
    )
    language_friction: str = Field(
        description="Assessment of language requirements (e.g., 'None: English is sufficient', 'High: Native German C1 required', 'Flexible: English is enough but German is preferred')."
    )
    language_llm: List[str] = Field(
        description="LLM's interpretation of the language requirements, extracted from the job description. Result should be a list of languages or language levels (e.g., ['English', 'German C1'])."
    )
    language_llm_only_english: bool = Field(
        description="True if the LLM determined that English is sufficient for the role, False if additional languages are required or mandatory in the job description."
    )
    work_model: str = Field(
        description="The work model for the role (e.g., 'Remote', 'On-site', 'Hybrid', 'Flexible')."
    )
    required_yoe: int = Field(
        description="Number of years of experience required, use explicit values when available if not specified try to estimate. Result should be a integer number. If the job is suitable for junior developers, this should be 0-3. Mid-level positions typically require 3-5 years. If senior, this should be 5 or more."
    )
    llm_tags: List[str] = Field(
        description="List of tags or keywords extracted by the LLM from the job description, highlighting key skills, technologies, or requirements mentioned in the posting."
    )

    foreign_friendly_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Score from 0.0 (Not foreign-friendly) to 10.0 (Highly foreign-friendly) indicating how welcoming the job is to international applicants, based on language requirements, visa sponsorship, and cultural inclusivity."
    )

    foreign_friendly_reasons: str = Field(
        description="Reasons for the foreign-friendly score, including details about language requirements, visa sponsorship, and cultural inclusivity. include the following structure: 'Language Requirements: ...; Visa Sponsorship: ...; Cultural Inclusivity: ...'. If the job is not foreign-friendly, provide specific reasons why. And if they include any mention about international applicants paraphrase it or quote it."
    )

    llm_summary: str = Field(
        description="If description is not in English make the full translation and at the end a concise summary in English. Include any notable details about the role, company, or required skills and requirements, responsibilities, expectations as interpreted by the LLM."
    )


