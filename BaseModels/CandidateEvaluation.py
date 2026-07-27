import re
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

class CandidateEvaluation(BaseModel):
    """Universal Candidate vs. Job Description Evaluation."""

    evaluation_reasoning: str = Field(
        description=(
            "Step-by-step thinking:\n"
            "1) Identify the Job's Primary Daily Duty.\n"
            "2) Compare against Candidate's Core Disciplines.\n"
            "3) Separate Core Domain match/disconnect from Secondary Tool gaps.\n"
            "4) Assign flags and rank."
        )
    )

    has_language_dealbreaker: bool = Field(
        description="MUST BE TRUE ONLY IF the role strictly requires a spoken human language the candidate lacks."
    )

    has_yoe_dealbreaker: bool = Field(
        default=False,
        description="MUST BE TRUE ONLY IF the role is strictly Mid/Senior/Lead AND candidate has severely insufficient YOE."
    )

    has_stack_domain_dealbreaker: bool = Field(
        description=(
            "MUST BE TRUE IF candidate lacks the core primary discipline required for the job's main daily duties (e.g., lacking GTK+/Qt/C++ for a Linux Desktop GUI role).\n"
            "MUST BE FALSE IF candidate covers the primary daily discipline, even if secondary tools or frameworks are missing."
        )
    )

    missing_language: Optional[str] = Field(
        default=None,
        description=(
            "If has_language_dealbreaker is True, state the exact missing spoken language (e.g., 'French', 'German C1', 'Dutch'). "
            "Leave None or empty if no language dealbreaker exists."
        )
    )

    has_critical_dealbreakers: bool = Field(
        default=False,
        description="Auto-computed in code based on Language and YOE dealbreakers."
    )

    cv_match_rank: Literal["Unfit", "Borderline", "Fit"] = Field(
        description=(
            "- 'Fit': Matches primary domain, YOE, and core stack with minimal gaps.\n"
            "- 'Borderline': Strong primary domain match, but missing secondary/peripheral tools or minor stack items.\n"
            "- 'Unfit': Active dealbreaker in Language, YOE, or Primary Macro Domain."
        )
    )

    stack_gap: List[str] = Field(
        description="List of technologies or tools requested in the JD that are missing from candidate profile."
    )

    # --- 1. MANDATORY SEPARATE FIELDS (FORCES THE LLM TO WRITE BOTH) ---
    macro_domain_assessment: str = Field(
        description=(
            "MUST START WITH 'On a macro domain level, ...'. "
            "Explicitly compare the candidate's core engineering discipline (e.g., Java Backend / Cloud) "
            "against the job's main daily duties (e.g., building Linux Desktop GUI apps or Integration APIs)."
        )
    )

    specific_tooling_gaps: str = Field(
        description=(
            "MUST START WITH 'Regarding specific tooling, ...'. "
            "Detail the specific secondary frameworks, libraries, vendor tools, or nice-to-have items missing."
        )
    )

    # --- 2. AUTO-ASSEMBLED FIELD (NO LLM HALLUCINATION) ---
    cv_match_reasons: str = Field(
        default="",
        description="Auto-assembled in Python code from the two fields above."
    )

    @model_validator(mode="after")
    def enforce_universal_logic(self) -> "CandidateEvaluation":
        # 1. Sync Critical Dealbreakers
        self.has_critical_dealbreakers = bool(
            self.has_language_dealbreaker or self.has_yoe_dealbreaker
        )

        # 2. Prevent Cloud Vendor Mismatches (AWS vs Azure) from triggering Stack Dealbreaker
        azure_aws_keywords = ["azure", ".net", "c#", "service bus", "logic apps", "power apps"]
        reason_lower = (self.macro_domain_assessment + " " + self.specific_tooling_gaps).lower()
        
        if self.has_stack_domain_dealbreaker and not self.has_critical_dealbreakers:
            if any(kw in reason_lower for kw in azure_aws_keywords):
                # Force stack dealbreaker to False since AWS/Cloud backend transfers to Azure/Cloud backend
                self.has_stack_domain_dealbreaker = False

        # 3. DYNAMICALLY INJECT MISSING LANGUAGE INTO MACRO ASSESSMENT
        if self.has_language_dealbreaker:
            lang_name = self.missing_language if self.missing_language else "required spoken language"
            
            # Preserve technical fit, but state the explicit missing language
            self.macro_domain_assessment = (
                f"On a macro domain level, the candidate's core background in Backend Engineering, Distributed Systems, "
                f"and Cloud Infrastructure aligns with the core technical domain. However, the role strictly requires mandatory "
                f"fluency in {lang_name}, which is missing on the candidate's profile."
            )

        # 4. Final Rank Alignment
        if self.has_critical_dealbreakers or self.has_stack_domain_dealbreaker:
            self.cv_match_rank = "Unfit"
        else:
            if self.cv_match_rank == "Unfit":
                self.cv_match_rank = "Borderline" if len(self.stack_gap) > 0 else "Fit"

        # 5. Assemble final cv_match_reasons
        flag_summary = (
            f" [Dealbreakers -> Language: {self.has_language_dealbreaker}, "
            f"YOE: {self.has_yoe_dealbreaker}, "
            f"Stack/Domain: {self.has_stack_domain_dealbreaker}, "
            f"Critical: {self.has_critical_dealbreakers}]"
        )
        
        self.cv_match_reasons = (
            f"{self.macro_domain_assessment.strip()}\n\n"
            f"{self.specific_tooling_gaps.strip()}"
            f"{flag_summary}"
        )

        return self

