"""
File-based storage — replaces SQLite/SQLAlchemy with plain CSV + JSON files.

Structure:
  azero_data/
    analyses.csv          — one row per analysis (metadata only)
    analyses/
      {id}_input.json     — IdeaInput JSON
      {id}_result.json    — full AnalysisResult JSON (written on completion)

No database, no migrations, no setup. Everything is human-readable.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Storage root — next to wherever the process runs
_STORAGE_ROOT = Path(os.environ.get("AZERO_DATA_DIR", "./azero_data"))
_CSV_PATH = _STORAGE_ROOT / "analyses.csv"
_ANALYSES_DIR = _STORAGE_ROOT / "analyses"

CSV_FIELDS = [
    "id", "status", "stage",
    "created_at", "completed_at",
    "idea_name", "is_demo", "error_message",
]


def _ensure_dirs() -> None:
    _STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    _ANALYSES_DIR.mkdir(parents=True, exist_ok=True)


def _read_all() -> list[dict]:
    """Read all rows from the CSV. Returns [] if file doesn't exist."""
    if not _CSV_PATH.exists():
        return []
    with _CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_all(rows: list[dict]) -> None:
    """Overwrite the CSV with the given rows."""
    _ensure_dirs()
    with _CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def resolve_id(query: str) -> Optional[str]:
    """Resolve a full UUID, short prefix (e.g. b28a73fb), or 1-based index (e.g. 1) to a full analysis ID."""
    rows = _read_all()
    if not rows:
        return None

    # Check 1-based index (e.g. "1", "2")
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(rows):
            return rows[idx]["id"]

    query_clean = query.strip().lower()

    # Check exact match
    for row in rows:
        if row["id"].lower() == query_clean:
            return row["id"]

    # Check prefix match (e.g. first 8 characters)
    matches = [row["id"] for row in rows if row["id"].lower().startswith(query_clean)]
    if matches:
        return matches[0]

    return None


def _input_path(analysis_id: str) -> Path:
    if len(analysis_id) >= 32 and "-" in analysis_id:
        full_id = analysis_id
    else:
        full_id = resolve_id(analysis_id) or analysis_id
    return _ANALYSES_DIR / f"{full_id}_input.json"


def _result_path(analysis_id: str) -> Path:
    if len(analysis_id) >= 32 and "-" in analysis_id:
        full_id = analysis_id
    else:
        full_id = resolve_id(analysis_id) or analysis_id
    return _ANALYSES_DIR / f"{full_id}_result.json"


# ── Public API ────────────────────────────────────────────────────────────────


def create_record(
    analysis_id: str,
    idea_name: str,
    input_data: dict,
    is_demo: bool = False,
) -> None:
    """Insert a new analysis row and write the input JSON."""
    _ensure_dirs()

    _input_path(analysis_id).write_text(
        json.dumps(input_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rows = _read_all()
    rows.insert(0, {
        "id": analysis_id,
        "status": "pending",
        "stage": "clarifying_idea",
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        "completed_at": "",
        "idea_name": idea_name,
        "is_demo": "true" if is_demo else "false",
        "error_message": "",
    })
    _write_all(rows)


def update_stage(analysis_id: str, status: str, stage: str) -> None:
    """Update status/stage while analysis is running."""
    full_id = resolve_id(analysis_id) or analysis_id
    rows = _read_all()
    for row in rows:
        if row["id"] == full_id:
            row["status"] = status
            row["stage"] = stage
            break
    _write_all(rows)


def complete_record(analysis_id: str, result_dict: dict) -> None:
    """Mark analysis complete and write the result JSON."""
    full_id = resolve_id(analysis_id) or analysis_id
    _result_path(full_id).write_text(
        json.dumps(result_dict, ensure_ascii=False, default=str, indent=2),
        encoding="utf-8",
    )
    rows = _read_all()
    for row in rows:
        if row["id"] == full_id:
            row["status"] = "complete"
            row["stage"] = "complete"
            row["completed_at"] = datetime.utcnow().isoformat(timespec="seconds")
            break
    _write_all(rows)


def fail_record(analysis_id: str, error: str) -> None:
    """Mark analysis as failed."""
    full_id = resolve_id(analysis_id) or analysis_id
    rows = _read_all()
    for row in rows:
        if row["id"] == full_id:
            row["status"] = "failed"
            row["error_message"] = error[:500]
            break
    _write_all(rows)


def get_record(analysis_id: str) -> Optional[dict]:
    """Return the CSV row dict for an analysis, or None."""
    full_id = resolve_id(analysis_id)
    if not full_id:
        return None
    for row in _read_all():
        if row["id"] == full_id:
            return row
    return None


def get_input(analysis_id: str) -> Optional[dict]:
    full_id = resolve_id(analysis_id) or analysis_id
    p = _input_path(full_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def get_result(analysis_id: str) -> Optional[dict]:
    full_id = resolve_id(analysis_id) or analysis_id
    p = _result_path(full_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def list_records(limit: int = 50) -> list[dict]:
    """Return rows newest-first."""
    rows = _read_all()
    return rows[:limit]


def delete_record(analysis_id: str) -> bool:
    """Delete analysis row + JSON files. Returns True if found."""
    full_id = resolve_id(analysis_id)
    if not full_id:
        return False
    rows = _read_all()
    new_rows = [r for r in rows if r["id"] != full_id]
    if len(new_rows) == len(rows):
        return False
    _write_all(new_rows)
    for p in (_input_path(full_id), _result_path(full_id)):
        if p.exists():
            p.unlink()
    return True


async def init_storage() -> None:
    """No-op — kept for API startup compatibility."""
    _ensure_dirs()
