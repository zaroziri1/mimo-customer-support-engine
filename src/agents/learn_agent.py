"""LearnAgent — feedback loop from resolved tickets, improve future responses."""
import json
import logging
from src.agents.base_agent import BaseAgent
from src.database import insert_learning, record_metric

logger = logging.getLogger(__name__)


class LearnAgent(BaseAgent):
    def __init__(self):
        super().__init__("learn")

    async def process(self, data: dict) -> dict:
        ticket_id = data.get("id")
        category = data.get("category", "general")
        response = data.get("response", {})
        pipeline_results = data.get("pipeline_results", {})
        reasoning = pipeline_results.get("reasoning", {})

        # Extract pattern and solution from the pipeline
        pattern = self._extract_pattern(data)
        solution = self._extract_solution(response, pipeline_results)
        effectiveness = self._estimate_effectiveness(pipeline_results)

        # Store learning
        if pattern and solution:
            insert_learning(
                ticket_id, pattern, solution,
                effectiveness, category
            )

        # Record metrics
        if reasoning and isinstance(reasoning, dict):
            confidence = reasoning.get("confidence", 0)
            record_metric("reasoning_confidence", confidence, "gauge", "reasoning")

        triage = pipeline_results.get("triage", {})
        if triage and isinstance(triage, dict):
            record_metric("sentiment_score", triage.get("sentiment", 0), "gauge", "triage")
            record_metric("priority_score", triage.get("priority_score", 0), "gauge", "triage")

        if response and isinstance(response, dict):
            record_metric("response_confidence", response.get("confidence", 0), "gauge", "response")

        return {
            "learned": bool(pattern and solution),
            "pattern": pattern,
            "effectiveness": effectiveness,
        }

    def _extract_pattern(self, data: dict) -> str:
        subject = data.get("subject", "")
        body = data.get("body", "")[:200]
        category = data.get("category", "general")
        return f"[{category}] {subject}: {body}"

    def _extract_solution(self, response: dict, pipeline_results: dict) -> str:
        if isinstance(response, dict):
            return response.get("response_text", "")[:500]
        return ""

    def _estimate_effectiveness(self, pipeline_results: dict) -> float:
        reasoning = pipeline_results.get("reasoning", {})
        if isinstance(reasoning, dict):
            return reasoning.get("confidence", 0.5)
        return 0.5
