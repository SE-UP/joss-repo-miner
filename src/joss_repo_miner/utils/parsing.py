# src/joss_repo_miner/utils/parsing.py
from __future__ import annotations
import re
from typing import Optional

WS = re.compile(r"\s+")
DOI_RE = re.compile(r"10\.21105/joss\.(\d+)")

# Loosened host filter to catch common/self-hosted GitLab patterns
GIT_HOST_RE = re.compile(
    r"https?://(?:www\.)?(?:github\.com|gitlab(?:\.[\w.-]+)?|codeberg\.org|bitbucket\.org)/[^\s)>\"]+",
    re.I,
)

def clean_text(s: Optional[str]) -> Optional[str]:
    return None if not s else WS.sub(" ", s).strip()

def first_repo_link_from_text(text: str) -> Optional[str]:
    m = GIT_HOST_RE.search(text or "")
    if not m:
        return None
    return m.group(0).rstrip(").,;\"'>")
