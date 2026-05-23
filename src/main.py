"""MiMo Customer Support Engine — FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.kernel import AgentKernel
from src.database import init_db
from src.api.routes import router
from src.api.websocket import websocket_dashboard
from src.agents.triage_agent import TriageAgent
from src.agents.search_agent import SearchAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.action_agent import ActionAgent
from src.agents.escalation_agent import EscalationAgent
from src.agents.response_agent import ResponseAgent
from src.agents.learn_agent import LearnAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

kernel = AgentKernel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info("Initializing MiMo Customer Support Engine...")
    init_db()

    # Register all agents
    kernel.register_agent("triage", TriageAgent())
    kernel.register_agent("search", SearchAgent())
    kernel.register_agent("reasoning", ReasoningAgent())
    kernel.register_agent("action", ActionAgent())
    kernel.register_agent("escalation", EscalationAgent())
    kernel.register_agent("response", ResponseAgent())
    kernel.register_agent("learn", LearnAgent())

    await kernel.start()
    logger.info("All agents initialized. Engine ready.")
    yield
    await kernel.stop()
    logger.info("MiMo Customer Support Engine shut down.")


app = FastAPI(
    title="MiMo Customer Support Engine",
    description="Multi-agent AI customer support powered by MiMo v2.5 Pro",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount routes
app.include_router(router)

# WebSocket
app.add_api_websocket_route("/ws/dashboard", websocket_dashboard)

# Templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the real-time dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "healthy", "agents": kernel.get_stats()}
