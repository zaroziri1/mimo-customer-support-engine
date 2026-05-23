"""Base agent class for all support agents."""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the support engine."""

    def __init__(self, name: str):
        self.name = name
        self.initialized = False
        self._process_count = 0
        self._error_count = 0

    async def initialize(self):
        """Initialize the agent. Override for custom setup."""
        self.initialized = True
        logger.info(f"Agent {self.name} initialized")

    async def shutdown(self):
        """Graceful shutdown. Override for cleanup."""
        self.initialized = False
        logger.info(f"Agent {self.name} shut down")

    @abstractmethod
    async def process(self, data: dict) -> Any:
        """Process input data and return results."""
        pass

    async def safe_process(self, data: dict) -> dict:
        """Process with error handling and metrics."""
        try:
            self._process_count += 1
            result = await self.process(data)
            return {"success": True, "result": result, "agent": self.name}
        except Exception as e:
            self._error_count += 1
            logger.error(f"Agent {self.name} error: {e}")
            return {"success": False, "error": str(e), "agent": self.name}

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "initialized": self.initialized,
            "process_count": self._process_count,
            "error_count": self._error_count,
        }
