# src/joss_repo_miner/config.py
from __future__ import annotations
import os
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()  # reads .env in project root if present

GITHUB_TOKEN = (os.getenv("GITHUB_TOKEN") or "").strip()
GITHUB_USERNAME = (os.getenv("GITHUB_USERNAME") or "joss-repo-miner").strip()

USER_AGENT = f"joss-repo-miner (+user:{GITHUB_USERNAME})"

BASE_JOSS = "https://joss.theoj.org"
BASE_REVIEWS_HTML = "https://github.com/openjournals/joss-reviews/issues"
BASE_REVIEWS_API = "https://api.github.com/repos/openjournals/joss-reviews/issues"

FIFTEEN_MIN = 15 * 60
