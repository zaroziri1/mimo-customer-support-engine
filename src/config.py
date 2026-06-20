"""Configuration for MiMo Customer Support Engine."""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "mimo_support.db"

# MiMo LLM Configuration
MIMO_API_ENDPOINT = os.getenv("MIMO_API_ENDPOINT")
MIMO_MODEL = os.getenv("MIMO_MODEL", "xmtp/mimo-v2.5-pro")
MIMO_API_KEY = os.getenv("MIMO_API_KEY")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Ticket categories
CATEGORIES = [
    "billing", "technical", "account", "shipping",
    "product", "security", "general", "complaint"
]

URGENCY_LEVELS = ["low", "medium", "high", "critical"]

# Agent configuration
AGENT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
ESCALATION_THRESHOLD = 0.7  # confidence threshold for auto-escalation
