# 🧠 MiMo Customer Support Engine

A multi-agent AI customer support system powered by **MiMo v2.5 Pro** LLM. Seven specialized agents coordinate through an AgentKernel to triage, investigate, resolve, and learn from customer support tickets in real-time.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application (main.py)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   AgentKernel (kernel.py)                  │  │
│  │           Lifecycle management & pipeline orchestration    │  │
│  └─────────┬─────────────────────────────────────────────────┘  │
│            │                                                    │
│  ┌─────────▼──────────────────────────────────────────────────┐ │
│  │              Agent Pipeline (7 Agents)                     │ │
│  │                                                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐            │ │
│  │  │ Triage   │→ │ Search   │→ │  Reasoning   │            │ │
│  │  │ Agent    │  │ Agent    │  │  Agent (LLM) │            │ │
│  │  └──────────┘  └──────────┘  └──────┬───────┘            │ │
│  │                                     │                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────▼───────┐            │ │
│  │  │Escalation│← │ Response │← │   Action     │            │ │
│  │  │ Agent    │  │ Agent    │  │   Agent      │            │ │
│  │  └──────────┘  └──────────┘  └──────────────┘            │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────┐         │ │
│  │  │          Learn Agent (Feedback Loop)          │         │ │
│  │  └──────────────────────────────────────────────┘         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   SQLite     │  │  MiMo LLM   │  │  WebSocket Dashboard  │  │
│  │   (WAL)      │  │  Client      │  │  (Real-time UI)       │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Role |
|---|---|
| **TriageAgent** | Classify ticket urgency, category, sentiment, language |
| **SearchAgent** | Search knowledge base, past tickets, documentation |
| **ReasoningAgent** | MiMo LLM for complex troubleshooting & root cause analysis |
| **ActionAgent** | Execute automated fixes (refund, reset, unlock, config) |
| **EscalationAgent** | Detect when human handoff is needed, route to correct team |
| **ResponseAgent** | Generate contextual, empathetic reply |
| **LearnAgent** | Feedback loop from resolved tickets, improve future responses |

## File Structure

```
mimo-customer-support-engine/
├── README.md
├── requirements.txt
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── kernel.py            # AgentKernel lifecycle management
│   ├── database.py          # SQLite WAL mode, all table operations
│   ├── config.py            # Configuration constants
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Abstract base class for all agents
│   │   ├── triage_agent.py  # Ticket classification & prioritization
│   │   ├── search_agent.py  # Knowledge base & past ticket search
│   │   ├── reasoning_agent.py  # MiMo LLM root cause analysis
│   │   ├── action_agent.py  # Automated fix execution
│   │   ├── escalation_agent.py # Human handoff detection & routing
│   │   ├── response_agent.py   # Empathetic reply generation
│   │   └── learn_agent.py   # Feedback loop & pattern learning
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # REST API endpoints
│   │   └── websocket.py     # Real-time WebSocket dashboard
│   └── mimo/
│       ├── __init__.py
│       └── client.py        # MiMo LLM integration (OpenAI-compatible)
├── templates/
│   └── dashboard.html       # Professional dark-theme real-time dashboard
└── data/                    # SQLite database location
```

## Dashboard

The real-time dashboard features 8 tabs:

- **🎫 Tickets** — View, create, and manage support tickets
- **📚 Knowledge Base** — Browse and add knowledge base entries
- **⚡ Pipeline** — Visualize the 7-agent pipeline in real-time
- **🔧 Actions** — Track automated actions executed by ActionAgent
- **🚨 Escalations** — Monitor escalated tickets and routing
- **💬 Responses** — Review AI-generated responses and confidence scores
- **📊 Analytics** — Ticket distribution, sentiment trends, category breakdown
- **⚙️ System** — Agent health, kernel stats, metrics

## Quick Start

### Local

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Open `http://localhost:8000` for the dashboard.

### Docker

```bash
docker-compose up --build
```

### API Usage

```bash
# Submit a ticket
curl -X POST http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-001",
    "subject": "Cannot log in to my account",
    "body": "I have been trying to log in for 2 hours. Password reset doesn't work.",
    "category": "account",
    "urgency": "high"
  }'

# Get analytics
curl http://localhost:8000/api/analytics

# Search knowledge base
curl http://localhost:8000/api/knowledge-base?q=login
```

## Database Tables

| Table | Purpose |
|---|---|
| `tickets` | Customer support tickets with classification |
| `knowledge_base` | Searchable knowledge articles |
| `responses` | AI-generated responses with confidence scores |
| `actions` | Automated actions executed by ActionAgent |
| `escalations` | Tickets escalated to human teams |
| `learnings` | Patterns and solutions learned from resolved tickets |
| `metrics` | System and agent performance metrics |
| `sessions` | Pipeline processing sessions |

## MiMo LLM Integration

Uses the OpenAI-compatible API format to communicate with MiMo v2.5 Pro:

- **Endpoint**: Configurable via `MIMO_API_ENDPOINT`
- **Model**: `xmtp/mimo-v2.5-pro`
- **Used by**: TriageAgent (classification), ReasoningAgent (root cause), ResponseAgent (reply generation)

## License

MIT
