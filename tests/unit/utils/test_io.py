# tests/unit/utils/test_io.py
import csv
from datetime import datetime, timezone
import os
import pytest

from joss_repo_miner.utils.io import _to_ddmmyyyy, CsvWriter, Record

# ---------- _to_ddmmyyyy ----------

def test_to_ddmmyyyy_keeps_ddmmyyyy():
    assert _to_ddmmyyyy("05.09.2024") == "05.09.2024"

def test_to_ddmmyyyy_from_yyyy_mm_dd():
    assert _to_ddmmyyyy("2024-09-05") == "05.09.2024"

def test_to_ddmmyyyy_from_iso_no_tz():
    assert _to_ddmmyyyy("2024-09-05T12:34:56") == "05.09.2024"

def test_to_ddmmyyyy_from_iso_with_tz():
    # fromisoformat path handles +hh:mm offsets
    assert _to_ddmmyyyy("2024-09-05T12:34:56+00:00") == "05.09.2024"

def test_to_ddmmyyyy_from_space_sep_datetime():
    assert _to_ddmmyyyy("2024-09-05 12:34:56") == "05.09.2024"

def test_to_ddmmyyyy_unparsable_falls_back_to_today_utc():
    today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    assert _to_ddmmyyyy("not-a-date") == today

def test_to_ddmmyyyy_none_falls_back_to_today_utc():
    today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    assert _to_ddmmyyyy(None) == today

# ---------- CsvWriter ----------

def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def test_csvwriter_writes_header_in_order(tmp_path):
    out = tmp_path / "out.csv"
    CsvWriter(str(out))  # init writes header
    fieldnames, rows = read_csv_rows(out)
    assert fieldnames == ["status", "paper_url", "title", "repo_url", "created_at"]
    assert rows == []  # no data yet

def test_csvwriter_add_normalizes_created_at(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    rec = Record(
        status="open",
        paper_url="https://example.org/paper",
        issue_url=None,
        doi=None,
        joss_id=None,
        title="A Study",
        repo_url="https://github.com/org/repo",
        created_at="2024-09-05T12:00:00"
    )
    w.add(rec)
    fieldnames, rows = read_csv_rows(out)
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "open"
    assert row["paper_url"] == "https://example.org/paper"
    assert row["title"] == "A Study"
    assert row["repo_url"] == "https://github.com/org/repo"
    assert row["created_at"] == "05.09.2024"  # normalized

def test_csvwriter_add_ignores_unspecified_record_fields(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    rec = Record(
        status="closed",
        paper_url=None,
        issue_url="https://github.com/openjournals/joss-reviews/issues/12345",
        doi="10.21105/joss.12345",
        joss_id="joss.12345",
        title="Hidden Fields Should Not Leak",
        repo_url="https://github.com/org/repo",
        created_at="2024-09-06"
    )
    w.add(rec)
    fieldnames, rows = read_csv_rows(out)
    row = rows[0]
    # Only these columns should exist
    assert set(row.keys()) == {"status", "paper_url", "title", "repo_url", "created_at"}
    # The extra dataclass fields did not become columns
    assert "issue_url" not in row and "doi" not in row and "joss_id" not in row

def test_csvwriter_add_handles_none_created_at_as_today(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    rec = Record(
        status="queued",
        paper_url=None,
        issue_url=None,
        doi=None,
        joss_id=None,
        title="No Date",
        repo_url=None,
        created_at=None,
    )
    w.add(rec)
    today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    _, rows = read_csv_rows(out)
    assert rows[0]["created_at"] == today

def test_csvwriter_appends_multiple_rows(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    w.add(Record("open", None, None, None, None, "T1", "r1", "2024-09-01"))
    w.add(Record("closed", "p2", None, None, None, "T2", "r2", "2024-09-02"))
    _, rows = read_csv_rows(out)
    assert [r["title"] for r in rows] == ["T1", "T2"]
    assert [r["created_at"] for r in rows] == ["01.09.2024", "02.09.2024"]

def test_csvwriter_handles_unicode_text(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    w.add(Record("open", "https://exämple.org", None, None, None, "Café μParser", "https://gïthub.com/x/y", "2024-09-03"))
    _, rows = read_csv_rows(out)
    assert rows[0]["paper_url"] == "https://exämple.org"
    assert rows[0]["title"] == "Café μParser"
    assert rows[0]["repo_url"] == "https://gïthub.com/x/y"

def test_csvwriter_checkpoint_arg_is_ignored(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out), checkpoint_every=10)  # should not change behavior
    w.add(Record("s", None, None, None, None, "T", None, "2024-01-02"))
    _, rows = read_csv_rows(out)
    assert len(rows) == 1

def test_csvwriter_flush_and_finalize_noops(tmp_path):
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    # Should not raise or modify the file
    w.flush()
    w.finalize()
    # Still just header
    fieldnames, rows = read_csv_rows(out)
    assert rows == []
