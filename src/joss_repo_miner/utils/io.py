# src/joss_repo_miner/utils/io.py
"""Input and Output (I/O) utilities for the JOSS repository miner.

This module defines the primary data transfer object (Record) used to represent 
scraped repository metadata, handles dates normalization format workflows, 
and manages incremental file streaming operations into standardized CSV data outputs.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone


@dataclass
class Record:
    """Represents a single scraped JOSS paper or review issue entry.

    Attributes:
        status (str): The publication or curation status (e.g., 'accepted', 'published').
        paper_url (Optional[str]): The direct hyperlink targeting the JOSS web paper view.
        issue_url (Optional[str]): The associated GitHub repository review thread URL.
        doi (Optional[str]): The Digital Object Identifier string bound to the paper.
        joss_id (Optional[str]): Unique tracking identifier given to the paper inside JOSS.
        title (Optional[str]): The full textual title of the software submission.
        repo_url (Optional[str]): The targeted third-party open-source codebase repository URL.
        repo_status_code (int): The HTTP responses integer status code when checking the repo URL.
        created_at (Optional[str]): The timestamp tracking creation of the underlying record.
    """

    status: str
    paper_url: Optional[str]
    issue_url: Optional[str]
    doi: Optional[str]
    joss_id: Optional[str]
    title: Optional[str]
    repo_url: Optional[str]
    repo_status_code: int = None
    created_at: Optional[str] = None  # kept as str; we'll normalize on write


def _to_ddmmyyyy(value: Optional[str]) -> str:
    """Normalize any provided date/time string to dd.mm.yyyy; default = today.

    Args:
        value (Optional[str]): A raw timestamp text sequence in one of several ISO
            or localized standard calendar formats.

    Returns:
        str: The normalized calendar date text sequenced in a strict "dd.mm.yyyy" format.
    """
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
        """Initializes the CSV output pipeline and sets up file headers.

        Args:
            out_file (str): The filesystem destination path where data rows are streamed.
            checkpoint_every (int): Ignored parameter kept for compatibility signatures.

        Returns:
            None
        """
        self.out_file = out_file
        self.fieldnames = [
            "status",
            "paper_url",
            "joss_id",
            "title",
            "repo_url",
            "repo_status_code",
            "created_at",
        ]
        with open(self.out_file, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

    def add(self, rec: Record) -> None:
        """Appends an individual structured dataset entry block to the output file.

        Extracts selected record attributes, passes timestamps through a
        normalization filter, and streams data rows directly to the target system.

        Args:
            rec (Record): The data entity model container object containing the attributes.

        Returns:
            None
        """
        # write only selected fields; always store created_at as dd.mm.yyyy
        row = {
            k: getattr(rec, k, None)
            for k in [
                "status",
                "paper_url",
                "joss_id",
                "title",
                "repo_url",
                "repo_status_code",
                "created_at",
            ]
        }
        row["created_at"] = _to_ddmmyyyy(rec.created_at)
        with open(self.out_file, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writerow(row)

    def flush(self) -> None:
        """Flushes underlying buffered database writing structures.

        Returns:
            None
        """
        pass

    def finalize(self) -> None:
        """Finalizes program operational execution, closing downstream writing processes.

        Returns:
            None
        """
        pass