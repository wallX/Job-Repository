from pydantic import BaseModel, Field
from typing import List

# Import the CLASSES directly from the modules, NOT the modules themselves
from BaseModels.RoleClassification import RoleClassification
from BaseModels.LanguageAndInclusivity import LanguageAndInclusivity
from BaseModels.CandidateEvaluation import CandidateEvaluation


class JobEvaluation(BaseModel):
    reasoning_analysis: str = Field(
        description="Internal step-by-step evaluation..."
    )
    llm_tags: List[str] = Field(
        description=(
            "List of 3-6 core technical skills, tools, or domain keywords extracted STRICTLY from the Job Description "
            "(e.g., ['.NET', 'C#', 'Docker', 'Oracle']). "
            "DO NOT use abstract meta-tags like 'language_friction' or 'junior_vs_mid_senior'."
        )
    )



    llm_summary: str = Field(
        description="Comprehensive summary of position."
    )

    # These fields must reference the imported Pydantic Classes
    role_classification: RoleClassification = Field(
        description="Classification regarding role level, YOE requirements, and work setup."
    )
    inclusivity: LanguageAndInclusivity = Field(
        description="Assessment of language friction, visa availability, and foreign friendliness."
    )
    candidate_match: CandidateEvaluation = Field(
        description="Specific evaluation comparing candidate skills/experience to JD demands."
    )
