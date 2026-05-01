import logging
from typing import Optional
from core.schemas import CandidateProfile, InterviewTurn, LLMMetrics
from core.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class CoachAgent:
    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.system_prompt = PromptLoader().load_prompt("coach_agent")

    def run(
        self,
        candidate_profile: CandidateProfile,
        target_role: str,
        focus_area: str,
        turn_history: list[InterviewTurn],
    ) -> tuple[Optional[str], LLMMetrics]:

        if not turn_history:
            logger.warning("No turns in history. Coach will produce minimal report.")

        # Aggregate scores
        scores = [t.evaluator_json.score_overall for t in turn_history if t.evaluator_json]
        session_avg = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Build per-turn summary for the prompt
        turn_summaries = []
        for turn in turn_history:
            ev = turn.evaluator_json
            if ev:
                turn_summaries.append(
                    f"Turn {turn.turn_id}:\n"
                    f"  Question: {turn.question}\n"
                    f"  Answer: {turn.normalized_transcript or turn.transcript or '(no response)'}\n"
                    f"  Overall Score: {ev.score_overall}/5\n"
                    f"  Strengths: {'; '.join(ev.strengths)}\n"
                    f"  Gaps: {'; '.join(ev.gaps)}\n"
                    f"  Misconceptions: {'; '.join(ev.misconceptions)}\n"
                )
            else:
                turn_summaries.append(
                    f"Turn {turn.turn_id}:\n"
                    f"  Question: {turn.question}\n"
                    f"  (No evaluation data available)\n"
                )

        user_prompt = f"""Target Role: {target_role}
Focus Area: {focus_area}
Candidate Summary: {candidate_profile.summary or 'Not available'}
Session Average Score: {session_avg}/5
Total Turns Completed: {len(turn_history)}

Candidate Strengths (from profile): {', '.join(candidate_profile.strengths)}
Candidate Gaps (from profile): {', '.join(candidate_profile.gaps)}

--- Full Session Record ---
{chr(10).join(turn_summaries)}
"""

        result, metrics = self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            primary_provider="gemini_flash",
            fallback_providers=["groq"],
        )

        if result is None:
            logger.error("Coach agent returned no result.")
            fallback_md = (
                f"# Mock Interview Coaching Report\n\n"
                f"## Summary\nThe coaching report could not be generated due to a system error.\n\n"
                f"## Session Average Score\n{session_avg}/5 across {len(turn_history)} turns.\n"
            )
            return fallback_md, metrics

        return result, metrics
