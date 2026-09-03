"""Conversation persistence kept separate from reasoning and providers."""

from __future__ import annotations

import sqlite3
import uuid
import json

from app.repositories.beliefs import utc_now


class ConversationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, title: str) -> dict[str, object]:
        conversation_id = str(uuid.uuid4())
        created_at = utc_now()
        self.connection.execute(
            "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
            (conversation_id, title, created_at),
        )
        self.connection.commit()
        return {"id": conversation_id, "title": title, "created_at": created_at, "messages": []}

    def list(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
        ).fetchall()
        return [{**dict(row), "messages": []} for row in rows]

    def get(self, conversation_id: str) -> dict[str, object] | None:
        conversation = self.connection.execute(
            "SELECT id, title, created_at FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conversation is None:
            return None
        messages = self.connection.execute(
            """SELECT messages.id, messages.conversation_id, messages.role, messages.content, messages.created_at,
                      analyses.payload_json
               FROM messages LEFT JOIN analyses ON analyses.message_id = messages.id
               WHERE messages.conversation_id = ? ORDER BY messages.created_at ASC, messages.rowid ASC""",
            (conversation_id,),
        ).fetchall()
        serialized_messages = []
        for message in messages:
            serialized = dict(message)
            payload = serialized.pop("payload_json")
            serialized["analysis"] = json.loads(payload) if payload else None
            serialized_messages.append(serialized)
        return {**dict(conversation), "messages": serialized_messages}

    def add_message(self, conversation_id: str, role: str, content: str) -> dict[str, str]:
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": utc_now(),
        }
        self.connection.execute(
            """INSERT INTO messages (id, conversation_id, role, content, created_at)
               VALUES (:id, :conversation_id, :role, :content, :created_at)""",
            message,
        )
        self.connection.commit()
        return message

    def add_turn(
        self, conversation_id: str, user_content: str, xod_content: str, analysis_json: str | None = None
    ) -> None:
        created_at = utc_now()
        xod_message_id = str(uuid.uuid4())
        with self.connection:
            self.connection.executemany(
                """INSERT INTO messages (id, conversation_id, role, content, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (str(uuid.uuid4()), conversation_id, "USER", user_content, created_at),
                    (xod_message_id, conversation_id, "XOD", xod_content, utc_now()),
                ],
            )
            if analysis_json:
                self.connection.execute(
                    """INSERT INTO analyses (id, conversation_id, message_id, mode, payload_json, created_at)
                       VALUES (?, ?, ?, 'TRIBUNAL', ?, ?)""",
                    (str(uuid.uuid4()), conversation_id, xod_message_id, analysis_json, utc_now()),
                )
