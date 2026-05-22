# src/joss_repo_miner/utils/http.py
"""HTTP network request utilities and failure-handling layers.

This module encapsulates network request executions, dynamically structures
platform-specific request headers, handles exponential backoff retry cycles on
transient network errors, and intercepts explicit rate-limiting conditions for 
both general web addresses and GitHub API platform endpoints.
"""

from __future__ import annotations
import sys
import time
import requests
from typing import Optional, Dict
from ..config import USER_AGENT, FIFTEEN_MIN


def build_headers(url: str, token: str = "") -> Dict[str, str]:
    """Builds appropriate HTTP request headers depending on the target destination.

    Args:
        url (str): The destination endpoint URL for the network request.
        token (str): An optional access token used for GitHub API authorization.

    Returns:
        Dict[str, str]: A dictionary tracking headers including user-agents and
        API configuration properties.
    """
    h = {"User-Agent": USER_AGENT}
    if url.startswith("https://api.github.com") and token:
        h["Authorization"] = f"Bearer {token}"
        h["X-GitHub-Api-Version"] = "2022-11-28"
        h["Accept"] = "application/vnd.github+json"
    return h


def _countdown(seconds: int, why: str) -> None:
    """Blocks execution via controlled sleeping loops while outputting progress metrics.

    Args:
        seconds (int): Total delay durations required in seconds.
        why (str): A descriptive contextual log note stating the cause for delaying.

    Returns:
        None
    """
    print(f"[rate-limit] {why}; sleeping {seconds} sec...", file=sys.stderr)
    while seconds > 0:
        tick = min(60, seconds)
        time.sleep(tick)
        seconds -= tick


def _handle_rate_limit(resp: Optional[requests.Response], url: str) -> bool:
    """Inspects response status attributes to intercept and manage platform rate limiting.

    Args:
        resp (Optional[requests.Response]): The network response metadata wrapper.
        url (str): The absolute link resource address targeted.

    Returns:
        bool: True if a rate limit event occurred and was handled by blocking,
        False otherwise.
    """
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



def http_get(
    url: str, *, token: str = "", timeout: int = 30, retries: int = 5, base_sleep: float = 1.0
) -> requests.Response:
    """Executes a defensive HTTP GET network transfer sequence against a target URL.

    Maintains long-running conditional loops managing platform rate blocks or
    transient status codes via parameterized exponential backoff delay loops.

    Args:
        url (str): Target asset or endpoint string location.
        token (str): Authentication token supplied directly into API pathways.
        timeout (int): Total seconds allowed before raising internal timeout exceptions.
        retries (int): Maximum attempts permitted on server-side fault distributions.
        base_sleep (float): Linear anchor factor applied to compute exponential backoffs.

    Returns:
        requests.Response: A successful HTTP network state data payload package.

    Raises:
        requests.HTTPError: If a client or permanent server exception persists.
        requests.ConnectionError: On ongoing lower-level network interface issues.
        requests.Timeout: If the data stream exceeds timeout allocations across all steps.
    """
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
                print(
                    f"[warn] {url} -> HTTP {getattr(resp, 'status_code', 'ERR')}; retry in {sleep:.1f}s",
                    file=sys.stderr,
                )
                time.sleep(sleep)
                continue
            raise
        except (requests.ConnectionError, requests.Timeout) as e:  
            if attempt <= retries:
                sleep = base_sleep * (2 ** (attempt - 1))
                print(
                    f"[warn] network error on {url}: {e}; retry in {sleep:.1f}s", file=sys.stderr
                )
                time.sleep(sleep)
                continue
            raise