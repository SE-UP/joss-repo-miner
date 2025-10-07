# src/joss_repo_miner/utils/parsing.py
from __future__ import annotations

import os
import re
from typing import Optional, Any
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

# --------- regex & constants --------- #

WS = re.compile(r"\s+")
DOI_RE = re.compile(r"10\.21105/joss\.(\d+)")
TRAILING_JUNK = ").,;\"'>*"

# Known public forges (exact match, after stripping "www.")
CODE_HOSTS = ("github.com", "gitlab.com", "codeberg.org", "bitbucket.org")

# Block these owners (avoid org/home links like github.com/openjournals/joss)
BLOCKED_OWNERS = {"openjournals", "joss"}

# ======= NEW: knobs to allow more hosts =======

# Allow ANY host that looks like owner/repo (overrides host checks below)
ALLOW_ANY_HOST = os.getenv("ALLOW_ANY_HOST", "0").lower() in {"1", "true", "yes"}

# Comma-separated explicit allowlist additions (e.g., "code.europa.eu,forge.inrae.fr")
EXTRA_CODE_HOSTS = {
    h.strip().lower()
    for h in (os.getenv("EXTRA_CODE_HOSTS", "").split(","))
    if h.strip()
}

# Accept hosts containing any of these substrings (covers many self-hosted forges)
ALLOWED_HOST_SUBSTRINGS = {
    "gitlab", "gitea", "sr.ht", "sourcehut",
    "code.", "forge.", "git.", "cgit",
    "codebase", "c4science", "savannah", "sourceforge",
}

# --------- helpers --------- #

def clean_text(s: Optional[str]) -> Optional[str]:
    """Collapse whitespace and strip."""
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

def _host_allowed(host: str) -> bool:
    host = _normalize_host(host)
    if host in CODE_HOSTS:
        return True
    if host in EXTRA_CODE_HOSTS:
        return True
    if any(substr in host for substr in ALLOWED_HOST_SUBSTRINGS):
        return True
    return False

def is_repo_like(href: str) -> bool:
    """
    Accept if:
      - scheme is http/https
      - host is allowed (or ALLOW_ANY_HOST=1)
      - path looks like owner/repo (>=2 segments), except special forges (SourceForge/Savannah/C4Science) where >=1 is ok
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

        # Special forges: project pages are okay with one segment
        special_host = any(s in host for s in ("sourceforge.net", "savannah.gnu.org", "savannah.nongnu.org", "c4science.ch"))
        if special_host:
            return (_host_allowed(host) or ALLOW_ANY_HOST) and owner not in BLOCKED_OWNERS

        # Default: require owner/repo
        if len(parts) < 2:
            return False
        if owner in BLOCKED_OWNERS:
            return False

        return _host_allowed(host) or ALLOW_ANY_HOST
    except Exception:
        return False

def first_repo_link_from_text(text: str) -> Optional[str]:
    """
    Very loose fallback: first URL-looking thing in text that passes is_repo_like().
    (Now NOT limited to specific hosts.)
    """
    m = re.search(r"https?://[^\s)>\"]+", text or "", re.I)
    if not m:
        return None
    href = _sanitize_href(m.group(0))
    return href if is_repo_like(href) else None

# --------- main extractor --------- #

def extract_repo_href(doc: Any) -> Optional[str]:
    """
    Extract the most likely software repository URL from a JOSS paper page.

    Accepts either:
      - a BeautifulSoup object, or
      - an HTML string (it will be parsed here).

    Strategy:
      1) Anchor whose *text* mentions 'repository'.
      2) <dt>/<th> 'Repository' → next <dd>/<td> link.
      3) First acceptable link by is_repo_like().
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
