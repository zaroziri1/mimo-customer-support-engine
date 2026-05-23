"""TriageAgent — classify ticket urgency, category, sentiment, language."""
import json
import logging
from src.agents.base_agent import BaseAgent
from src.mimo.client import mimo_chat

logger = logging.getLogger(__name__)

TRIAGE_PROMPT = """You are a customer support triage agent. Analyze the following ticket and return a JSON object with:
- "urgency": one of "low", "medium", "high", "critical"
- "category": one of "billing", "technical", "account", "shipping", "product", "security", "general", "complaint"
- "sentiment": a float from -1.0 (very negative) to 1.0 (very positive)
- "language": ISO 639-1 language code (e.g., "en", "es", "fr")
- "priority_score": float 0.0-1.0 based on urgency and sentiment
- "summary": one-line summary of the issue

Return ONLY valid JSON, no other text.

Ticket Subject: {subject}
Ticket Body: {body}
Customer ID: {customer_id}
"""


class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__("triage")

    async def process(self, data: dict) -> dict:
        prompt = TRIAGE_PROMPT.format(
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            customer_id=data.get("customer_id", "unknown"),
        )

        response = await mimo_chat(prompt)
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {
                    "urgency": "medium",
                    "category": "general",
                    "sentiment": 0.0,
                    "language": "en",
                    "priority_score": 0.5,
                    "summary": "Unable to auto-triage",
                }
        return result
