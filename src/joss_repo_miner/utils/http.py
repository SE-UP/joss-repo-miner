# src/joss_repo_miner/utils/http.py
from __future__ import annotations
import sys, time, requests
from typing import Optional, Dict
from ..config import USER_AGENT, FIFTEEN_MIN

def build_headers(url: str, token: str = "") -> Dict[str, str]:
    h = {"User-Agent": USER_AGENT}
    if url.startswith("https://api.github.com") and token:
        h["Authorization"] = f"Bearer {token}"
        h["X-GitHub-Api-Version"] = "2022-11-28"
        h["Accept"] = "application/vnd.github+json"
    return h

def _countdown(seconds: int, why: str) -> None:
    print(f"[rate-limit] {why}; sleeping {seconds} sec...", file=sys.stderr)
    while seconds > 0:
        tick = min(60, seconds)
        time.sleep(tick)
        seconds -= tick

def _handle_rate_limit(resp: Optional[requests.Response], url: str) -> bool:
    if resp is None:
        return False
    status = resp.status_code

    if status == 429:
        retry_after = resp.headers.get("Retry-After")
        wait = int(retry_after) if (retry_after and retry_after.isdigit()) else FIFTEEN_MIN
        _countdown(wait, f"HTTP 429 on {url}")
        return True

    if "github.com" in url and status == 403:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        reset = resp.headers.get("X-RateLimit-Reset")
        if remaining == "0":
            now = int(time.time())
            try:
                wait = max(0, int(reset) - now) or FIFTEEN_MIN
            except Exception:
                wait = FIFTEEN_MIN
            _countdown(wait, f"GitHub 403 rate limit on {url}")
            return True
    return False

def http_get(url: str, *, token: str = "", timeout: int = 30, retries: int = 5, base_sleep: float = 1.0) -> requests.Response:
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.get(url, headers=build_headers(url, token), timeout=timeout)
            if _handle_rate_limit(resp, url):
                continue
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            resp = e.response
            if _handle_rate_limit(resp, url):
                continue
            if attempt <= retries and (resp is None or 500 <= resp.status_code < 600):
                sleep = base_sleep * (2 ** (attempt - 1))
                print(f"[warn] {url} -> HTTP {getattr(resp, 'status_code','ERR')}; retry in {sleep:.1f}s", file=sys.stderr)
                time.sleep(sleep); continue
            raise
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt <= retries:
                sleep = base_sleep * (2 ** (attempt - 1))
                print(f"[warn] network error on {url}: {e}; retry in {sleep:.1f}s", file=sys.stderr)
                time.sleep(sleep); continue
            raise
