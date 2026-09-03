"""SQLite initialization for the local-first XOD foundation."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "xod.db"

MIGRATIONS = [
    (
        "0002_belief_versions_add_status_and_analysis_source",
        """
        ALTER TABLE belief_versions ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE_TEST';
        ALTER TABLE belief_versions ADD COLUMN source_analysis_message_id TEXT;
        """,
    ),
    (
        "0003_belief_falsification_conditions",
        """
        CREATE TABLE IF NOT EXISTS belief_falsification_conditions (
            id TEXT PRIMARY KEY,
            belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
            condition TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
    (
        "0004_self_critique_evaluations",
        """
        CREATE TABLE IF NOT EXISTS self_critique_evaluations (
            message_id TEXT PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
            rubric_version TEXT NOT NULL,
            score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 4),
            verdict TEXT NOT NULL CHECK (verdict IN ('USEFUL', 'NEEDS_WORK')),
            checks_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
    (
        "0005_specialist_evaluation_measurements",
        """
        CREATE TABLE IF NOT EXISTS specialist_evaluation_measurements (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL UNIQUE,
            baseline_quality REAL NOT NULL CHECK (baseline_quality BETWEEN 0 AND 4),
            specialist_quality REAL NOT NULL CHECK (specialist_quality BETWEEN 0 AND 4),
            baseline_cost_usd REAL NOT NULL CHECK (baseline_cost_usd >= 0),
            specialist_cost_usd REAL NOT NULL CHECK (specialist_cost_usd >= 0),
            baseline_latency_ms INTEGER NOT NULL CHECK (baseline_latency_ms >= 0),
            specialist_latency_ms INTEGER NOT NULL CHECK (specialist_latency_ms >= 0),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """,
    ),
    (
        "0006_prediction_confidence_snapshot",
        """
        ALTER TABLE predictions ADD COLUMN belief_confidence_at_commit REAL
            CHECK (belief_confidence_at_commit BETWEEN 0 AND 1);
        """,
    ),
    (
        "0007_belief_relationships",
        """
        CREATE TABLE IF NOT EXISTS belief_relationships (
            id TEXT PRIMARY KEY,
            source_belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
            target_belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
            relationship_type TEXT NOT NULL CHECK (relationship_type IN (
                'SUPPORTS', 'CONTRADICTS', 'DEPENDS_ON', 'DERIVED_FROM', 'ALTERNATIVE_TO',
                'EVIDENCE_FOR', 'EVIDENCE_AGAINST', 'REQUIRES', 'UNTESTED_DEPENDENCY'
            )),
            note TEXT,
            created_at TEXT NOT NULL,
            CHECK (source_belief_id <> target_belief_id),
            UNIQUE (source_belief_id, target_belief_id, relationship_type)
        );
        """,
    ),
    (
        "0008_failure_reports",
        """
        CREATE TABLE IF NOT EXISTS failure_reports (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL CHECK (category IN (
                'INCORRECT_OBJECTION', 'MISUNDERSTOOD_PROPOSITION', 'IGNORED_CONTEXT',
                'HALLUCINATED_EVIDENCE', 'TOO_CONFIDENT', 'MISSED_CONTRADICTION', 'OTHER'
            )),
            summary TEXT NOT NULL,
            expected_behavior TEXT,
            evaluation_case_id TEXT,
            source_analysis_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
    (
        "0009_provider_failure_events",
        """
        CREATE TABLE IF NOT EXISTS provider_failure_events (
            error_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            operation TEXT NOT NULL CHECK (operation IN ('SPAR', 'TRIBUNAL')),
            provider TEXT NOT NULL,
            model TEXT,
            retryable INTEGER NOT NULL CHECK (retryable IN (0, 1)),
            latency_ms INTEGER,
            occurred_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_provider_failure_events_category_occurred_at
            ON provider_failure_events (category, occurred_at);
        """,
    ),
]


def database_path() -> Path:
    configured = os.getenv("XOD_DATABASE_PATH")
    return Path(configured) if configured else DEFAULT_DATABASE_PATH


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path | None = None) -> None:
    connection = connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('USER', 'XOD', 'SYSTEM')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS beliefs (
                id TEXT PRIMARY KEY,
                proposition TEXT NOT NULL,
                current_version INTEGER NOT NULL DEFAULT 1,
                user_confidence REAL CHECK (user_confidence BETWEEN 0 AND 1),
                xod_confidence REAL CHECK (xod_confidence BETWEEN 0 AND 1),
                status TEXT NOT NULL DEFAULT 'ACTIVE_TEST',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS belief_versions (
                id TEXT PRIMARY KEY,
                belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
                version INTEGER NOT NULL,
                proposition TEXT NOT NULL,
                user_confidence REAL CHECK (user_confidence BETWEEN 0 AND 1),
                change_reason TEXT,
                created_at TEXT NOT NULL,
                UNIQUE (belief_id, version)
            );
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
                claim TEXT NOT NULL,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                url TEXT,
                retrieved_at TEXT,
                reliability REAL CHECK (reliability BETWEEN 0 AND 1),
                relevance REAL CHECK (relevance BETWEEN 0 AND 1),
                direction TEXT NOT NULL CHECK (direction IN ('SUPPORTS', 'CONTRADICTS')),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY,
                belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
                statement TEXT NOT NULL,
                success_criteria TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expected_resolution_at TEXT,
                result TEXT,
                status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'RESOLVED', 'CANCELLED')),
                impact TEXT CHECK (impact IN ('SUPPORTS', 'WEAKENS', 'INCONCLUSIVE')),
                resolved_at TEXT
            );
            CREATE TABLE IF NOT EXISTS belief_falsification_conditions (
                id TEXT PRIMARY KEY,
                belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
                condition TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS objections (
                id TEXT PRIMARY KEY,
                belief_id TEXT REFERENCES beliefs(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                strength TEXT NOT NULL CHECK (strength IN ('LOW', 'MEDIUM', 'HIGH')),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                message_id TEXT NOT NULL UNIQUE REFERENCES messages(id) ON DELETE CASCADE,
                mode TEXT NOT NULL CHECK (mode IN ('TRIBUNAL')),
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS self_critique_evaluations (
                message_id TEXT PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
                rubric_version TEXT NOT NULL,
                score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 4),
                verdict TEXT NOT NULL CHECK (verdict IN ('USEFUL', 'NEEDS_WORK')),
                checks_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS specialist_evaluation_measurements (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL UNIQUE,
                baseline_quality REAL NOT NULL CHECK (baseline_quality BETWEEN 0 AND 4),
                specialist_quality REAL NOT NULL CHECK (specialist_quality BETWEEN 0 AND 4),
                baseline_cost_usd REAL NOT NULL CHECK (baseline_cost_usd >= 0),
                specialist_cost_usd REAL NOT NULL CHECK (specialist_cost_usd >= 0),
                baseline_latency_ms INTEGER NOT NULL CHECK (baseline_latency_ms >= 0),
                specialist_latency_ms INTEGER NOT NULL CHECK (specialist_latency_ms >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS belief_relationships (
                id TEXT PRIMARY KEY,
                source_belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
                target_belief_id TEXT NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
                relationship_type TEXT NOT NULL CHECK (relationship_type IN (
                    'SUPPORTS', 'CONTRADICTS', 'DEPENDS_ON', 'DERIVED_FROM', 'ALTERNATIVE_TO',
                    'EVIDENCE_FOR', 'EVIDENCE_AGAINST', 'REQUIRES', 'UNTESTED_DEPENDENCY'
                )),
                note TEXT,
                created_at TEXT NOT NULL,
                CHECK (source_belief_id <> target_belief_id),
                UNIQUE (source_belief_id, target_belief_id, relationship_type)
            );
            CREATE TABLE IF NOT EXISTS failure_reports (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL CHECK (category IN (
                    'INCORRECT_OBJECTION', 'MISUNDERSTOOD_PROPOSITION', 'IGNORED_CONTEXT',
                    'HALLUCINATED_EVIDENCE', 'TOO_CONFIDENT', 'MISSED_CONTRADICTION', 'OTHER'
                )),
                summary TEXT NOT NULL,
                expected_behavior TEXT,
                evaluation_case_id TEXT,
                source_analysis_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS provider_failure_events (
                error_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                operation TEXT NOT NULL CHECK (operation IN ('SPAR', 'TRIBUNAL')),
                provider TEXT NOT NULL,
                model TEXT,
                retryable INTEGER NOT NULL CHECK (retryable IN (0, 1)),
                latency_ms INTEGER,
                occurred_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            """
        )
        applied = {row["id"] for row in connection.execute("SELECT id FROM schema_migrations")}
        for migration_id, migration_sql in MIGRATIONS:
            if migration_id not in applied:
                connection.executescript(migration_sql)
                connection.execute(
                    "INSERT INTO schema_migrations (id, applied_at) VALUES (?, datetime('now'))",
                    (migration_id,),
                )
        connection.commit()
    finally:
        connection.close()
