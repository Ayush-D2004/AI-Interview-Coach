import os
import json
import logging
from typing import Dict, Any, Optional
from core.schemas import SessionState

logger = logging.getLogger(__name__)

class SessionStore:
    def __init__(self, storage_dir: str = "data/sessions"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.cache: Dict[str, Any] = {}
        
    def get_session_dir(self, session_id: str) -> str:
        s_dir = os.path.join(self.storage_dir, session_id)
        os.makedirs(s_dir, exist_ok=True)
        return s_dir

    def save_state(self, state: SessionState):
        s_dir = self.get_session_dir(state.session_id)
        filepath = os.path.join(s_dir, "state.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error saving session state: {e}")

    def load_state(self, session_id: str) -> Optional[SessionState]:
        filepath = os.path.join(self.get_session_dir(session_id), "state.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return SessionState.model_validate(data)
            except Exception as e:
                logger.error(f"Error loading session state: {e}")
        return None

    def log_metrics(self, session_id: str, turn_id: int, agent_name: str, metrics: Any):
        s_dir = self.get_session_dir(session_id)
        filepath = os.path.join(s_dir, "metrics.jsonl")
        log_entry = {
            "turn_id": turn_id,
            "agent": agent_name,
            "metrics": metrics.model_dump() if hasattr(metrics, "model_dump") else metrics
        }
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")

    # Basic caching mechanism for LLM responses
    def get_cache(self, cache_key: str) -> Optional[Any]:
        return self.cache.get(cache_key)

    def set_cache(self, cache_key: str, value: Any):
        self.cache[cache_key] = value
