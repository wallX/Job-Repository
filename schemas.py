from typing import List, Optional

from pydantic import BaseModel, Field

class JobEvaluation(BaseModel):
    title: str = Field(description="Job title extracted or cleaned from the post")
    company: str = Field(description="Name of the hiring company")
    location: str = Field(description="Full location string (e.g. '8001 Zürich / Hybrid')")
    city: str = Field(description="Extracted clean city name (e.g. 'Zürich', 'Bern')")
    workload: str = Field(description="Workload percentage if mentioned (e.g. '80-100%', '100%')")
    contract_type: str = Field(description="Contract type (e.g. 'Permanent position', 'Temporary')")
    
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
        description="Assessment of language requirements (e.g., 'None: English adequate', 'High: Native German C1 required', 'Medium: French B2')."
    )
    language_llm: List[str] = Field(
        description="LLM's interpretation of the language requirements, extracted from the job description."
    )
    language_llm_only_english: bool = Field(
        description="True if the LLM determined that English alone is sufficient for the role, False if additional languages are required and mandatory."
    )
    work_model: str = Field(
        description="The work model for the role (e.g., 'Remote', 'On-site', 'Hybrid', 'Flexible')."
    )
    required_yoe: int = Field(
        description="Explicit years of experience required (e.g. 3), or an estimate based on the job description if unspecified. But add an observation in the summary if it's an estimate."
    )
    llm_summary: str = Field(
        description="A concise summary of the job's requirements, responsibilities, and expectations as interpreted by the LLM."
    )