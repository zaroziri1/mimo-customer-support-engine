"""ResponseAgent — generate contextual, empathetic reply."""
import logging
from src.agents.base_agent import BaseAgent
from src.mimo.client import mimo_chat
from src.database import insert_response

logger = logging.getLogger(__name__)

RESPONSE_PROMPT = """You are a professional, empathetic customer support agent. Generate a helpful response for this customer.

Customer's Issue:
Subject: {subject}
Body: {body}
Category: {category}
Sentiment: {sentiment}

Root Cause Analysis:
{reasoning}

Actions Taken:
{actions}

Knowledge Base References:
{kb_refs}

Guidelines:
- Be empathetic and acknowledge the customer's frustration
- Be specific about what was found and what actions were taken
- Provide clear next steps if the issue isn't fully resolved
- Use professional but warm language
- Keep the response concise but thorough
"""


class ResponseAgent(BaseAgent):
    def __init__(self):
        super().__init__("response")

    async def process(self, data: dict) -> dict:
        reasoning = data.get("reasoning", {})
        action_result = data.get("action_result", {})
        search_results = data.get("search_results", [])

        kb_refs = "\n".join(
            f"- {r.get('title', 'N/A')}" for r in search_results[:3]
        ) if search_results else "No specific references."

        actions_text = "No automated actions taken."
        if action_result and isinstance(action_result, dict):
            results = action_result.get("results", [])
            if results:
                actions_text = "\n".join(
                    f"- {r['type']}: {r['status']}" for r in results
                )

        reasoning_text = "Standard troubleshooting applied."
        if reasoning and isinstance(reasoning, dict):
            reasoning_text = (
                f"Root cause: {reasoning.get('root_cause', 'Under investigation')}\n"
                f"Confidence: {reasoning.get('confidence', 'N/A')}"
            )

        prompt = RESPONSE_PROMPT.format(
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            category=data.get("category", "general"),
            sentiment=data.get("sentiment", 0.0),
            reasoning=reasoning_text,
            actions=actions_text,
            kb_refs=kb_refs,
        )

        response_text = await mimo_chat(prompt, max_tokens=800)

        # Determine confidence based on reasoning agent's confidence
        confidence = reasoning.get("confidence", 0.7) if isinstance(reasoning, dict) else 0.7

        ticket_id = data.get("id")
        if ticket_id:
            insert_response(ticket_id, self.name, response_text, confidence)

        return {
            "response_text": response_text,
            "confidence": confidence,
            "agent": self.name,
        }
