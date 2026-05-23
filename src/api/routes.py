"""API routes for MiMo Customer Support Engine."""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src import database as db

router = APIRouter(prefix="/api")


class TicketCreate(BaseModel):
    customer_id: str
    customer_email: Optional[str] = None
    subject: str
    body: str
    category: Optional[str] = "general"
    urgency: Optional[str] = "medium"


class KBEntry(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"
    tags: Optional[str] = ""
    relevance_score: Optional[float] = 1.0


# ── Ticket endpoints ──

@router.post("/tickets")
async def create_ticket(ticket: TicketCreate):
    from src.main import kernel
    ticket_data = ticket.model_dump()
    ticket_id = db.insert_ticket(ticket_data)
    ticket_data["id"] = ticket_id

    # Process through pipeline
    result = await kernel.process_ticket(ticket_data)
    db.update_ticket(ticket_id, {"status": "resolved" if result.get("status") == "completed" else "processing"})
    return {"ticket_id": ticket_id, "pipeline_result": result}


@router.get("/tickets")
async def list_tickets(status: Optional[str] = None, limit: int = 50):
    return db.get_tickets(status=status, limit=limit)


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int):
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, updates: dict):
    db.update_ticket(ticket_id, updates)
    return {"status": "updated"}


# ── Knowledge Base endpoints ──

@router.get("/knowledge-base")
async def search_kb(q: Optional[str] = None, category: Optional[str] = None, limit: int = 20):
    if q:
        return db.search_knowledge_base(q, category=category, limit=limit)
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM knowledge_base ORDER BY relevance_score DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/knowledge-base")
async def add_kb_entry(entry: KBEntry):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO knowledge_base (title, content, category, tags, relevance_score) VALUES (?, ?, ?, ?, ?)",
        (entry.title, entry.content, entry.category, entry.tags, entry.relevance_score)
    )
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": entry_id, "status": "created"}


# ── Actions endpoints ──

@router.get("/actions")
async def list_actions(limit: int = 50):
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM actions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Escalations endpoints ──

@router.get("/escalations")
async def list_escalations(limit: int = 50):
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Responses endpoints ──

@router.get("/responses")
async def list_responses(limit: int = 50):
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM responses ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Analytics endpoints ──

@router.get("/analytics")
async def get_analytics():
    return db.get_analytics()


@router.get("/metrics")
async def get_metrics(name: Optional[str] = None, limit: int = 100):
    return db.get_metrics(name=name, limit=limit)


# ── System endpoints ──

@router.get("/system/stats")
async def system_stats():
    from src.main import kernel
    return kernel.get_stats()
