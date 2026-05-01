import json
import logging
from typing import Optional
from core.schemas import CandidateProfile, LLMMetrics
from core.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class ProfileAgent:
    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.system_prompt = PromptLoader().load_prompt("profile_agent")

    def run(
        self,
        target_role: str,
        focus_area: str,
        resume_text: str,
        url_summaries: str,
        background_snippet: str,
    ) -> tuple[Optional[CandidateProfile], LLMMetrics]:

        user_prompt = f"""Target Role: {target_role}
Focus Area: {focus_area}

Resume Text:
{resume_text or "(none provided)"}

URL Summaries:
{url_summaries or "(none provided)"}

Candidate Background:
{background_snippet or "(none provided)"}
"""
        result, metrics = self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            primary_provider="gemini_flash",
            fallback_providers=[],
            response_model=CandidateProfile,
        )

        if result is None:
            logger.error("Profile agent returned no result.")
            # Graceful fallback: minimal profile
            fallback = CandidateProfile(
                role=target_role,
                focus_area=focus_area,
            )
            return fallback, metrics

        return result, metrics
