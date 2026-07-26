from typing import List
from pydantic import BaseModel, Field

# Assuming the above models are imported correctly
from BaseModels.RoleClassification import RoleClassification
from BaseModels.LanguageAndInclusivity import LanguageAndInclusivity
from BaseModels.CandidateEvaluation import CandidateEvaluation

class JobEvaluation(BaseModel):
    # UPGRADE: Prevent empty reasoning
    reasoning_analysis: str = Field(
        min_length=20,
        description="Internal step-by-step evaluation. Must contain detailed logical breakdown, cannot be empty."
    )
    
    # UPGRADE: Prevent empty tags
    llm_tags: List[str] = Field(
        min_length=1,
        description=(
            "List of 3-6 core technical skills, tools, or domain keywords extracted STRICTLY from the Job Description "
            "(e.g., ['.NET', 'C#', 'Docker', 'Oracle']). "
            "DO NOT use abstract meta-tags like 'language_friction' or 'junior_vs_mid_senior'."
        )
    )

    # UPGRADE: Prevent empty summaries
    llm_summary: str = Field(
        min_length=20,
        description="Comprehensive summary of position. Cannot be empty."
    )

    role_classification: RoleClassification = Field(
        description="Classification regarding role level, YOE requirements, and work setup."
    )
    
    inclusivity: LanguageAndInclusivity = Field(
        description="Assessment of language friction, visa availability, and foreign friendliness."
    )
    
    candidate_match: CandidateEvaluation = Field(
        description="Specific evaluation comparing candidate skills/experience to JD demands."
    )
