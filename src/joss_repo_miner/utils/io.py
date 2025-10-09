# src/joss_repo_miner/utils/io.py
from __future__ import annotations
import csv
from dataclasses import dataclass, asdict
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
    created_at: Optional[str] = None  # new optional timestamp field

class CsvWriter:
    """Write directly to the final CSV (no checkpoints)."""
    def __init__(self, out_file: str, checkpoint_every: int = 0):  # arg kept but ignored
        self.out_file = out_file
        self.fieldnames = ["status", "paper_url", "title", "repo_url", "created_at"]
        # fresh file with header
        with open(self.out_file, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

    def add(self, rec: Record) -> None:
        # write only selected fields; fill created_at if missing
        row = {k: getattr(rec, k, None) for k in ["status", "paper_url", "title", "repo_url", "created_at"]}
        if not row.get("created_at"):
            row["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(self.out_file, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writerow(row)

    def flush(self) -> None:
        pass

    def finalize(self) -> None:
        pass
