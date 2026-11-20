import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "fixit.db"
DATASET = "fixit_household"

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repair_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            category TEXT NOT NULL,
            appliance_or_area TEXT NOT NULL,
            problem_summary TEXT NOT NULL,
            diagnosis_json TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

async def remember_repair(category, appliance_or_area, problem_summary, diagnosis):
    created = datetime.now(timezone.utc).isoformat()
    payload = {
        "created_at": created,
        "category": category,
        "appliance_or_area": appliance_or_area,
        "problem_summary": problem_summary,
        "diagnosis": diagnosis
    }
    conn = _db()
    conn.execute(
        "INSERT INTO repair_memory(created_at, category, appliance_or_area, problem_summary, diagnosis_json) VALUES (?, ?, ?, ?, ?)",
        (created, category, appliance_or_area, problem_summary, json.dumps(diagnosis))
    )
    conn.commit()
    conn.close()

    if os.getenv("COGNEE_ENABLED", "true").lower() != "true":
        return {"provider": "sqlite", "saved": True}

    try:
        import cognee
        await cognee.remember(
            json.dumps(payload),
            dataset_name=DATASET
        )
        return {"provider": "cognee", "saved": True}
    except Exception as exc:
        # The product remains usable if first-run model setup or Cognee fails.
        return {"provider": "sqlite_fallback", "saved": True, "warning": str(exc)[:240]}

async def recall_repairs(query, limit=5):
    rows = []
    conn = _db()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT created_at, category, appliance_or_area, problem_summary, diagnosis_json FROM repair_memory ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    local_matches = [
        {
            "created_at": r["created_at"],
            "category": r["category"],
            "appliance_or_area": r["appliance_or_area"],
            "problem_summary": r["problem_summary"],
            "diagnosis": json.loads(r["diagnosis_json"])
        }
        for r in rows
        if query.lower() in (
            r["category"] + " " + r["appliance_or_area"] + " " + r["problem_summary"]
        ).lower()
    ]

    if os.getenv("COGNEE_ENABLED", "true").lower() != "true":
        return {"provider": "sqlite", "memories": local_matches}

    try:
        import cognee
        result = await cognee.recall(query, datasets=[DATASET])
        return {
            "provider": "cognee",
            "memories": local_matches,
            "semantic_recall": str(result)[:3000]
        }
    except Exception as exc:
        return {
            "provider": "sqlite_fallback",
            "memories": local_matches,
            "warning": str(exc)[:240]
        }
