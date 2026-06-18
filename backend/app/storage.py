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
                    included_facts TEXT NOT NULL DEFAULT '[]',
                    missing_facts TEXT NOT NULL DEFAULT '[]',
                    quality_scores TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    needs_human_review INTEGER NOT NULL,
                    review_reasons TEXT NOT NULL DEFAULT '[]',
                    hallucination_flag INTEGER NOT NULL DEFAULT 0,
                    judge_reason TEXT NOT NULL DEFAULT '',
                    prompt_version TEXT NOT NULL,
                    token_usage TEXT NOT NULL,
                    latency_ms REAL
                )
                """
            )
            self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(generations)").fetchall()}
        migrations = {
            "included_facts": "ALTER TABLE generations ADD COLUMN included_facts TEXT NOT NULL DEFAULT '[]'",
            "missing_facts": "ALTER TABLE generations ADD COLUMN missing_facts TEXT NOT NULL DEFAULT '[]'",
            "review_reasons": "ALTER TABLE generations ADD COLUMN review_reasons TEXT NOT NULL DEFAULT '[]'",
            "hallucination_flag": "ALTER TABLE generations ADD COLUMN hallucination_flag INTEGER NOT NULL DEFAULT 0",
            "judge_reason": "ALTER TABLE generations ADD COLUMN judge_reason TEXT NOT NULL DEFAULT ''",
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)

    def save_generation(self, record: GenerationLogRecord) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                INSERT INTO generations (
                    intent, key_facts, tone, strategy, model_used, subject, email,
                    included_facts, missing_facts, quality_scores, attempt_count,
                    needs_human_review, review_reasons, hallucination_flag,
                    judge_reason, prompt_version, token_usage, latency_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.intent,
                    json.dumps(record.key_facts),
                    record.tone,
                    record.strategy,
                    record.model_used,
                    record.subject,
                    record.email,
                    json.dumps(record.included_facts),
                    json.dumps(record.missing_facts),
                    record.quality_scores.model_dump_json(),
                    record.attempt_count,
                    1 if record.needs_human_review else 0,
                    json.dumps(record.review_reasons),
                    1 if record.hallucination_flag else 0,
                    record.judge_reason,
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
                       key_facts, email, included_facts, missing_facts, quality_scores,
                       attempt_count, needs_human_review, review_reasons,
                       hallucination_flag, judge_reason, prompt_version
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
                key_facts=_json_list(row["key_facts"]),
                tone=row["tone"],
                strategy=row["strategy"],
                model_used=row["model_used"],
                subject=row["subject"],
                email=row["email"],
                included_facts=_history_included_facts(row),
                missing_facts=_json_list(row["missing_facts"]),
                quality_scores=QualityScores.model_validate_json(row["quality_scores"]),
                attempt_count=int(row["attempt_count"]),
                needs_human_review=bool(row["needs_human_review"]),
                review_reasons=_history_review_reasons(row),
                hallucination_flag=bool(row["hallucination_flag"]),
                judge_reason=row["judge_reason"] or "",
                prompt_version=row["prompt_version"] or "",
            )
            for row in rows
        ]


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def _history_included_facts(row: sqlite3.Row) -> list[str]:
    included = _json_list(row["included_facts"])
    if included:
        return included
    key_facts = _json_list(row["key_facts"])
    missing = set(_json_list(row["missing_facts"]))
    if not missing:
        return key_facts
    return [fact for fact in key_facts if fact not in missing]


def _history_review_reasons(row: sqlite3.Row) -> list[str]:
    reasons = _json_list(row["review_reasons"])
    if reasons:
        return reasons
    missing = _json_list(row["missing_facts"])
    if missing:
        return [f"Missing or weakly integrated fact: {fact}" for fact in missing]
    if bool(row["needs_human_review"]):
        return ["This older history item was flagged for review, but detailed review reasons were not stored."]
    return []
