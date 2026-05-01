import json
import logging
from typing import Optional
from core.schemas import CandidateProfile, StrategistDecision, InterviewTurn, EvaluatorJSON, LLMMetrics
from core.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class StrategistAgent:
    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.system_prompt = PromptLoader().load_prompt("strategist_agent")

    def run(
        self,
        candidate_profile: CandidateProfile,
        target_role: str,
        focus_area: str,
        turn_history: list[InterviewTurn],
        evaluator_outputs: list[EvaluatorJSON],
        current_difficulty: str,
        turns_remaining: int,
        completed_topics: list[str],
    ) -> tuple[Optional[StrategistDecision], LLMMetrics]:

        # Summarize history for the prompt
        history_lines = []
        for turn in turn_history:
            score = turn.evaluator_json.score_overall if turn.evaluator_json else "N/A"
            history_lines.append(
                f"Turn {turn.turn_id}: Q={turn.question!r} | Score={score}/5 | Transcript={turn.normalized_transcript or '(none)'!r}"
            )

        eval_summary = []
        for ev in evaluator_outputs:
            eval_summary.append(
                f"Turn {ev.turn_id}: overall={ev.score_overall}/5, followup_needed={ev.followup_needed}, "
                f"recommended_difficulty={ev.recommended_next_difficulty}"
            )

        user_prompt = f"""Target Role: {target_role}
Focus Area: {focus_area}
Current Difficulty: {current_difficulty}
Turns Remaining: {turns_remaining}
Completed Topics: {', '.join(completed_topics) if completed_topics else 'None yet'}

Candidate Profile Summary:
- Seniority: {candidate_profile.seniority_guess}
- Skills: {', '.join(candidate_profile.skills[:10])}
- Strengths: {', '.join(candidate_profile.strengths)}
- Gaps: {', '.join(candidate_profile.gaps)}
- Avoid Topics: {', '.join(candidate_profile.avoid_topics)}

Turn History:
{chr(10).join(history_lines) if history_lines else 'No turns yet (this is the first question).'}

Evaluator Outputs:
{chr(10).join(eval_summary) if eval_summary else 'No evaluator data yet.'}
"""

        result, metrics = self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            primary_provider="gemini_flash",
            fallback_providers=["groq"],
            response_model=StrategistDecision,
        )

        if result is None:
            logger.error("Strategist agent returned no result.")
            fallback = StrategistDecision(
                next_question=f"Can you walk me through a recent project where you applied your {focus_area} skills?",
                follow_up_type="new_topic",
                competency=focus_area,
                difficulty_adjustment="maintain",
                stop_or_continue="continue",
                rationale="Fallback to safe opening question due to LLM failure.",
            )
            return fallback, metrics

        return result, metrics
