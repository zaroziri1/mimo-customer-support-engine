"""EscalationAgent — detect when human handoff needed, route to correct team."""
import logging
from src.agents.base_agent import BaseAgent
from src.database import insert_escalation
from src.config import ESCALATION_THRESHOLD

logger = logging.getLogger(__name__)

ESCALATION_RULES = {
    "legal": "legal_team",
    "lawsuit": "legal_team",
    "fraud": "security_team",
    "hacked": "security_team",
    "compromised": "security_team",
    "suicide": "crisis_team",
    "self-harm": "crisis_team",
    "vip": "vip_support",
    "enterprise": "enterprise_support",
}


class EscalationAgent(BaseAgent):
    def __init__(self):
        super().__init__("escalation")

    async def process(self, data: dict) -> dict:
        body = (data.get("body", "") + " " + data.get("subject", "")).lower()
        urgency = data.get("urgency", "medium")
        sentiment = data.get("sentiment", 0.0)
        category = data.get("category", "")
        ticket_id = data.get("id")

        reasons = []
        to_team = None

        # Check keyword-based rules
        for keyword, team in ESCALATION_RULES.items():
            if keyword in body:
                reasons.append(f"Keyword match: '{keyword}'")
                to_team = team
                break

        # Sentiment-based escalation
        if sentiment < -0.7 and not to_team:
            reasons.append(f"Very negative sentiment: {sentiment}")
            to_team = "senior_support"

        # Urgency-based escalation
        if urgency == "critical" and not to_team:
            reasons.append("Critical urgency ticket")
            to_team = "tier_2_support"

        # Low confidence escalation (from triage)
        if data.get("priority_score", 0) > 0.85 and not to_team:
            reasons.append(f"High priority score: {data.get('priority_score')}")
            to_team = "tier_2_support"

        should_escalate = len(reasons) > 0

        if should_escalate and ticket_id:
            insert_escalation(
                ticket_id, self.name, to_team,
                "; ".join(reasons), urgency
            )

        return {
            "escalate": should_escalate,
            "to_team": to_team,
            "reasons": reasons,
        }
