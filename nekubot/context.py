"""SQLite-backed conversation history storage for the bot."""

import os
import sqlite3
from typing import Dict, List

MAX_CONTEXT_HISTORY = 8


class ContextStore:
    """Lightweight SQLite-backed conversation store."""

    def __init__(self, db_path: str = "context_history.db") -> None:
        db_dir = os.path.dirname(db_path)
        if db_path != ":memory:" and db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS context_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def save_message(self, user_id: str, role: str, content: str) -> None:
        """Persist a single message to the conversation history."""
        self.cursor.execute(
            "INSERT INTO context_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        self.conn.commit()

    def get_context(self, user_id: str) -> List[Dict[str, str]]:
        """Return the most recent conversation history for ``user_id``."""
        self.cursor.execute(
            "SELECT role, content FROM context_history WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,),
        )
        rows = self.cursor.fetchall()
        context = [{"role": row[0], "content": row[1]} for row in rows]
        if len(context) > MAX_CONTEXT_HISTORY:
            context = context[-MAX_CONTEXT_HISTORY:]
        return context
