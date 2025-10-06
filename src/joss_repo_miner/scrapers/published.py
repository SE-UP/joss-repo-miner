# src/joss_repo_miner/scrapers/published.py
from __future__ import annotations
import time
from typing import Iterable, Set, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from ..config import BASE_JOSS
from ..utils.http import http_get
from ..utils.parsing import clean_text, DOI_RE, first_repo_link_from_text
from ..utils.io import Record

class PublishedScraper:
    """Scrape JOSS 'Published' index and paper pages."""
    def __init__(self, politeness_sleep: float = 0.7):
        self.polite = politeness_sleep

    def iter_paper_urls(self, max_pages: int = 0) -> Iterable[str]:
        seen: Set[str] = set()
        page = 1
        while True:
            url = f"{BASE_JOSS}/papers/published?page={page}"
            soup = BeautifulSoup(http_get(url).text, "html.parser")
            links = [urljoin(BASE_JOSS, a.get("href", "")) for a in soup.select("a[href^='/papers/10.21105/joss.']")]
            if not links: break
            new = 0
            for u in links:
                if u not in seen:
                    seen.add(u); new += 1
                    yield u
            if (max_pages and page >= max_pages) or new == 0:
                break
            page += 1; time.sleep(self.polite)

    def parse_paper(self, paper_url: str) -> Record:
        html = http_get(paper_url).text
        soup = BeautifulSoup(html, "html.parser")
        title_el = soup.find("h1")
        title = clean_text(title_el.get_text(" ", strip=True)) if title_el else None
        m = DOI_RE.search(paper_url) or DOI_RE.search(html)
        doi = f"10.21105/joss.{m.group(1)}" if m else None
        joss_id = m.group(1) if m else None

        repo_url: Optional[str] = None
        btn = soup.find("a", string=lambda s: s and ("Software repository" in s or "Repository" in s))
        if btn and btn.has_attr("href"):
            repo_url = btn["href"]
        if not repo_url:
            repo_url = first_repo_link_from_text(html)

        return Record(
            status="published", paper_url=paper_url, issue_url=None,
            doi=doi, joss_id=joss_id, title=title, repo_url=repo_url
        )
