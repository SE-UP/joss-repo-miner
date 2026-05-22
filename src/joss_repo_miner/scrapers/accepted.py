# src/joss_repo_miner/scrapers/accepted.py
"""Scraper implementations targeting accepted JOSS papers.

This module provides the AcceptedScraper class which handles extraction of 
accepted publication records via either the GitHub REST API endpoints or an
HTML parsing fallback extraction process targeting the joss-reviews repository.
"""

from __future__ import annotations
import time
from typing import Iterable, List, Dict, Any, Optional
from bs4 import BeautifulSoup

from ..config import BASE_REVIEWS_API, BASE_REVIEWS_HTML
from ..utils.http import http_get
from ..utils.parsing import clean_text, DOI_RE, first_repo_link_from_text
from ..utils.io import Record

class AcceptedScraper:
    """Scrape 'accepted' review issues (prefers GitHub API if token present)."""
    def __init__(self, politeness_sleep: float = 0.7, token: str = ""):
        """Initializes the scraper context with execution pacing and auth details.

        Args:
            politeness_sleep (float): Seconds to sleep between page network requests.
            token (str): Optional authentication token used for GitHub API pathways.

        Returns:
            None
        """
        self.polite = politeness_sleep
        self.token = token

    # API (preferred)
    def iter_issue_json_api(self, max_pages: int = 0) -> Iterable[Dict[str, Any]]:
        """Iterates over paginated GitHub API endpoints to yield closed accepted issues.

        Args:
            max_pages (int): Upper bound limit of index page intervals to harvest (0 = all).

        Yields:
            Dict[str, Any]: Individual raw issue data payloads from the API server.
        """
        if not self.token:
            return
        page = 1; per_page = 100
        while True:
            url = f"{BASE_REVIEWS_API}?state=closed&labels=accepted&per_page={per_page}&page={page}"
            data = http_get(url, token=self.token).json()
            if not data: break
            for issue in data:
                if "pull_request" in issue:  # skip PRs
                    continue
                yield issue
            if max_pages and page >= max_pages: break
            page += 1; time.sleep(self.polite)

    def parse_issue_api(self, issue: Dict[str, Any]) -> Record:
        """Extracts text structures out of raw JSON issue bodies into a Record layout.

        Args:
            issue (Dict[str, Any]): A single raw dictionary payload for a target issue.

        Returns:
            Record: A structured metadata dataset container instance.
        """
        title = clean_text(issue.get("title"))
        issue_url = issue.get("html_url")
        body = issue.get("body") or ""
        repo_url = first_repo_link_from_text(body)
        m = DOI_RE.search(body)
        doi = f"10.21105/joss.{m.group(1)}" if m else None
        joss_id = m.group(1) if m else None
        return Record(
            status="accepted", paper_url=None, issue_url=issue_url,
            doi=doi, joss_id=joss_id, title=title, repo_url=repo_url
        )

    # HTML fallback
    def iter_issue_urls_html(self, max_pages: int = 0) -> Iterable[str]:
        """Crawls HTML index sheets directly when executing public fallback routines.

        Args:
            max_pages (int): Upper bound limit of index page intervals to harvest (0 = all).

        Yields:
            str: Resolved target web hyperlinks pointing to repository review items.
        """
        page = 1
        while True:
            url = f"{BASE_REVIEWS_HTML}?q=is%3Aissue+is%3Aclosed+label%3Aaccepted&page={page}"
            soup = BeautifulSoup(http_get(url, token=self.token).text, "html.parser")
            links: List[str] = []
            for a in soup.select("a.Link--primary[href*='/openjournals/joss-reviews/issues/']"):
                href = a.get("href", "")
                links.append("https://github.com" + href if href.startswith("/") else href)
            if not links: break
            for u in links: yield u
            if max_pages and page >= max_pages: break
            page += 1; time.sleep(self.polite)

    def parse_issue_html(self, issue_url: str) -> Record:
        """Parses a public HTML response string to isolate metadata tokens into a Record.

        Args:
            issue_url (str): Absolute network link corresponding to a tracking thread.

        Returns:
            Record: A structured metadata dataset container instance.
        """
        html = http_get(issue_url, token=self.token).text
        soup = BeautifulSoup(html, "html.parser")
        title_el = soup.find("span", {"class": "js-issue-title"})
        title = clean_text(title_el.get_text(" ", strip=True)) if title_el else None
        repo_url = first_repo_link_from_text(html)
        m = DOI_RE.search(html)
        doi = f"10.21105/joss.{m.group(1)}" if m else None
        joss_id = m.group(1) if m else None
        return Record(
            status="accepted", paper_url=None, issue_url=issue_url,
            doi=doi, joss_id=joss_id, title=title, repo_url=repo_url
        )