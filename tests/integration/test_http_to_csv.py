import csv
import pytest
import responses
from datetime import datetime, timezone

from joss_repo_miner.utils.http import http_get
import joss_repo_miner.utils.http as http_mod
from joss_repo_miner.utils.io import CsvWriter, Record

def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        return rdr.fieldnames, list(rdr)

@responses.activate
def test_http_to_csv_rate_limit_then_success_and_write(tmp_path, monkeypatch):
    # Make waits short & deterministic
    monkeypatch.setattr(http_mod, "FIFTEEN_MIN", 1, raising=False)
    monkeypatch.setattr(http_mod, "USER_AGENT", "test-agent", raising=False)

    # Capture sleeps to prove we respected the rate-limit pause
    sleeps = []
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: sleeps.append(s))

    url = "https://example.com/data"

    # First call -> 429 with Retry-After=1 (triggers rate-limit handling and sleep)
    responses.add(
        responses.GET, url,
        status=429,
        headers={"Retry-After": "1"}
    )
    # Second call -> success (200)
    payload = "OK!"
    responses.add(
        responses.GET, url,
        status=200,
        body=payload,
        headers={"Content-Type": "text/plain"}
    )

    # 1) Integration: fetch with retry/backoff due to rate limit
    resp = http_get(url, timeout=5, retries=2, base_sleep=0.01)
    assert resp.status_code == 200
    assert resp.text == payload

    # Ensure we actually "slept" because of 429 (countdown path)
    assert sleeps != [] and sum(sleeps) >= 1

    # 2) Integration: write a CSV row using CsvWriter with date normalization
    out = tmp_path / "out.csv"
    w = CsvWriter(str(out))
    # created_at in ISO; should normalize to dd.mm.yyyy
    iso_date = "2024-09-05T12:34:56"
    rec = Record(
        status="published",
        paper_url=url,
        issue_url=None,
        doi=None,
        joss_id=None,
        title="Hello",
        repo_url="https://github.com/owner/repo",
        created_at=iso_date,
    )
    w.add(rec)

    # Verify CSV schema and normalized date
    fields, rows = read_rows(out)
    assert fields == ["status", "paper_url", "title", "repo_url", "created_at"]
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "published"
    assert row["paper_url"] == url
    assert row["title"] == "Hello"
    assert row["repo_url"] == "https://github.com/owner/repo"
    assert row["created_at"] == "05.09.2024"