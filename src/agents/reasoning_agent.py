"""ReasoningAgent — MiMo LLM for complex troubleshooting, root cause analysis."""
import json
import logging
from src.agents.base_agent import BaseAgent
from src.mimo.client import mimo_chat

logger = logging.getLogger(__name__)

REASONING_PROMPT = """You are an expert customer support reasoning agent. Analyze this support ticket and provide:
- "root_cause": identified root cause of the issue
- "diagnosis_steps": list of diagnostic steps taken
- "recommended_actions": list of specific actions to resolve the issue
- "confidence": float 0.0-1.0 in your diagnosis
- "complexity": "simple", "moderate", or "complex"
- "estimated_resolution_time": e.g., "5 minutes", "1 hour", "24 hours"

Return ONLY valid JSON.

Ticket:
Subject: {subject}
Body: {body}
Category: {category}
Urgency: {urgency}

Related Knowledge Base Articles:
{kb_articles}
"""


class ReasoningAgent(BaseAgent):
    def __init__(self):
        super().__init__("reasoning")

    async def process(self, data: dict) -> dict:
        search_results = data.get("search_results", [])
        kb_text = "\n".join(
            f"- {r.get('title', 'N/A')}: {r.get('content', '')[:200]}"
            for r in search_results[:3]
        ) if search_results else "No relevant articles found."

        prompt = REASONING_PROMPT.format(
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            category=data.get("category", "general"),
            urgency=data.get("urgency", "medium"),
            kb_articles=kb_text,
        )

        response = await mimo_chat(prompt, max_tokens=1000)
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {
                    "root_cause": "Unable to determine automatically",
                    "diagnosis_steps": ["Manual review required"],
                    "recommended_actions": ["Escalate to human agent"],
                    "confidence": 0.3,
                    "complexity": "complex",
                    "estimated_resolution_time": "unknown",
                }
        return result
