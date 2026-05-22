# src/joss_repo_miner/config.py
"""Configuration settings and environment variable initialization for the JOSS repository miner.

This module loads environment variables via python-dotenv, sets up global constants,
and structures authentication variables and baseline API/HTML scrape targets.
"""

from __future__ import annotations
import os
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()  # reads .env in project root if present

# Authentication information gathered from system environment variables
GITHUB_TOKEN = (os.getenv("GITHUB_TOKEN") or "").strip()
GITHUB_USERNAME = (os.getenv("GITHUB_USERNAME") or "joss-repo-miner").strip()

# Custom User-Agent header required by GitHub API guidelines
USER_AGENT = f"joss-repo-miner (+user:{GITHUB_USERNAME})"

# Baseline target endpoints for the scrapers
BASE_JOSS = "https://joss.theoj.org"
BASE_REVIEWS_HTML = "https://github.com/openjournals/joss-reviews/issues"
BASE_REVIEWS_API = "https://api.github.com/repos/openjournals/joss-reviews/issues"

# Default rate-limiting duration constants
FIFTEEN_MIN = 15 * 60