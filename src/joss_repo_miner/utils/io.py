# src/joss_repo_miner/utils/io.py
from __future__ import annotations
import csv
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

@dataclass
class Record:
    status: str
    paper_url: Optional[str]
    issue_url: Optional[str]
    doi: Optional[str]
    joss_id: Optional[str]
    title: Optional[str]
    repo_url: Optional[str]
    created_at: Optional[str] = None  # kept as str; we'll normalize on write

def _to_ddmmyyyy(value: Optional[str]) -> str:
    """Normalize any provided date/time string to dd.mm.yyyy; default = today."""
    if value:
        # Try a few common formats, including ISO-8601 with/without tz
        fmts = (
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        )
        for fmt in fmts:
            try:
                return datetime.strptime(value, fmt).strftime("%d.%m.%Y")
            except ValueError:
                pass
        # As a last resort, try datetime.fromisoformat (handles offsets like +00:00)
        try:
            return datetime.fromisoformat(value).strftime("%d.%m.%Y")
        except Exception:
            pass
    # Fallback: today (UTC), date only
    return datetime.now(timezone.utc).strftime("%d.%m.%Y")

class CsvWriter:
    """Write directly to the final CSV (no checkpoints)."""
    def __init__(self, out_file: str, checkpoint_every: int = 0):  # arg kept but ignored
        self.out_file = out_file
        self.fieldnames = ["status", "paper_url", "title", "repo_url", "created_at"]
        with open(self.out_file, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

    def add(self, rec: Record) -> None:
        # write only selected fields; always store created_at as dd.mm.yyyy
        row = {k: getattr(rec, k, None) for k in ["status", "paper_url", "title", "repo_url", "created_at"]}
        row["created_at"] = _to_ddmmyyyy(rec.created_at)
        with open(self.out_file, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writerow(row)

    def flush(self) -> None:
        pass

    def finalize(self) -> None:
        pass
