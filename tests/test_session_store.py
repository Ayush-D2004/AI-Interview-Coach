import pytest
import os
import shutil
from core.session_store import SessionStore
from core.schemas import SessionState

def test_session_store():
    test_dir = "test_sessions_dir"
    store = SessionStore(storage_dir=test_dir)
    
    # Create and save
    state = SessionState(session_id="test_session")
    store.save_state(state)
    
    # Load
    loaded = store.load_state("test_session")
    assert loaded is not None
    assert loaded.session_id == "test_session"
    assert loaded.status == "INTAKE"
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
