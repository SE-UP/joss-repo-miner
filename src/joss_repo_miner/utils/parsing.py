# src/joss_repo_miner/utils/parsing.py
from __future__ import annotations

import re
from typing import Optional, Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

# --------- regex & constants --------- #

WS = re.compile(r"\s+")
DOI_RE = re.compile(r"10\.21105/joss\.(\d+)")

# Only accept links that look like real code hosts (owner/repo),
# and avoid JOSS’s own org links which often appear in headers/footers.
CODE_HOSTS = ("github.com", "gitlab.com", "codeberg.org", "bitbucket.org")
BLOCKED_OWNERS = {"openjournals", "joss"}

# --------- helpers --------- #

def clean_text(s: Optional[str]) -> Optional[str]:
    """Collapse whitespace and strip."""
    return None if not s else WS.sub(" ", s).strip()

def is_repo_like(href: str) -> bool:
    """Heuristic: http(s) URL, known host, at least owner/repo, not a blocked owner."""
    try:
        u = urlparse(href)
        if u.scheme not in ("http", "https"):
            return False
        if u.netloc not in CODE_HOSTS:
            return False
        parts = [p for p in u.path.split("/") if p]
        if len(parts) < 2:
            return False  # need owner/repo
        if parts[0].lower() in BLOCKED_OWNERS:
            return False
        return True
    except Exception:
        return False

def first_repo_link_from_text(text: str) -> Optional[str]:
    """
    Very loose fallback: find the first code-hosting URL in plain text,
    then run it through is_repo_like() for sanity.
    """
    m = re.search(
        r"https?://(?:www\.)?(?:github\.com|gitlab\.com|codeberg\.org|bitbucket\.org)/[^\s)>\"]+",
        text or "",
        re.I,
    )
    if not m:
        return None
    href = m.group(0).rstrip(").,;\"'>")
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
      3) First code-hosting link on the page (filtered).
    """
    soup = doc if hasattr(doc, "find_all") else BeautifulSoup(doc or "", "html.parser")

    # (1) anchors mentioning “repository”
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if "repository" in txt:
            href = a["href"].strip()
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
                    href = a["href"].strip()
                    if is_repo_like(href):
                        return href

    # (3) last resort: first code-hosting link on the page (filtered)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if is_repo_like(href):
            return href

    return None
