from typing import List, Literal
from pydantic import BaseModel, Field, model_validator

class CandidateEvaluation(BaseModel):
    """Direct comparison between candidate profile and JD requirements."""
    
    has_language_dealbreaker: bool = Field(
        description=(
            "MUST BE TRUE ONLY IF the job explicitly requires a mandatory language proficiency that the candidate lacks "
            "(e.g., 'Must speak fluent French' or 'German C1 required').\n"
            "MUST BE FALSE if the language is described as 'a plus', 'nice to have', 'optional', or if the working language is English."
        )
    )

    has_yoe_dealbreaker: bool = Field(
        default=False,
        description=(
            "MUST BE FALSE if the role is Junior, Entry-Level, Graduate, or Intern "
            "(even if metadata incorrectly flags it as Mid/Senior).\n"
            "MUST BE FALSE if there are conflicting seniority signals (e.g., 'Graduate' in title but 'Mid-Senior' in metadata).\n"
            "MUST BE TRUE ONLY IF all of the following are met:\n"
            "1) The role is strictly Mid, Senior, Lead, or Principal.\n"
            "2) The required YOE is explicitly far higher than candidate's experience (e.g., candidate has 1 YOE applying for a 5-7+ YOE Senior role).\n"
            "When in doubt or if data is contradictory, default to FALSE."
        )
    )


    has_stack_domain_dealbreaker: bool = Field(
        description=(
            "MUST BE TRUE ONLY IF there is an absolute macro-domain disconnect "
            "(e.g., pure Frontend applying for Senior Data Engineer/ML) where the candidate "
            "lacks all primary core engineering principles for the role.\n"
            "MUST BE FALSE if the candidate works within the same broad engineering domain, "
            "even if they lack specific cloud services, databases, frameworks, Git providers, or project management tools.\n"
            "Treat specific vendor tools, cloud services, and secondary stack variances as transferable skills, NOT dealbreakers."
        )
    )


    has_critical_dealbreakers: bool = Field(
        default=False,
        description=(
            "Combined master flag. Set to True IF ANY of has_language_dealbreaker or has_yoe_dealbreaker, are True. "
            "But has_stack_domain_dealbreaker alone does NOT trigger this flag unless it is accompanied by one of the other two dealbreakers."
        ),
    )

    cv_match_rank: Literal["Unfit", "Borderline", "Fit"] = Field(
        description=(
            "STRICT EVALUATION RULES:\n"
            "- IF has_critical_dealbreakers is True -> MUST BE 'Unfit'. NO EXCEPTIONS.\n"
            "- Select 'Fit' ONLY if candidate meets the core domain, required YOE, AND all primary technologies in the stack.\n"
            "- Select 'Borderline' if candidate has strong domain fit (e.g., Backend or Fullstack background) but lacks 1 or more specific technologies in the required stack (e.g., strong Java/Spring backend but missing Angular frontend).\n"
           # "- Select 'Borderline' if there are inconsistencies in the proposal's YOE (like telling 'Graduate', 'Entry Level' or 'Junior' in on place and other level on another) or skill claims that require further verification).\n"
            "- Select 'Unfit' ONLY if has_critical_dealbreakers is True."
        )
    )

    stack_gap: List[str] = Field(
        description="List of required technologies/tools mentioned in JD that are missing in Candidate Profile."
    )
    
    cv_match_reasons: str = Field(
        min_length=10,
        description=(
            "Detailed plain text explanation supporting the assigned cv_match_rank. "
            "MUST include a clear breakdown of the dealbreaker status flags "
            "(Language, YOE, Stack Domain, Critical Dealbreaker)."
        ),
    )

    # UPGRADE: Mechanically enforces the dealbreaker rule so the LLM cannot violate it
    @model_validator(mode="after")
    def enforce_dealbreaker_logic(self) -> "CandidateEvaluation":
        # 1. Sync master flag
        self.has_critical_dealbreakers = (
            self.has_language_dealbreaker
            or self.has_yoe_dealbreaker
            or self.has_stack_domain_dealbreaker
        )

        # 2. Enforce rank alignment
        if self.has_critical_dealbreakers:
            self.cv_match_rank = "Unfit"

        # 3. Mechanically append flag values to cv_match_reasons to ensure exact logging
        flag_summary = (
            f" [Dealbreakers -> Language: {self.has_language_dealbreaker}, "
            f"YOE: {self.has_yoe_dealbreaker}, "
            f"Stack/Domain: {self.has_stack_domain_dealbreaker}, "
            f"Critical: {self.has_critical_dealbreakers}]"
        )

        if flag_summary not in self.cv_match_reasons:
            self.cv_match_reasons = (
                self.cv_match_reasons.strip() + flag_summary
            )

        return self
