# src/joss_repo_miner/utils/io.py
from __future__ import annotations
import csv, os, sys
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class Record:
    status: str                # "published" | "accepted"
    paper_url: Optional[str]
    issue_url: Optional[str]
    doi: Optional[str]
    joss_id: Optional[str]
    title: Optional[str]
    repo_url: Optional[str]

class CsvWriter:
    """Buffered writer with checkpointing (.part.csv) to avoid data loss."""
    def __init__(self, out_file: str, checkpoint_every: int = 100):
        self.out_file = out_file
        root, ext = os.path.splitext(out_file)
        self.part_file = f"{root}.part{ext or '.csv'}"
        self.checkpoint_every = max(1, checkpoint_every)
        self.fieldnames = ["status","paper_url","issue_url","doi","joss_id","title","repo_url"]
        self.buffer: List[Record] = []
        self._ensure_header()

    def _ensure_header(self):
        if not os.path.exists(self.part_file):
            with open(self.part_file, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

    def add(self, rec: Record):
        self.buffer.append(rec)
        if len(self.buffer) >= self.checkpoint_every:
            self.flush()

    def flush(self):
        if not self.buffer: return
        with open(self.part_file, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            for r in self.buffer:
                w.writerow(asdict(r))
        print(f"[checkpoint] +{len(self.buffer)} rows -> {self.part_file}", file=sys.stderr)
        self.buffer.clear()

    def finalize(self):
        self.flush()
        with open(self.part_file, "r", encoding="utf-8") as src, open(self.out_file, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print(f"[done] finalized {self.out_file}", file=sys.stderr)
