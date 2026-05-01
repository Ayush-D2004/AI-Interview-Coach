from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class LLMMetrics(BaseModel):
    provider_used: str
    fallback_triggered: bool
    latency_ms: int
    retry_count: int
    structured_parse_success: bool
    error_message: Optional[str] = None

class CandidateProfile(BaseModel):
    role: str
    focus_area: str
    seniority_guess: Optional[str] = None
    experience_years_guess: Optional[int] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    avoid_topics: List[str] = Field(default_factory=list)

class Dimensions(BaseModel):
    correctness: int = Field(ge=0, le=5)
    specificity: int = Field(ge=0, le=5)
    reasoning: int = Field(ge=0, le=5)
    clarity: int = Field(ge=0, le=5)
    role_relevance: int = Field(ge=0, le=5)
    honesty_under_uncertainty: int = Field(ge=0, le=5)
    communication: int = Field(ge=0, le=5)

class EvaluatorJSON(BaseModel):
    turn_id: int
    score_overall: int = Field(ge=0, le=5)
    dimensions: Dimensions
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    followup_needed: bool
    followup_reason: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_spans: List[str] = Field(default_factory=list)
    recommended_next_difficulty: str

class StrategistDecision(BaseModel):
    next_question: str
    follow_up_type: str
    competency: str
    difficulty_adjustment: str
    stop_or_continue: str
    rationale: str

class InterviewTurn(BaseModel):
    turn_id: int
    question: str
    raw_audio_path: Optional[str] = None
    transcript: Optional[str] = None
    normalized_transcript: Optional[str] = None
    evaluator_json: Optional[EvaluatorJSON] = None
    strategist_decision: Optional[StrategistDecision] = None
    timestamps: Optional[Dict[str, float]] = None
    metrics: Optional[LLMMetrics] = None

class SessionStatus(str, Enum):
    INTAKE = "INTAKE"
    PROFILE_BUILD = "PROFILE_BUILD"
    INTERVIEW_PLAN = "INTERVIEW_PLAN"
    ASK_QUESTION = "ASK_QUESTION"
    STT_TRANSCRIBE = "STT_TRANSCRIBE"
    NORMALIZE_ANSWER = "NORMALIZE_ANSWER"
    EVALUATE_ANSWER = "EVALUATE_ANSWER"
    DECIDE_NEXT_STEP = "DECIDE_NEXT_STEP"
    COACH = "COACH"
    FINAL_REPORT = "FINAL_REPORT"
    ERROR = "ERROR"

class SessionState(BaseModel):
    session_id: str
    candidate_profile: Optional[CandidateProfile] = None
    turn_history: List[InterviewTurn] = Field(default_factory=list)
    difficulty_level: str = "medium"
    current_topic: Optional[str] = None
    completed_topics: List[str] = Field(default_factory=list)
    current_turn_index: int = 0
    status: SessionStatus = SessionStatus.INTAKE
    final_report_path: Optional[str] = None
