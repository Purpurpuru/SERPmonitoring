#!/usr/bin/env python3
"""
serp_fetcher.py
===============
Fetch Google Organic SERP data via DataforSEO v3 using the official
`dataforseo-client` wrapper and export results to CSV.

Documentation references
-----------------------
• General SERP: https://docs.dataforseo.com/v3/serp/overview/  
• Google SERP specifics: https://docs.dataforseo.com/v3/serp/google/overview/

Environment variables
---------------------
DFS_LOGIN     – DataforSEO API login  
DFS_PASSWORD  – DataforSEO API password

Usage
-----
```bash
python serp_fetcher.py keywords.txt out.csv \
  --location-code 2840 --language-code en --device desktop --depth 20 \
  --people-also-ask-depth 0 --group-organic-results --load-async-ai-overview
```
Run `python serp_fetcher.py -h` for the full option list.
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from dataforseo_client.api.serp_api import SerpApi
from dataforseo_client.models.serp_google_organic_live_advanced_request_info import (
    SerpGoogleOrganicLiveAdvancedRequestInfo,
)
from dataforseo_client import configuration as dfs_config, api_client as dfs_provider
from dataforseo_client.rest import ApiException

RATE_LIMIT_DELAY = 1.0  # seconds (free plan = 1 RPS)
MAX_RETRIES = 5
CSV_FIELDS = ["keyword", "rank", "title", "snippet", "url", "is_autodna"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_keywords(path: Path | None, single_kw: str | None) -> List[str]:
    if single_kw:
        return [single_kw.strip()]
    if not path or not path.exists():
        logging.error("Keywords file not found and --keyword not provided.")
        sys.exit(1)
    return [k.strip() for k in path.read_text(encoding="utf-8").splitlines() if k.strip()]


def build_task(keyword: str, args: argparse.Namespace) -> SerpGoogleOrganicLiveAdvancedRequestInfo:
    task = SerpGoogleOrganicLiveAdvancedRequestInfo(
        keyword=keyword,
        language_code=args.language_code,
        location_code=args.location_code,
        device=args.device,
        depth=args.depth,
        se_domain=args.se_domain,
    )
    if args.people_also_ask_depth:
        task.people_also_ask_depth = args.people_also_ask_depth
    if args.group_organic_results:
        task.group_organic_results = True
    if args.load_async_ai_overview:
        task.load_async_ai_overview = True
    if args.target:
        task.target = args.target
    return task


def parse_items(keyword: str, items: List[Dict], depth: int) -> List[Dict]:
    rows: List[Dict[str, str | int]] = []
    for itm in items:
        if itm.get("type") != "organic":
            continue
        rank = int(itm.get("rank_absolute", 0))
        if rank <= 0 or rank > depth:
            continue
        url = itm.get("url", "")
        rows.append(
            {
                "keyword": keyword,
                "rank": rank,
                "title": itm.get("title", ""),
                "snippet": itm.get("description", ""),
                "url": url,
                "is_autodna": "true" if "autodna" in urlparse(url).netloc.lower() else "false",
            }
        )
    return rows


def write_csv(rows: List[Dict], dest: Path) -> None:
    if not rows:
        logging.warning("No data returned – CSV will not be created.")
        return
    with dest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["keyword"], r["rank"])))


# CLI and main as previously implemented
