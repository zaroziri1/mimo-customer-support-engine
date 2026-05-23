"""AgentKernel - lifecycle management for all agents."""
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentKernel:
    """Central orchestrator for agent lifecycle and coordination."""

    def __init__(self):
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.active_sessions: Dict[int, dict] = {}
        self.running = False
        self._pipeline_stats = {
            "tickets_processed": 0,
            "avg_processing_time": 0,
            "errors": 0,
        }

    def register_agent(self, name: str, agent: 'BaseAgent'):
        """Register an agent with the kernel."""
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")

    def get_agent(self, name: str) -> Optional['BaseAgent']:
        return self.agents.get(name)

    async def start(self):
        """Start all registered agents."""
        self.running = True
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                logger.info(f"Agent {name} initialized")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")

    async def stop(self):
        """Gracefully stop all agents."""
        self.running = False
        for name, agent in self.agents.items():
            try:
                await agent.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")

    async def process_ticket(self, ticket: dict) -> dict:
        """Full ticket processing pipeline through all agents."""
        start_time = datetime.now()
        session = {
            "ticket_id": ticket.get("id"),
            "started_at": start_time.isoformat(),
            "agent_chain": [],
            "results": {},
        }

        try:
            # Step 1: Triage
            triage = self.agents.get("triage")
            if triage:
                triage_result = await triage.process(ticket)
                session["agent_chain"].append("triage")
                session["results"]["triage"] = triage_result
                ticket.update(triage_result)

            # Step 2: Search knowledge base
            search = self.agents.get("search")
            search_results = []
            if search:
                search_results = await search.process(ticket)
                session["agent_chain"].append("search")
                session["results"]["search"] = search_results

            # Step 3: Check if escalation needed
            escalation = self.agents.get("escalation")
            if escalation:
                esc_result = await escalation.process({**ticket, "search_results": search_results})
                session["results"]["escalation"] = esc_result
                if esc_result.get("escalate"):
                    session["agent_chain"].append("escalation")
                    session["escalated"] = True
                    # Still generate a response even if escalated

            # Step 4: Reasoning (for complex issues)
            reasoning = self.agents.get("reasoning")
            reasoning_result = None
            if reasoning:
                reasoning_result = await reasoning.process({
                    **ticket, "search_results": search_results
                })
                session["agent_chain"].append("reasoning")
                session["results"]["reasoning"] = reasoning_result

            # Step 5: Actions
            action = self.agents.get("action")
            action_result = None
            if action and reasoning_result:
                action_result = await action.process({
                    **ticket, "reasoning": reasoning_result
                })
                session["agent_chain"].append("action")
                session["results"]["action"] = action_result

            # Step 6: Generate response
            response_agent = self.agents.get("response")
            final_response = None
            if response_agent:
                final_response = await response_agent.process({
                    **ticket,
                    "search_results": search_results,
                    "reasoning": reasoning_result,
                    "action_result": action_result,
                })
                session["agent_chain"].append("response")
                session["results"]["response"] = final_response

            # Step 7: Learn
            learn = self.agents.get("learn")
            if learn:
                await learn.process({
                    **ticket,
                    "response": final_response,
                    "pipeline_results": session["results"],
                })
                session["agent_chain"].append("learn")

            elapsed = (datetime.now() - start_time).total_seconds()
            session["completed_at"] = datetime.now().isoformat()
            session["processing_time"] = elapsed
            self._pipeline_stats["tickets_processed"] += 1
            n = self._pipeline_stats["tickets_processed"]
            old_avg = self._pipeline_stats["avg_processing_time"]
            self._pipeline_stats["avg_processing_time"] = old_avg + (elapsed - old_avg) / n

            return {
                "status": "completed",
                "response": final_response,
                "session": session,
                "processing_time": elapsed,
            }

        except Exception as e:
            logger.error(f"Pipeline error for ticket {ticket.get('id')}: {e}")
            self._pipeline_stats["errors"] += 1
            session["error"] = str(e)
            return {"status": "error", "error": str(e), "session": session}

    def get_stats(self) -> dict:
        return {
            "running": self.running,
            "registered_agents": list(self.agents.keys()),
            "active_sessions": len(self.active_sessions),
            **self._pipeline_stats,
        }
