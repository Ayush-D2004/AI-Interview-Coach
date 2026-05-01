import pytest
from pydantic import ValidationError
from core.schemas import SessionState, CandidateProfile, Dimensions

def test_session_state_initialization():
    state = SessionState(session_id="test-123")
    assert state.session_id == "test-123"
    assert state.status == "INTAKE"
    assert state.difficulty_level == "medium"
    assert len(state.turn_history) == 0

def test_candidate_profile_schema():
    profile = CandidateProfile(role="Engineer", focus_area="Backend")
    assert profile.role == "Engineer"
    assert profile.skills == []

def test_evaluator_json_validation():
    with pytest.raises(ValidationError):
        # 6 is out of bounds (ge=0, le=5)
        Dimensions(
            correctness=6, 
            specificity=3, 
            reasoning=4, 
            clarity=4, 
            role_relevance=4, 
            honesty_under_uncertainty=4, 
            communication=4
        )
