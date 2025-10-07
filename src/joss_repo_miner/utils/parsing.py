# src/joss_repo_miner/utils/parsing.py
from __future__ import annotations

import re
from typing import Optional, Any
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

WS = re.compile(r"\s+")
DOI_RE = re.compile(r"10\.21105/joss\.(\d+)")
TRAILING_JUNK = ").,;\"'>*"

# Block these owners (avoid org/home links like github.com/openjournals/joss)
BLOCKED_OWNERS = {"openjournals", "joss"}

def clean_text(s: Optional[str]) -> Optional[str]:
    return None if not s else WS.sub(" ", s).strip()

def _normalize_host(host: str) -> str:
    host = (host or "").strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host

def _sanitize_href(href: str) -> str:
    """Strip trailing punctuation, query/fragment, keep scheme/host/path."""
    href = (href or "").strip().rstrip(TRAILING_JUNK)
    try:
        u = urlparse(href)
        u = u._replace(params="", query="", fragment="")
        return urlunparse(u)
    except Exception:
        return href

def is_repo_like(href: str) -> bool:
    """
    Accept ANY host as long as:
      - scheme is http/https
      - path looks like owner/repo (>=2 segments)
      - OR it's a special forge where project pages (>=1 segment) are OK
      - first path segment (owner) is not in BLOCKED_OWNERS
    """
    try:
        href = _sanitize_href(href)
        u = urlparse(href)
        if u.scheme not in ("http", "https"):
            return False

        host = _normalize_host(u.netloc)
        parts = [p for p in (u.path or "").split("/") if p]
        if not parts:
            return False

        owner = parts[0].lower()

        # Special forges that may not follow owner/repo strictly
        special_hosts = (
            "sourceforge.net",
            "savannah.gnu.org",
            "savannah.nongnu.org",
            "c4science.ch",
        )
        if any(h in host for h in special_hosts):
            return owner not in BLOCKED_OWNERS  # accept project page

        # Default: need owner/repo
        if len(parts) < 2:
            return False
        if owner in BLOCKED_OWNERS:
            return False

        return True
    except Exception:
        return False

def first_repo_link_from_text(text: str) -> Optional[str]:
    """
    Very loose fallback: first URL-looking thing in text that passes is_repo_like().
    (Generic URL regex; not limited to specific hosts.)
    """
    m = re.search(r"https?://[^\s)>\"]+", text or "", re.I)
    if not m:
        return None
    href = _sanitize_href(m.group(0))
    return href if is_repo_like(href) else None

def extract_repo_href(doc: Any) -> Optional[str]:
    """
    Extract most likely repo URL from a JOSS paper page.
    Accepts a BeautifulSoup object or an HTML string.

    Strategy:
      1) <a> whose text mentions 'repository'
      2) <dt>/<th> 'Repository' → next <dd>/<td> link
      3) First acceptable link by is_repo_like()
    """
    soup = doc if hasattr(doc, "find_all") else BeautifulSoup(doc or "", "html.parser")

    # (1) anchors mentioning “repository”
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if "repository" in txt:
            href = _sanitize_href(a["href"])
            if is_repo_like(href):
                return href

    # (2) definition list: <dt>/<th> Repository → next <dd>/<td> link
    for dt in soup.find_all(["dt", "th"]):
        label = (dt.get_text() or "").strip().lower()
        if "repository" in label:
            dd = dt.find_next(["dd", "td"])
            if dd:
                a = dd.find("a", href=True)
                if a:
                    href = _sanitize_href(a["href"])
                    if is_repo_like(href):
                        return href

    # (3) last resort: first acceptable link
    for a in soup.find_all("a", href=True):
        href = _sanitize_href(a["href"])
        if is_repo_like(href):
            return href

    return None
