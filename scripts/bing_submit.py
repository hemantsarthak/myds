#!/usr/bin/env python3
"""bing_submit.py — submit a site's sitemap URLs to Bing Webmaster Tools (URL Submission API).

Requires a BWT API key (Settings -> API access -> API key) in the environment:
    BING_WMT_API_KEY            (see shared/.env; loaded automatically if present)

Docs: https://learn.microsoft.com/en-us/bingwebmaster/ (URL Submission API)
Quota: 10,000 URLs/day per site, max 500 URLs per request. Errors are per-batch.

Usage:
    python scripts/bing_submit.py --list
    python scripts/bing_submit.py --site hub --limit 20 --dry-run
    python scripts/bing_submit.py --site airport --limit 3000
    python scripts/bing_submit.py --all --limit 10000     # stays inside the daily quota
    python scripts/bing_submit.py --quota                 # show today's usage

State: shared/bing_quota.json  ({"YYYY-MM-DD": {"site": count, ...}} , 14-day retention)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SITES_DIR = ROOT / "sites"
QUOTA_FILE = SHARED / "bing_quota.json"

API_URL = "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch"
DAILY_LIMIT = 10_000
MAX_BATCH = 500
RETENTION_DAYS = 14
UA = "Mozilla/5.0 (compatible; myds-bing-submit/1.0)"

# slug -> (BWT siteUrl, public host). siteUrl must match the site exactly as added in BWT.
SITES: dict[str, tuple[str, str]] = {
    "hub": ("https://tekify.xyz/", "tekify.xyz"),
    "ifsc": ("https://ifsccodes.tekify.xyz/", "ifsccodes.tekify.xyz"),
    "airport": ("https://airportcodes.tekify.xyz/", "airportcodes.tekify.xyz"),
    "zip": ("https://zipcodes.tekify.xyz/", "zipcodes.tekify.xyz"),
    "places": ("https://places.tekify.xyz/", "places.tekify.xyz"),
    "colleges": ("https://colleges.tekify.xyz/", "colleges.tekify.xyz"),
    "calculators": ("https://calculators.tekify.xyz/", "calculators.tekify.xyz"),
}


# ---------------------------------------------------------------- credentials
def load_env() -> dict[str, str]:
    env = dict(os.environ)
    f = SHARED / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def api_key() -> str:
    key = load_env().get("BING_WMT_API_KEY", "").strip()
    if not key:
        sys.exit(
            "ERROR: BING_WMT_API_KEY is not set.\n"
            "Get it at https://www.bing.com/webmasters/ -> Settings -> API access -> API key,\n"
            "then add it to shared/.env as BING_WMT_API_KEY=...  (docs/BING.md)"
        )
    return key


# ---------------------------------------------------------------- sitemaps
def _locs(path: Path) -> list[str]:
    try:
        tree = ElementTree.parse(path)
    except ElementTree.ParseError as e:
        print(f"  ! unparseable sitemap {path}: {e}", file=sys.stderr)
        return []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = tree.getroot()
    tag = root.tag.split("}")[-1]
    if tag == "sitemapindex":
        out: list[str] = []
        for sm in root.findall("sm:sitemap/sm:loc", ns) or root.findall("sitemap/loc"):
            child = (sm.text or "").strip()
            if not child:
                continue
            name = child.rsplit("/", 1)[-1]
            local = path.parent / name
            out.extend(_locs(local) if local.exists() else [child])
        return out
    return [(loc.text or "").strip() for loc in (root.findall("sm:url/sm:loc", ns) or root.findall("url/loc")) if (loc.text or "").strip()]


def sitemap_urls(slug: str) -> list[str]:
    sm = SITES_DIR / slug / "site" / "sitemap.xml"
    if not sm.exists():
        sys.exit(f"ERROR: no sitemap for site '{slug}' at {sm}")
    urls = _locs(sm)
    host = SITES[slug][1] if slug in SITES else None
    if host:
        urls = [u for u in urls if host in u]
    # de-dupe, preserve order
    seen: set[str] = set()
    return [u for u in urls if not (u in seen or seen.add(u))]


# ---------------------------------------------------------------- quota ledger
def _today() -> str:
    return date.today().isoformat()


def load_quota() -> dict:
    if QUOTA_FILE.exists():
        try:
            return json.loads(QUOTA_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def save_quota(q: dict) -> None:
    cutoff = (date.today() - timedelta(days=RETENTION_DAYS)).isoformat()
    q = {d: v for d, v in q.items() if d >= cutoff}
    QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUOTA_FILE.write_text(json.dumps(q, indent=1, sort_keys=True))


def used_today(q: dict, site: str | None = None) -> int:
    day = q.get(_today(), {})
    return sum(day.values()) if site is None else int(day.get(site, 0))


# ---------------------------------------------------------------- API
def submit_batch(key: str, site_url: str, urls: list[str]) -> tuple[bool, str]:
    body = json.dumps({"siteUrl": site_url, "urlList": urls}).encode()
    req = urllib.request.Request(
        f"{API_URL}?apikey={key}",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return True, f"HTTP {r.status} {r.read().decode(errors='replace')[:300]}"
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:500]
        return False, f"HTTP {e.code} {msg}"
    except urllib.error.URLError as e:
        return False, f"network error: {e.reason}"


# ---------------------------------------------------------------- commands
def cmd_list() -> None:
    print(f"{'site':12} {'BWT siteUrl':38} {'sitemap URLs':>12}")
    for slug, (site_url, _host) in SITES.items():
        try:
            n = len(sitemap_urls(slug))
        except SystemExit:
            n = -1
        print(f"{slug:12} {site_url:38} {n:>12,}")


def cmd_quota() -> None:
    q = load_quota()
    today = _today()
    print(f"BWT URL Submission quota ledger ({QUOTA_FILE.relative_to(ROOT)})")
    print(f"today {today}: {used_today(q)} / {DAILY_LIMIT:,} used")
    for site in SITES:
        u = used_today(q, site)
        if u:
            print(f"  {site:12} {u:>6,}")
    other = {d: v for d, v in q.items() if d != today}
    if other:
        print("earlier days:")
        for d in sorted(other, reverse=True)[:RETENTION_DAYS]:
            print(f"  {d}  {sum(other[d].values()):>6,}")


def run_site(slug: str, key: str, limit: int, dry: bool, batch_size: int, delay: float) -> int:
    site_url = SITES[slug][0]
    urls = sitemap_urls(slug)[:limit]
    if not urls:
        print(f"[{slug}] no URLs")
        return 0
    q = load_quota()
    already = used_today(q, slug)
    room = max(0, DAILY_LIMIT - already)
    if room <= 0:
        print(f"[{slug}] daily quota already used ({already:,}); skipping")
        return 0
    urls = urls[:room]
    print(f"[{slug}] {len(urls):,} URLs -> {site_url} (batch={batch_size}, used today={already:,})")
    if dry:
        for u in urls[:10]:
            print("   DRY", u)
        print(f"   ... {max(0, len(urls) - 10):,} more")
        return 0

    ok_total = 0
    for i in range(0, len(urls), batch_size):
        chunk = urls[i : i + batch_size]
        ok, msg = submit_batch(key, site_url, chunk)
        print(f"  batch {i // batch_size + 1}: {len(chunk)} URLs -> {msg}")
        if ok and '"d":null' in msg.replace(" ", ""):
            ok_total += len(chunk)
            day = q.setdefault(_today(), {})
            day[slug] = int(day.get(slug, 0)) + len(chunk)
            save_quota(q)
        else:
            print(f"  ! batch failed, stopping this site after {ok_total:,} accepted")
            break
        if i + batch_size < len(urls):
            time.sleep(delay)
    print(f"[{slug}] accepted by API: {ok_total:,}")
    return ok_total


def main() -> None:
    ap = argparse.ArgumentParser(description="Submit sitemap URLs to Bing Webmaster Tools (URL Submission API).")
    ap.add_argument("--site", choices=sorted(SITES), help="site slug")
    ap.add_argument("--all", action="store_true", help="submit every site (respects daily quota)")
    ap.add_argument("--limit", type=int, default=2000, help="max URLs per site (default 2000)")
    ap.add_argument("--batch", type=int, default=MAX_BATCH, help=f"URLs per request (max {MAX_BATCH})")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1.0)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be submitted")
    ap.add_argument("--list", action="store_true", help="list sites and sitemap URL counts")
    ap.add_argument("--quota", action="store_true", help="show today's submission usage")
    args = ap.parse_args()

    if args.list:
        return cmd_list()
    if args.quota:
        return cmd_quota()
    if not args.site and not args.all:
        ap.print_help()
        return

    batch = max(1, min(args.batch, MAX_BATCH))
    key = "DRY-RUN" if args.dry_run else api_key()
    targets = sorted(SITES) if args.all else [args.site]
    total = 0
    for slug in targets:
        limit = args.limit
        if args.all:
            remaining = DAILY_LIMIT - used_today(load_quota())
            limit = min(limit, max(0, remaining))
            if limit <= 0:
                print("daily quota exhausted; stopping")
                break
        total += run_site(slug, key, limit, args.dry_run, batch, args.delay)
    print(f"\nTOTAL submitted/queued: {total:,}")


if __name__ == "__main__":
    main()
