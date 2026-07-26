from typing import Literal
from pydantic import BaseModel, Field, model_validator

class RoleClassification(BaseModel):
    """Metadata regarding role level, experience requirements, and work arrangements STRICTLY derived from the Job Description."""
    
    is_junior: bool = Field(
        description=(
            "EVALUATE THE JOB DESCRIPTION ONLY (IGNORE THE CANDIDATE CV).\n"
            "True ONLY if the JOB REQUIREMENT YOE is <= 2 OR the JOB TITLE explicitly contains ('Junior', 'Associate', 'Graduate', 'Intern').\n"
            "MUST BE FALSE if the JOB REQUIREMENT YOE is >= 3, or if the JOB TITLE contains 'Senior', 'Lead', 'Staff', 'Principal', or 'Manager'."
        )
    )
    
    required_yoe: int = Field(
        ge=0,
        description=(
            "Extract required years of experience from the JOB DESCRIPTION as an integer. "
            "Rules: 1) Use lower bound if range (e.g., '3-5 years' -> 3). "
            "2) If explicit YOE is missing: 'Junior/Entry' -> 0, 'Mid' -> 3, 'Senior' -> 5, 'Lead/Principal' -> 8. "
            "3) If 'X+ years', use X."
        )
    )
    
    junior_score: float = Field(
        ge=0.0, le=100.0,
        description=(
            "Score from 0.0 to 100.0 based STRICTLY on the JOB DESCRIPTION requirements (IGNORE CANDIDATE CV):\n"
            "100.0 = Job explicitly says 'Junior/No experience required' & 0 YOE.\n"
            "70.0-90.0 = 1-2 YOE required, standard tech stack.\n"
            "40.0-60.0 = 3 YOE or ambiguous mid-level requirements.\n"
            "1.0-3.0 = 4-5 YOE or 'Senior' title without lead duties.\n"
            "0.0 = Lead/Senior title, >5 YOE required, or niche legacy architecture."
        )
    )
    
    # UPGRADE: Replaced generic 'str' with strict Literal to enforce formatting
    work_model: Literal["ONSITE", "HYBRID", "REMOTE", "FLEXIBLE"] = Field(
        description="The strictly standardized work model for the role. Must be 'ONSITE', 'HYBRID', 'REMOTE', or 'FLEXIBLE'."
    )

    # UPGRADE: Prevents logical contradictions between YOE and Junior status
    @model_validator(mode='after')
    def validate_junior_logic(self) -> 'RoleClassification':
        if not self.is_junior and self.required_yoe == 0 and self.junior_score >= 70.0:
            raise ValueError("Contradiction: is_junior cannot be False if required_yoe is 0 and junior_score is high.")
        if self.is_junior and self.required_yoe >= 3:
            raise ValueError(f"Contradiction: Role cannot be 'junior' if required YOE is {self.required_yoe}.")
        return self
