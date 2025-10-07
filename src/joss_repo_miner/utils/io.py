# src/joss_repo_miner/utils/io.py
from __future__ import annotations
import csv
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Record:
    status: str
    paper_url: Optional[str]
    issue_url: Optional[str]
    doi: Optional[str]
    joss_id: Optional[str]
    title: Optional[str]
    repo_url: Optional[str]

class CsvWriter:
    """Write directly to the final CSV (no checkpoints)."""
    def __init__(self, out_file: str, checkpoint_every: int = 0):  # arg kept but ignored
        self.out_file = out_file
        self.fieldnames = ["status","paper_url","issue_url","doi","joss_id","title","repo_url"]
        # fresh file with header
        with open(self.out_file, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

    def add(self, rec: Record) -> None:
        with open(self.out_file, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writerow(asdict(rec))

    def flush(self) -> None:
        pass

    def finalize(self) -> None:
        pass

