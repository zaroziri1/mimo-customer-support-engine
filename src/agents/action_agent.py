"""ActionAgent — execute automated fixes (refund, reset, config change, account unlock)."""
import json
import logging
from src.agents.base_agent import BaseAgent
from src.database import insert_action, update_action

logger = logging.getLogger(__name__)

# Simulated action handlers
ACTION_HANDLERS = {
    "refund": lambda details: {"status": "completed", "refund_id": "REF-2024-001", "amount": details.get("amount", 0)},
    "password_reset": lambda details: {"status": "completed", "reset_link_sent": True},
    "account_unlock": lambda details: {"status": "completed", "account_status": "unlocked"},
    "config_change": lambda details: {"status": "completed", "setting": details.get("setting"), "new_value": details.get("value")},
    "credit_adjustment": lambda details: {"status": "completed", "credit_applied": details.get("amount", 0)},
    "shipping_resend": lambda details: {"status": "completed", "new_tracking": "TRK-NEW-001"},
}


class ActionAgent(BaseAgent):
    def __init__(self):
        super().__init__("action")

    async def process(self, data: dict) -> dict:
        reasoning = data.get("reasoning", {})
        recommended = reasoning.get("recommended_actions", [])
        ticket_id = data.get("id")

        results = []
        for action_desc in recommended:
            action_type = self._classify_action(action_desc)
            if action_type and action_type in ACTION_HANDLERS:
                action_id = insert_action(ticket_id, action_type, json.dumps({"description": action_desc}), self.name)
                handler = ACTION_HANDLERS[action_type]
                result = handler({"description": action_desc})
                update_action(action_id, result["status"], json.dumps(result))
                results.append({
                    "action_id": action_id,
                    "type": action_type,
                    "status": result["status"],
                    "details": result,
                })

        return {"actions_executed": len(results), "results": results}

    def _classify_action(self, action_desc: str) -> str:
        desc_lower = action_desc.lower()
        if "refund" in desc_lower:
            return "refund"
        elif "reset" in desc_lower and "password" in desc_lower:
            return "password_reset"
        elif "unlock" in desc_lower:
            return "account_unlock"
        elif "config" in desc_lower or "setting" in desc_lower:
            return "config_change"
        elif "credit" in desc_lower:
            return "credit_adjustment"
        elif "reship" in desc_lower or "resend" in desc_lower or "shipping" in desc_lower:
            return "shipping_resend"
        return None
