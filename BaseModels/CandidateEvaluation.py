from typing import List, Literal
from pydantic import BaseModel, Field


class CandidateEvaluation(BaseModel):
    """Direct comparison between candidate profile and JD requirements."""
    
    # 1. HARD GATE FIRST - Forces the decision before generating text
    has_critical_dealbreakers: bool = Field(
        description=(
            "MUST BE TRUE if candidate lacks mandatory core tech stack (e.g. missing .NET/C#) "
            "or has fewer years of experience than required for mid/senior roles. "
            "Java/Python background DOES NOT substitute missing required stack."
        )
    )

    # 2. RATED ENUM SECOND - Bound immediately to step 1
    cv_match_rank: Literal["Unfit", "Borderline", "Fit"] = Field(  # Note: "Unfit" is first in Literal
        description=(
            "STRICT MANDATORY RULE:\n"
            "- IF has_critical_dealbreakers is True -> MUST BE 'Unfit'. NO EXCEPTIONS.\n"
            "- Select 'Fit' ONLY if candidate meets core stack AND required YOE.\n"
            "- Select 'Borderline' ONLY if candidate has partial exact-stack overlap."
        )
    )

    # 3. TEXT EXPLANATION LAST - Written after the rating is locked in
    stack_gap: List[str] = Field(
        description="List of required technologies/tools mentioned in JD that are missing in Candidate Profile."
    )
    
    cv_match_reasons: str = Field(
        description="Detailed plain text explanation supporting the assigned cv_match_rank."
    )
    
    cv_match_rank: Literal["Fit", "Unfit", "Borderline"] = Field(
        description=(
            "Evaluate candidate fit against role requirements with strict gating rules:\n"
            "CRITICAL RULE: If has_critical_dealbreakers is true, THIS FIELD MUST BE 'Unfit'. NO EXCEPTIONS."
            "A strong background in non-relevant languages (e.g., Java, Python) DOES NOT substitute missing core stack requirements.\n"
            "- Select 'Fit': Candidate meets or exceeds mandatory core stack and experience requirements.\n"
            "- Select 'Borderline': Candidate has partial overlap in the exact stack or slightly less experience than requested.\n"
            "- Select 'Unfit': Candidate lacks core non-negotiable tech stack experience or required YOE."
        )
    )