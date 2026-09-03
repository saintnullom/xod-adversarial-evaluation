"""Explicit belief-graph persistence and bounded traversal."""

from __future__ import annotations

import sqlite3
import uuid

from app.repositories.beliefs import utc_now


RELATIONSHIP_COLUMNS = """r.id, r.source_belief_id, source.proposition AS source_proposition,
    r.target_belief_id, target.proposition AS target_proposition, r.relationship_type, r.note, r.created_at"""
RELATIONSHIP_JOINS = """ FROM belief_relationships r
    JOIN beliefs source ON source.id = r.source_belief_id
    JOIN beliefs target ON target.id = r.target_belief_id """


class BeliefRelationshipRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, source_belief_id: str, target_belief_id: str, relationship_type: str, note: str | None) -> dict[str, object]:
        if source_belief_id == target_belief_id:
            raise ValueError("A belief cannot be related to itself.")
        record = {
            "id": str(uuid.uuid4()), "source_belief_id": source_belief_id, "target_belief_id": target_belief_id,
            "relationship_type": relationship_type, "note": note, "created_at": utc_now(),
        }
        with self.connection:
            self.connection.execute(
                """INSERT INTO belief_relationships
                   (id, source_belief_id, target_belief_id, relationship_type, note, created_at)
                   VALUES (:id, :source_belief_id, :target_belief_id, :relationship_type, :note, :created_at)""",
                record,
            )
        return self._by_id(str(record["id"]))

    def list_for_belief(self, belief_id: str) -> dict[str, list[dict[str, object]]]:
        outgoing = self.connection.execute(
            f"SELECT {RELATIONSHIP_COLUMNS}{RELATIONSHIP_JOINS} WHERE r.source_belief_id = ? ORDER BY r.created_at DESC",
            (belief_id,),
        ).fetchall()
        incoming = self.connection.execute(
            f"SELECT {RELATIONSHIP_COLUMNS}{RELATIONSHIP_JOINS} WHERE r.target_belief_id = ? ORDER BY r.created_at DESC",
            (belief_id,),
        ).fetchall()
        return {"outgoing": [dict(row) for row in outgoing], "incoming": [dict(row) for row in incoming]}

    def neighborhood(self, root_belief_id: str, depth: int) -> dict[str, object]:
        all_edges = [dict(row) for row in self.connection.execute(
            f"SELECT {RELATIONSHIP_COLUMNS}{RELATIONSHIP_JOINS}"
        ).fetchall()]
        node_ids = {root_belief_id}
        frontier = {root_belief_id}
        included_edges: list[dict[str, object]] = []
        for _ in range(depth):
            next_frontier: set[str] = set()
            for edge in all_edges:
                source = str(edge["source_belief_id"])
                target = str(edge["target_belief_id"])
                if source in frontier or target in frontier:
                    if edge not in included_edges:
                        included_edges.append(edge)
                    next_frontier.update({source, target})
            next_frontier -= node_ids
            node_ids.update(next_frontier)
            frontier = next_frontier
            if not frontier:
                break
        placeholders = ",".join("?" for _ in node_ids)
        rows = self.connection.execute(
            f"""SELECT id, proposition, current_version, user_confidence, xod_confidence, status, created_at, updated_at
                FROM beliefs WHERE id IN ({placeholders}) ORDER BY updated_at DESC""",
            tuple(node_ids),
        ).fetchall()
        return {"root_belief_id": root_belief_id, "depth": depth, "nodes": [dict(row) for row in rows], "edges": included_edges}

    def _by_id(self, relationship_id: str) -> dict[str, object]:
        row = self.connection.execute(
            f"SELECT {RELATIONSHIP_COLUMNS}{RELATIONSHIP_JOINS} WHERE r.id = ?", (relationship_id,)
        ).fetchone()
        assert row is not None
        return dict(row)
