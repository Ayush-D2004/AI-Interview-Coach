import os
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        
    def load_prompt(self, agent_name: str) -> str:
        filepath = os.path.join(self.prompts_dir, f"{agent_name}.md")
        if not os.path.exists(filepath):
            logger.warning(f"Prompt file {filepath} not found.")
            return ""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
