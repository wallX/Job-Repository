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
        description="Explicit years of experience required (e.g. 3), or an integer estimate based on the job description if unspecified. But add an observation in the summary if it's an estimate. Result should 0 if the job is explicitly for juniors or interns. Result should be a number."
    )
    llm_summary: str = Field(
        description="If description is not in English make the full translation and at the end a concise summary in English. Include any notable details about the role, company, or required skills and requirements, responsibilities, expectations as interpreted by the LLM."
    )


