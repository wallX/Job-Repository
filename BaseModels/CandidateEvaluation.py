from typing import List, Literal
from pydantic import BaseModel, Field, model_validator

class CandidateEvaluation(BaseModel):
    """Direct comparison between candidate profile and JD requirements."""
    
    has_critical_dealbreakers: bool = Field(
        description=(
            "MUST BE TRUE if candidate lacks mandatory core tech stack (e.g. missing .NET/C#) "
            "or has fewer years of experience than required for mid/senior roles. "
            "Java/Python background DOES NOT substitute missing required stack."
        )
    )

    # UPGRADE: Removed duplicate field definition and enforced Literal typing
    cv_match_rank: Literal["Unfit", "Borderline", "Fit"] = Field(
        description=(
            "STRICT MANDATORY RULE:\n"
            "- IF has_critical_dealbreakers is True -> MUST BE 'Unfit'. NO EXCEPTIONS.\n"
            "- Select 'Fit' ONLY if candidate meets core stack AND required YOE.\n"
            "- Select 'Borderline' ONLY if candidate has partial exact-stack overlap."
        )
    )

    stack_gap: List[str] = Field(
        description="List of required technologies/tools mentioned in JD that are missing in Candidate Profile."
    )
    
    cv_match_reasons: str = Field(
        min_length=10,
        description="Detailed plain text explanation supporting the assigned cv_match_rank."
    )

    # UPGRADE: Mechanically enforces the dealbreaker rule so the LLM cannot violate it
    @model_validator(mode='after')
    def enforce_dealbreaker_logic(self) -> 'CandidateEvaluation':
        if self.has_critical_dealbreakers and self.cv_match_rank != "Unfit":
            raise ValueError("If has_critical_dealbreakers is True, cv_match_rank MUST be 'Unfit'.")
        return self
