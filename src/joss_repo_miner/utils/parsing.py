# src/joss_repo_miner/utils/parsing.py
from typing import Optional
from urllib.parse import urlparse

CODE_HOSTS = ("github.com", "gitlab.com", "codeberg.org", "bitbucket.org")
BLOCKED_OWNERS = {"openjournals", "joss"}  # avoid org links like github.com/openjournals/joss

def is_repo_like(href: str) -> bool:
    try:
        u = urlparse(href)
        if u.scheme not in ("http", "https"): return False
        if u.netloc not in CODE_HOSTS: return False
        parts = [p for p in u.path.split("/") if p]
        if len(parts) < 2: return False           # need owner/repo
        if parts[0].lower() in BLOCKED_OWNERS:    # skip JOSS org repos
            return False
        return True
    except Exception:
        return False

def extract_repo_href(soup) -> Optional[str]:
    # (1) Button area (most reliable)
    for sel in [
        "a.paper-btn[href]",                      # JOSS button class
        "a[href][title*='Repository' i]",
        "a[href]:contains('Software repository')",  # bs4’s :contains works only via lambda (see below)
    ]:
        for a in soup.select(sel) if "[" in sel else []:
            href = a.get("href", "").strip()
            if is_repo_like(href): return href

    # (1b) text-based match (case-insensitive) for “repository”
    a = soup.find("a", string=lambda s: isinstance(s, str) and "repository" in s.lower())
    if a:
        href = (a.get("href") or "").strip()
        if is_repo_like(href): return href

    # (2) Definition list fallback: <dt>Repository</dt><dd><a href=...>
    dt = soup.find(["dt","th"], string=lambda s: isinstance(s, str) and "repository" in s.lower())
    if dt:
        dd = dt.find_next(["dd","td"])
        if dd:
            a = dd.find("a", href=True)
            if a and is_repo_like(a["href"]): return a["href"].strip()

    # (3) Document-order scan but FILTERED (skip openjournals/joss etc.)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if is_repo_like(href): return href

    return None
