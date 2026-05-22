# src/joss_repo_miner/scrapers/published.py
"""Scraper implementations targeting officially published JOSS papers.

This module provides the PublishedScraper class which handles crawling through
the public JOSS website, dynamically processes index responses (supporting both 
traditional HTML pages and XML/Atom feed formats), and extracts full paper metadata.
"""

from __future__ import annotations
import time
from typing import Iterable, Set, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from ..config import BASE_JOSS
from ..utils.http import http_get
from ..utils.parsing import clean_text, DOI_RE, extract_repo_href
from ..utils.io import Record

class PublishedScraper:
    """Scrape JOSS 'Published' index and paper pages."""
    def __init__(self, politeness_sleep: float = 0.7):
        """Initializes the scraper context with execution pacing details.

        Args:
            politeness_sleep (float): Seconds to sleep between page network requests.

        Returns:
            None
        """
        self.polite = politeness_sleep

    def iter_paper_urls(self, max_pages: int = 0) -> Iterable[str]:
        """Crawls and reads paginated indices to discover valid JOSS paper links.

        Detects whether incoming feeds are serving structured XML payloads or
        traditional markup layouts, filters out unique matches, and yields items.

        Args:
            max_pages (int): Upper bound limit of index page intervals to harvest (0 = all).

        Yields:
            str: Discovered absolute URLs pointing to detailed individual paper logs.
        """
        seen: Set[str] = set()
        page = 1
        while True:
            print(f"Scraping page {page}/{max_pages}")
            url = f"{BASE_JOSS}/papers/published?page={page}"
            resp = http_get(url)
            text = resp.text
            ctype = (resp.headers.get("Content-Type") or "").lower()

            # Detect Atom/XML vs HTML
            if "xml" in ctype or text.lstrip().startswith("<?xml"):
                soup = BeautifulSoup(text, "lxml-xml")  # requires lxml
                hrefs = [tag.get("href", "") for tag in soup.find_all("link")]
                links = [h for h in hrefs if "/papers/10.21105/joss." in h]
            else:
                soup = BeautifulSoup(text, "html.parser")
                links = [
                    urljoin(BASE_JOSS, a.get("href", ""))
                    for a in soup.select("a[href^='/papers/10.21105/joss.']")
                ]

            if not links:
                break

            new = 0
            for u in links:
                if u and u not in seen:
                    seen.add(u)
                    new += 1
                    yield u

            if (max_pages and page >= max_pages) or new == 0:
                break

            page += 1
            time.sleep(self.polite)

    def parse_paper(self, paper_url: str) -> Record:
        """Parses a published JOSS paper page to collect structured tracking tokens.

        Isolates document object properties like title headers, internal DOIs, 
        explicit repository nodes, and verifies endpoint routing availability.

        Args:
            paper_url (str): Absolute network link corresponding to the target paper.

        Returns:
            Record: A structured metadata dataset container instance.
        """
        html = http_get(paper_url).text
        soup = BeautifulSoup(html, "html.parser")
        repo_url = extract_repo_href(soup)

        title_el = soup.find("h1")
        title = clean_text(title_el.get_text(" ", strip=True)) if title_el else None
        m = DOI_RE.search(paper_url) or DOI_RE.search(html)
        doi = f"10.21105/joss.{m.group(1)}" if m else None
        joss_id = m.group(1) if m else None

        # Prefer explicit repository button; fall back to first code-host link
        repo_url: Optional[str] = None
        btn = soup.find("a", string=lambda s: isinstance(s, str) and "Software repository" in s)
        if btn and btn.has_attr("href"):
            repo_url = btn["href"]
        if not repo_url:
            repo_url = extract_repo_href(html)

        # Check if the repository is accessible
        status_code = http_get(repo_url).status_code

        return Record(
            status="published",
            paper_url=paper_url,
            issue_url=None,
            doi=doi,
            joss_id=joss_id,
            title=title,
            repo_url=repo_url,
            repo_status_code=status_code
        )