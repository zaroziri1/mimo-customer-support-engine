"""SQLite database with WAL mode for MiMo Customer Support Engine."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get a new SQLite connection with WAL mode."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            customer_id TEXT NOT NULL,
            customer_email TEXT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            urgency TEXT DEFAULT 'medium',
            sentiment REAL DEFAULT 0.0,
            language TEXT DEFAULT 'en',
            status TEXT DEFAULT 'open',
            assigned_agent TEXT,
            priority_score REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            relevance_score REAL DEFAULT 1.0,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            response_text TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            sent BOOLEAN DEFAULT 0,
            customer_feedback INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_details TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            executed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            from_agent TEXT NOT NULL,
            to_team TEXT NOT NULL,
            reason TEXT NOT NULL,
            urgency TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            pattern TEXT NOT NULL,
            solution TEXT NOT NULL,
            effectiveness REAL DEFAULT 0.0,
            category TEXT,
            times_applied INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_type TEXT DEFAULT 'gauge',
            agent_name TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            agent_chain TEXT,
            status TEXT DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
        CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
        CREATE INDEX IF NOT EXISTS idx_tickets_urgency ON tickets(urgency);
        CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
        CREATE INDEX IF NOT EXISTS idx_responses_ticket ON responses(ticket_id);
        CREATE INDEX IF NOT EXISTS idx_actions_ticket ON actions(ticket_id);
        CREATE INDEX IF NOT EXISTS idx_escalations_ticket ON escalations(ticket_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
    """)

    conn.commit()
    conn.close()


def insert_ticket(ticket_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (external_id, customer_id, customer_email, subject, body,
                           category, urgency, sentiment, language, status, priority_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_data.get('external_id'), ticket_data['customer_id'],
        ticket_data.get('customer_email'), ticket_data['subject'],
        ticket_data['body'], ticket_data.get('category', 'general'),
        ticket_data.get('urgency', 'medium'), ticket_data.get('sentiment', 0.0),
        ticket_data.get('language', 'en'), 'open', ticket_data.get('priority_score', 0.0)
    ))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


def update_ticket(ticket_id: int, updates: dict):
    conn = get_connection()
    set_clause = ", ".join(f"{k}=?" for k in updates.keys())
    values = list(updates.values()) + [ticket_id]
    conn.execute(f"UPDATE tickets SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
    conn.commit()
    conn.close()


def get_ticket(ticket_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tickets(status: str = None, limit: int = 50) -> list:
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM tickets WHERE status=? ORDER BY created_at DESC LIMIT ?",
                           (status, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_knowledge_base(query: str, category: str = None, limit: int = 5) -> list:
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM knowledge_base WHERE category=? AND (title LIKE ? OR content LIKE ? OR tags LIKE ?) "
            "ORDER BY relevance_score DESC LIMIT ?",
            (category, f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM knowledge_base WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? "
            "ORDER BY relevance_score DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_response(ticket_id: int, agent_name: str, response_text: str, confidence: float) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO responses (ticket_id, agent_name, response_text, confidence) VALUES (?, ?, ?, ?)",
        (ticket_id, agent_name, response_text, confidence)
    )
    rid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rid


def insert_action(ticket_id: int, action_type: str, details: str, executed_by: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO actions (ticket_id, action_type, action_details, executed_by) VALUES (?, ?, ?, ?)",
        (ticket_id, action_type, details, executed_by)
    )
    aid = cursor.lastrowid
    conn.commit()
    conn.close()
    return aid


def update_action(action_id: int, status: str, result: str = None):
    conn = get_connection()
    conn.execute(
        "UPDATE actions SET status=?, result=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, result, action_id)
    )
    conn.commit()
    conn.close()


def insert_escalation(ticket_id: int, from_agent: str, to_team: str, reason: str, urgency: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO escalations (ticket_id, from_agent, to_team, reason, urgency) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, from_agent, to_team, reason, urgency)
    )
    eid = cursor.lastrowid
    conn.commit()
    conn.close()
    return eid


def insert_learning(ticket_id: int, pattern: str, solution: str, effectiveness: float, category: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO learnings (ticket_id, pattern, solution, effectiveness, category) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, pattern, solution, effectiveness, category)
    )
    lid = cursor.lastrowid
    conn.commit()
    conn.close()
    return lid


def record_metric(name: str, value: float, metric_type: str = "gauge", agent_name: str = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO metrics (metric_name, metric_value, metric_type, agent_name) VALUES (?, ?, ?, ?)",
        (name, value, metric_type, agent_name)
    )
    conn.commit()
    conn.close()


def get_metrics(name: str = None, limit: int = 100) -> list:
    conn = get_connection()
    if name:
        rows = conn.execute(
            "SELECT * FROM metrics WHERE metric_name=? ORDER BY recorded_at DESC LIMIT ?",
            (name, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM metrics ORDER BY recorded_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_analytics() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    open_t = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='open'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='resolved'").fetchone()[0]
    escalated = conn.execute("SELECT COUNT(*) FROM escalations").fetchone()[0]
    actions_count = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
    avg_sentiment = conn.execute("SELECT AVG(sentiment) FROM tickets").fetchone()[0] or 0
    by_category = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM tickets GROUP BY category"
    ).fetchall()
    by_urgency = conn.execute(
        "SELECT urgency, COUNT(*) as cnt FROM tickets GROUP BY urgency"
    ).fetchall()
    conn.close()
    return {
        "total_tickets": total,
        "open_tickets": open_t,
        "resolved_tickets": resolved,
        "escalations": escalated,
        "actions_executed": actions_count,
        "avg_sentiment": round(avg_sentiment, 2),
        "by_category": {r['category']: r['cnt'] for r in by_category},
        "by_urgency": {r['urgency']: r['cnt'] for r in by_urgency},
    }
