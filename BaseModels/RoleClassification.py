from pydantic import BaseModel, Field

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
    
    work_model: str = Field(
        description="The work model for the role: 'Remote', 'On-site', 'Hybrid', or 'Flexible'."
    )
