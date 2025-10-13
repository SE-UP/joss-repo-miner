# tests/unit/utils/test_http.py
import io
import time as _time
import pytest
import requests
import responses

# Import the module under test
# adjust the import path to match your project structure
from src.joss_repo_miner.utils import http as http_mod

@pytest.fixture(autouse=True)
def patch_constants(monkeypatch):
    # Make sleeps short/predictable
    monkeypatch.setattr(http_mod, "FIFTEEN_MIN", 15, raising=False)
    # Freeze user agent for assertions
    monkeypatch.setattr(http_mod, "USER_AGENT", "test-agent", raising=False)

@pytest.fixture
def fast_sleep(monkeypatch):
    calls = []
    def fake_sleep(s):
        calls.append(s)
    monkeypatch.setattr(http_mod.time, "sleep", fake_sleep)
    return calls

# -------- build_headers --------

def test_build_headers_non_github():
    h = http_mod.build_headers("https://example.com/foo")
    assert h == {"User-Agent": "test-agent"}

def test_build_headers_github_with_token():
    h = http_mod.build_headers("https://api.github.com/repos/x/y", token="abc123")
    assert h["User-Agent"] == "test-agent"
    assert h["Authorization"] == "Bearer abc123"
    assert h["X-GitHub-Api-Version"] == "2022-11-28"
    assert h["Accept"] == "application/vnd.github+json"

def test_build_headers_github_without_token():
    h = http_mod.build_headers("https://api.github.com/search/repositories")
    assert "Authorization" not in h
    assert h["User-Agent"] == "test-agent"

# -------- http_get: success --------

@responses.activate
def test_http_get_success_first_try():
    responses.add(
        responses.GET, "https://example.com/data",
        json={"ok": True}, status=200
    )
    r = http_mod.http_get("https://example.com/data")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

# -------- http_get: 5xx retries with backoff --------

@responses.activate
def test_http_get_retries_on_5xx_with_backoff(fast_sleep):
    responses.add(responses.GET, "https://example.com", status=500)
    responses.add(responses.GET, "https://example.com", status=502)
    responses.add(responses.GET, "https://example.com", json={"ok": 1}, status=200)

    r = http_mod.http_get("https://example.com", retries=3, base_sleep=1.0)
    assert r.status_code == 200
    # sleeps should be 1.0 then 2.0 before success
    assert fast_sleep == [1.0, 2.0]

# -------- http_get: network errors with backoff --------

def test_http_get_retries_on_connection_error(monkeypatch, fast_sleep):
    calls = {"n": 0}
    def fake_get(url, headers, timeout):
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.ConnectionError("boom")
        class Resp:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return {"ok": True}
        return Resp()

    monkeypatch.setattr(http_mod.requests, "get", fake_get)
    r = http_mod.http_get("https://example.com", retries=5, base_sleep=0.5)
    assert r.status_code == 200
    assert fast_sleep == [0.5, 1.0]  # two retries before success

# -------- http_get: non-retryable 4xx --------

@responses.activate
def test_http_get_404_raises_and_no_retry(fast_sleep):
    responses.add(responses.GET, "https://example.com/missing", status=404)
    with pytest.raises(requests.HTTPError):
        http_mod.http_get("https://example.com/missing", retries=5)
    # no sleep because no retry
    assert fast_sleep == []

# -------- rate limit: 429 with Retry-After numeric --------

@responses.activate
def test_http_get_429_retry_after_numeric(monkeypatch, fast_sleep, capsys):
    responses.add(responses.GET, "https://example.com", status=429,
                  headers={"Retry-After": "7"})
    responses.add(responses.GET, "https://example.com", json={"ok": 1}, status=200)

    r = http_mod.http_get("https://example.com")
    assert r.status_code == 200
    # countdown should sleep in chunks <=60; here it's just one call of 7
    assert fast_sleep == [7]
    # stderr contains the rate-limit message
    captured = capsys.readouterr()
    assert "HTTP 429 on https://example.com" in captured.err

# -------- rate limit: 429 without Retry-After -> FIFTEEN_MIN fallback --------

@responses.activate
def test_http_get_429_missing_retry_after_uses_fifteen_min(fast_sleep):
    responses.add(responses.GET, "https://example.com", status=429)
    responses.add(responses.GET, "https://example.com", json={"ok": 1}, status=200)
    http_mod.http_get("https://example.com")
    assert fast_sleep == [15]

# -------- rate limit: GitHub 403 with remaining=0 and future reset --------

@responses.activate
def test_http_get_github_403_rate_limit_waits_until_reset(monkeypatch, fast_sleep):
    now = int(_time.time())
    reset = now + 9
    responses.add(
        responses.GET, "https://api.github.com/rate_limited",
        status=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)}
    )
    responses.add(
        responses.GET, "https://api.github.com/rate_limited",
        json={"ok": True}, status=200
    )
    r = http_mod.http_get("https://api.github.com/rate_limited")
    assert r.status_code == 200
    # sleeps ~9 (exact value depends on max(0, reset-now))
    assert fast_sleep[-1] in (8, 9)  # tolerate 1s drift

# -------- rate limit: GitHub 403 with remaining=0 and past reset -> FIFTEEN_MIN --------

@responses.activate
def test_http_get_github_403_rate_limit_past_reset_uses_fallback(fast_sleep):
    reset = str(int(_time.time()) - 1)
    responses.add(
        responses.GET, "https://api.github.com/rl",
        status=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset}
    )
    responses.add(
        responses.GET, "https://api.github.com/rl",
        json={"ok": True}, status=200
    )
    r = http_mod.http_get("https://api.github.com/rl")
    assert r.status_code == 200
    assert fast_sleep == [15]

# -------- 403 not a rate limit -> raises --------

@responses.activate
def test_http_get_github_403_non_rate_limit_raises(fast_sleep):
    responses.add(
        responses.GET, "https://api.github.com/some",
        status=403,
        headers={"X-RateLimit-Remaining": "10"}  # not a rate-limit
    )
    with pytest.raises(requests.HTTPError):
        http_mod.http_get("https://api.github.com/some")
    assert fast_sleep == []

# -------- retries exhausted --------

def test_http_get_retries_exhausted(monkeypatch, fast_sleep):
    def always_timeout(url, headers, timeout):
        raise requests.Timeout("zzz")
    monkeypatch.setattr(http_mod.requests, "get", always_timeout)
    with pytest.raises(requests.Timeout):
        http_mod.http_get("https://example.com", retries=2, base_sleep=0.1)
    assert fast_sleep == [0.1, 0.2]
