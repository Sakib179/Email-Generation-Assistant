from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .schemas import GenerationLogRecord, HistoryItem, QualityScores


class Storage:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    intent TEXT NOT NULL,
                    key_facts TEXT NOT NULL,
                    tone TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    email TEXT NOT NULL,
                    quality_scores TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    needs_human_review INTEGER NOT NULL,
                    prompt_version TEXT NOT NULL,
                    token_usage TEXT NOT NULL,
                    latency_ms REAL
                )
                """
            )

    def save_generation(self, record: GenerationLogRecord) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                INSERT INTO generations (
                    intent, key_facts, tone, strategy, model_used, subject, email,
                    quality_scores, attempt_count, needs_human_review, prompt_version,
                    token_usage, latency_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.intent,
                    json.dumps(record.key_facts),
                    record.tone,
                    record.strategy,
                    record.model_used,
                    record.subject,
                    record.email,
                    record.quality_scores.model_dump_json(),
                    record.attempt_count,
                    1 if record.needs_human_review else 0,
                    record.prompt_version,
                    json.dumps(record.token_usage),
                    record.latency_ms,
                ),
            )

    def list_history(self, limit: int = 20) -> list[HistoryItem]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, created_at, intent, tone, strategy, model_used, subject,
                       email, quality_scores, needs_human_review
                FROM generations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            HistoryItem(
                id=int(row["id"]),
                created_at=row["created_at"],
                intent=row["intent"],
                tone=row["tone"],
                strategy=row["strategy"],
                model_used=row["model_used"],
                subject=row["subject"],
                email=row["email"],
                quality_scores=QualityScores.model_validate_json(row["quality_scores"]),
                needs_human_review=bool(row["needs_human_review"]),
            )
            for row in rows
        ]

