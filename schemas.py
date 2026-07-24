from pydantic import BaseModel, Field

class JobAnalysis(BaseModel):
    title: str = Field(description="Job title extracted or cleaned from the post")
    company: str = Field(description="Name of the hiring company")
    location: str = Field(description="Full location string (e.g. '8001 Zürich / Hybrid')")
    city: str = Field(description="Extracted clean city name (e.g. 'Zürich', 'Bern')")
    workload: str = Field(description="Workload percentage if mentioned (e.g. '80-100%', '100%')")
    contract_type: str = Field(description="Contract type (e.g. 'Permanent position', 'Temporary')")
    
    is_junior: bool = Field(
        description="True if suitable for early-career/junior developers (0-2 years exp)"
    )
    junior_score: float = Field(
        description="Rating from 0.0 (Senior/Lead only) to 10.0 (Ideal Junior position)"
    )
    stack_gap: str = Field(
        description="Key technologies required by the role that the candidate lacks"
    )
    language_friction: str = Field(
        description="Required languages (e.g., 'German B2 required', 'English only')"
    )
    llm_summary: str = Field(
        description="A concise 2-sentence summary of why this job is or isn't a good fit"
    )