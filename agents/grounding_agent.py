import os
import requests
import logging
from typing import Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GroundingResult:
    role_expectations: list[str]
    common_interview_topics: list[str]
    company_signals: list[str]
    difficulty_benchmark: str
    sources: list[str]
    confidence: float
    notes: Optional[str]

class GroundingAgent:
    def __init__(self):
        self.api_key = os.environ.get("BRAVE_API_KEY")
        self.search_url = "https://api.search.brave.com/res/v1/web/search"

    def _search(self, query: str, num_results: int = 5) -> list[dict]:
        if not self.api_key:
            logger.warning("BRAVE_API_KEY not set. Grounding agent will return empty results.")
            return []
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {"q": query, "count": num_results}
        try:
            response = requests.get(self.search_url, headers=headers, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()
            results = data.get("web", {}).get("results", [])
            return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")} for r in results]
        except Exception as e:
            logger.error(f"Brave search error: {e}")
            return []

    def run(self, target_role: str, focus_area: str, company_name: Optional[str], llm_manager) -> tuple[Optional[GroundingResult], Optional[Any]]:
        from core.prompt_loader import PromptLoader
        from core.schemas import LLMMetrics

        system_prompt = PromptLoader().load_prompt("grounding_agent")

        # Build search queries
        query_role = f"{target_role} interview questions"
        query_company = f"{company_name} {target_role} interview process" if company_name else None

        search_results = self._search(query_role)
        if query_company:
            search_results += self._search(query_company, num_results=3)

        if not search_results:
            logger.warning("No search results. Returning minimal grounding.")
            res = GroundingResult(
                role_expectations=[],
                common_interview_topics=[],
                company_signals=[],
                difficulty_benchmark="mid",
                sources=[],
                confidence=0.0,
                notes="No search results were available.",
            )
            return res, None

        user_prompt = f"""Target Role: {target_role}
Focus Area: {focus_area}
Company: {company_name or "Not specified"}

Search Results:
{self._format_results(search_results)}
"""

        # We use a raw text call here since GroundingResult is a dataclass, not Pydantic
        response_text, metrics = llm_manager.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            primary_provider="gemini_flash",
            fallback_providers=[],
        )

        if not response_text:
            return None, metrics

        import json
        try:
            data = json.loads(response_text)
            res = GroundingResult(
                role_expectations=data.get("role_expectations", []),
                common_interview_topics=data.get("common_interview_topics", []),
                company_signals=data.get("company_signals", []),
                difficulty_benchmark=data.get("difficulty_benchmark", "mid"),
                sources=data.get("sources", []),
                confidence=data.get("confidence", 0.5),
                notes=data.get("notes"),
            )
            return res, metrics
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse grounding output: {e}")
            return None, metrics

    def _format_results(self, results: list[dict]) -> str:
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r['title']}]({r['url']})\n   {r['snippet']}")
        return "\n".join(lines)
