import json
import logging
from typing import Optional
from core.schemas import CandidateProfile, EvaluatorJSON, LLMMetrics
from core.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.system_prompt = PromptLoader().load_prompt("evaluator_agent")

    def run(
        self,
        turn_id: int,
        question: str,
        transcript: str,
        normalized_transcript: Optional[str],
        candidate_profile: CandidateProfile,
        competency: str,
    ) -> tuple[Optional[EvaluatorJSON], LLMMetrics]:

        answer_text = normalized_transcript or transcript or ""

        if not answer_text.strip():
            logger.warning(f"Turn {turn_id}: Empty transcript. Returning zero score.")
            zero_eval = self._empty_eval(turn_id)
            from core.schemas import LLMMetrics as M
            return zero_eval, M(
                provider_used="none",
                fallback_triggered=False,
                latency_ms=0,
                retry_count=0,
                structured_parse_success=True,
            )

        user_prompt = f"""Turn ID: {turn_id}
Competency Being Tested: {competency}
Target Role: {candidate_profile.role}
Focus Area: {candidate_profile.focus_area}
Candidate Seniority: {candidate_profile.seniority_guess or 'unknown'}

Question Asked:
{question}

Candidate's Answer (transcript):
{answer_text}

Normalized Transcript Available: {'Yes' if normalized_transcript else 'No'}
"""

        result, metrics = self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            primary_provider="gemini_flash",
            fallback_providers=["groq"],
            response_model=EvaluatorJSON,
        )

        if result is None:
            logger.error(f"Evaluator agent returned no result for turn {turn_id}.")
            return self._empty_eval(turn_id), metrics

        return result, metrics

    def _empty_eval(self, turn_id: int) -> EvaluatorJSON:
        from core.schemas import Dimensions
        return EvaluatorJSON(
            turn_id=turn_id,
            score_overall=0,
            dimensions=Dimensions(
                correctness=0,
                specificity=0,
                reasoning=0,
                clarity=0,
                role_relevance=0,
                honesty_under_uncertainty=0,
                communication=0,
            ),
            strengths=[],
            gaps=["No answer was provided."],
            misconceptions=[],
            followup_needed=True,
            followup_reason="No answer was provided.",
            confidence=0.0,
            evidence_spans=[],
            recommended_next_difficulty="easy",
        )
