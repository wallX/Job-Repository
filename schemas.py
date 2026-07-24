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
    llm_summary: str = Field(
        description="A concise 2-sentence summary explaining the key reasons for the score and any dealbreakers."
    )
    required_yoe: Optional[int] = Field(
        default=None,
        description="Explicit years of experience required (e.g. 3), or None if unspecified."
    )