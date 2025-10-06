# src/joss_repo_miner/cli.py
from __future__ import annotations
import argparse, sys
from typing import List, Set, Tuple

from .config import GITHUB_TOKEN
from .utils.io import CsvWriter, Record
from .scrapers.published import PublishedScraper
from .scrapers.accepted import AcceptedScraper

def scrape(statuses: List[str], max_pages_published: int, max_pages_accepted: int,
           politeness_sleep: float, writer: CsvWriter) -> None:
    seen: Set[Tuple[str, str, str, str]] = set()

    if "published" in statuses:
        pub = PublishedScraper(politeness_sleep=politeness_sleep)
        for paper_url in pub.iter_paper_urls(max_pages=max_pages_published):
            try:
                rec = pub.parse_paper(paper_url)
                key = ("published", rec.paper_url or "", "", rec.repo_url or "")
                if key not in seen:
                    seen.add(key); writer.add(rec)
            except Exception as e:
                print(f"[warn] published parse failed {paper_url}: {e}", file=sys.stderr)

    if "accepted" in statuses:
        acc = AcceptedScraper(politeness_sleep=politeness_sleep, token=GITHUB_TOKEN)
        if GITHUB_TOKEN:
            for issue in acc.iter_issue_json_api(max_pages=max_pages_accepted):
                try:
                    rec = acc.parse_issue_api(issue)
                    key = ("accepted", "", rec.issue_url or "", rec.repo_url or "")
                    if key not in seen:
                        seen.add(key); writer.add(rec)
                except Exception as e:
                    print(f"[warn] accepted(API) parse failed: {e}", file=sys.stderr)
        else:
            for issue_url in acc.iter_issue_urls_html(max_pages=max_pages_accepted):
                try:
                    rec = acc.parse_issue_html(issue_url)
                    key = ("accepted", "", rec.issue_url or "", rec.repo_url or "")
                    if key not in seen:
                        seen.add(key); writer.add(rec)
                except Exception as e:
                    print(f"[warn] accepted(HTML) parse failed {issue_url}: {e}", file=sys.stderr)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="joss-repo-miner",
        description="Command-line tool to scrape accepted, published JOSS repositories into CSV."
    )
    p.add_argument("--status", nargs="+", required=True,
                   choices=["accepted", "published"],
                   help="One or both statuses to scrape.")
    p.add_argument("--out", required=True, help="Final CSV path (a .part CSV is updated incrementally).")
    p.add_argument("--checkpoint-every", type=int, default=100, help="Write a checkpoint every N rows.")
    p.add_argument("--sleep", type=float, default=0.7, help="Seconds to sleep between index pages (politeness).")
    p.add_argument("--max-pages-published", type=int, default=0, help="Limit Published index pages (0 = all).")
    p.add_argument("--max-pages-accepted", type=int, default=0, help="Limit Accepted pages (API/HTML) (0 = all).")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    writer = CsvWriter(args.out, checkpoint_every=args.checkpoint_every)
    try:
        scrape(
            statuses=args.status,
            max_pages_published=args.max_pages_published,
            max_pages_accepted=args.max_pages_accepted,
            politeness_sleep=args.sleep,
            writer=writer,
        )
        writer.finalize()
    except Exception as e:
        print(f"[fatal] {e}. Partial data saved at {writer.part_file}", file=sys.stderr)
        try:
            writer.flush()
        finally:
            raise SystemExit(1)
