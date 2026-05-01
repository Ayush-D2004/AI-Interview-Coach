import logging
from typing import Optional

from core.schemas import SessionState, SessionStatus, InterviewTurn
from core.session_store import SessionStore
from core.llm_clients import LLMManager
from agents.profile_agent import ProfileAgent
from agents.strategist_agent import StrategistAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.coach_agent import CoachAgent
from agents.grounding_agent import GroundingAgent

logger = logging.getLogger(__name__)

class InterviewOrchestrator:
    def __init__(self, session_id: str, max_turns: int = 5):
        self.session_id = session_id
        self.max_turns = max_turns
        self.store = SessionStore()
        self.llm_manager = LLMManager()
        
        self.profile_agent = ProfileAgent(self.llm_manager)
        self.strategist_agent = StrategistAgent(self.llm_manager)
        self.evaluator_agent = EvaluatorAgent(self.llm_manager)
        self.coach_agent = CoachAgent(self.llm_manager)
        self.grounding_agent = GroundingAgent()
        
        loaded = self.store.load_state(session_id)
        if loaded:
            self.state = loaded
        else:
            self.state = SessionState(session_id=session_id)
            self.store.save_state(self.state)

    def process_intake(self, target_role: str, focus_area: str, resume_text: str, url_summaries: str, background_snippet: str):
        if self.state.status != SessionStatus.INTAKE:
            logger.warning(f"Invalid state transition from {self.state.status} to PROFILE_BUILD")
            return
            
        self.state.status = SessionStatus.PROFILE_BUILD
        self.store.save_state(self.state)
        
        profile, metrics = self.profile_agent.run(
            target_role=target_role,
            focus_area=focus_area,
            resume_text=resume_text,
            url_summaries=url_summaries,
            background_snippet=background_snippet
        )
        self.store.log_metrics(self.session_id, 0, "ProfileAgent", metrics)
        
        if profile:
            self.state.candidate_profile = profile
        
        # Defensive call to grounding agent
        grounding_result = self.grounding_agent.run(target_role, focus_area, None, self.llm_manager)
        if isinstance(grounding_result, tuple):
            grounding, g_metrics = grounding_result
        else:
            grounding, g_metrics = grounding_result, None
            
        if grounding:
            self.store.log_metrics(self.session_id, 0, "GroundingAgent", g_metrics)
            
        self.state.status = SessionStatus.INTERVIEW_PLAN
        self.store.save_state(self.state)

    def start_interview(self) -> str:
        if self.state.status != SessionStatus.INTERVIEW_PLAN:
            logger.warning(f"Invalid transition from {self.state.status} to ASK_QUESTION")
            return "Interview already started."
            
        return self._generate_next_question()

    def handle_answer(self, raw_transcript: str, normalized_transcript: Optional[str] = None) -> str:
        if self.state.status != SessionStatus.ASK_QUESTION:
            logger.error("Cannot handle answer unless waiting for one.")
            return "Invalid state."
            
        self.state.status = SessionStatus.EVALUATE_ANSWER
        self.store.save_state(self.state)
        
        current_turn = self.state.turn_history[-1]
        current_turn.transcript = raw_transcript
        current_turn.normalized_transcript = normalized_transcript or raw_transcript
        
        eval_json, eval_metrics = self.evaluator_agent.run(
            turn_id=current_turn.turn_id,
            question=current_turn.question,
            transcript=current_turn.transcript,
            normalized_transcript=current_turn.normalized_transcript,
            candidate_profile=self.state.candidate_profile,
            competency=self.state.current_topic or "general"
        )
        self.store.log_metrics(self.session_id, current_turn.turn_id, "EvaluatorAgent", eval_metrics)
        current_turn.evaluator_json = eval_json
        
        self.state.status = SessionStatus.DECIDE_NEXT_STEP
        self.store.save_state(self.state)
        
        turns_left = self.max_turns - len(self.state.turn_history)
        if turns_left <= 0:
            return self._finish_interview()
            
        decision, strat_metrics = self.strategist_agent.run(
            candidate_profile=self.state.candidate_profile,
            target_role=self.state.candidate_profile.role,
            focus_area=self.state.candidate_profile.focus_area,
            turn_history=self.state.turn_history,
            evaluator_outputs=[t.evaluator_json for t in self.state.turn_history if t.evaluator_json],
            current_difficulty=self.state.difficulty_level,
            turns_remaining=turns_left,
            completed_topics=self.state.completed_topics
        )
        self.store.log_metrics(self.session_id, current_turn.turn_id, "StrategistAgent", strat_metrics)
        current_turn.strategist_decision = decision
        
        if decision.stop_or_continue.lower() == "stop":
            return self._finish_interview()
            
        if decision.difficulty_adjustment == "increase" and self.state.difficulty_level != "expert":
            levels = ["easy", "medium", "hard", "expert"]
            self.state.difficulty_level = levels[levels.index(self.state.difficulty_level) + 1]
        elif decision.difficulty_adjustment == "decrease" and self.state.difficulty_level != "easy":
            levels = ["easy", "medium", "hard", "expert"]
            self.state.difficulty_level = levels[levels.index(self.state.difficulty_level) - 1]
            
        self.state.current_topic = decision.competency
        self.state.current_turn_index += 1
        
        new_turn = InterviewTurn(
            turn_id=self.state.current_turn_index,
            question=decision.next_question
        )
        self.state.turn_history.append(new_turn)
        
        self.state.status = SessionStatus.ASK_QUESTION
        self.store.save_state(self.state)
        return decision.next_question

    def _generate_next_question(self) -> str:
        turns_left = self.max_turns - len(self.state.turn_history)
        decision, metrics = self.strategist_agent.run(
            candidate_profile=self.state.candidate_profile,
            target_role=self.state.candidate_profile.role,
            focus_area=self.state.candidate_profile.focus_area,
            turn_history=self.state.turn_history,
            evaluator_outputs=[t.evaluator_json for t in self.state.turn_history if t.evaluator_json],
            current_difficulty=self.state.difficulty_level,
            turns_remaining=turns_left,
            completed_topics=self.state.completed_topics
        )
        self.store.log_metrics(self.session_id, self.state.current_turn_index + 1, "StrategistAgent", metrics)
        
        self.state.current_topic = decision.competency
        self.state.current_turn_index += 1
        
        new_turn = InterviewTurn(
            turn_id=self.state.current_turn_index,
            question=decision.next_question
        )
        self.state.turn_history.append(new_turn)
        
        self.state.status = SessionStatus.ASK_QUESTION
        self.store.save_state(self.state)
        return decision.next_question

    def _finish_interview(self) -> str:
        self.state.status = SessionStatus.COACH
        self.store.save_state(self.state)
        
        report_md, metrics = self.coach_agent.run(
            candidate_profile=self.state.candidate_profile,
            target_role=self.state.candidate_profile.role,
            focus_area=self.state.candidate_profile.focus_area,
            turn_history=self.state.turn_history
        )
        self.store.log_metrics(self.session_id, self.state.current_turn_index, "CoachAgent", metrics)
        
        import os
        s_dir = self.store.get_session_dir(self.session_id)
        report_path = os.path.join(s_dir, "report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
            
        self.state.final_report_path = report_path
        self.state.status = SessionStatus.FINAL_REPORT
        self.store.save_state(self.state)
        return "Interview complete. Report generated."
