"""SearchAgent — search knowledge base, past tickets, documentation."""
import logging
from src.agents.base_agent import BaseAgent
from src.database import search_knowledge_base, get_tickets

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("search")

    async def process(self, data: dict) -> list:
        query = data.get("subject", "") + " " + data.get("body", "")
        category = data.get("category")

        # Search knowledge base
        kb_results = search_knowledge_base(query[:200], category=category, limit=5)

        # Search past resolved tickets with similar issues
        past_tickets = get_tickets(status="resolved", limit=20)
        relevant_past = []
        query_lower = query.lower()
        for t in past_tickets:
            if any(word in t.get("body", "").lower() or word in t.get("subject", "").lower()
                   for word in query_lower.split()[:5]):
                relevant_past.append({
                    "id": t["id"],
                    "subject": t["subject"],
                    "category": t["category"],
                    "match_type": "past_ticket",
                })

        results = []
        for kb in kb_results:
            results.append({
                "id": kb["id"],
                "title": kb["title"],
                "content": kb["content"][:500],
                "category": kb["category"],
                "relevance_score": kb["relevance_score"],
                "match_type": "knowledge_base",
            })
        results.extend(relevant_past[:3])

        return results
