#!/usr/bin/env python3
"""Daily health check + IndexNow submission for the whole tekify.xyz portfolio.

Runs in GitHub Actions on a schedule (no laptop needed). For every property it:

  1. fetches the live homepage (expects 200),
  2. fetches sitemap.xml and extracts the URL list,
  3. compares against the committed baseline in `state/sitemaps.json`,
  4. submits only NEW URLs to IndexNow (batched, <=10k per request),
  5. writes `reports/health-YYYY-MM-DD.md` and updates the baseline.

The workflow commits the report + baseline back to the repo, so there is a durable trail even
when every agent is offline.

Usage:
  python scripts/health.py            # check + report (no submission)
  python scripts/health.py --submit   # also submit new URLs to IndexNow
"""
import argparse
import datetime
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from xml.etree import ElementTree

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "state" / "sitemaps.json"
REPORTS = ROOT / "reports"
UA = "Mozilla/5.0 (compatible; tekify-health/1.0)"
INDEXNOW_KEY = "moneyds7f3a9c2e5b1d4f8a6c0e2d9b5a7f1c3e"

HOSTS = [
    "tekify.xyz",
    "ifsccodes.tekify.xyz",
    "airportcodes.tekify.xyz",
    "zipcodes.tekify.xyz",
    "places.tekify.xyz",
    "colleges.tekify.xyz",
    "calculators.tekify.xyz",
]


def get(url: str, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def sitemap_urls(host: str) -> list[str]:
    status, body = get(f"https://{host}/sitemap.xml")
    if status != 200:
        raise RuntimeError(f"sitemap HTTP {status}")
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    root = ElementTree.fromstring(body)
    locs = [el.text.strip() for el in root.iter(f"{ns}loc") if el.text]
    if locs and all(u.endswith(".xml") for u in locs):  # sitemap index
        urls = []
        for sm in locs:
            _s, sub = get(sm)
            r2 = ElementTree.fromstring(sub)
            urls += [el.text.strip() for el in r2.iter(f"{ns}loc") if el.text]
        return urls
    return locs


def submit_indexnow(host: str, urls: list[str]) -> str:
    if not urls:
        return "nothing to submit"
    payload = json.dumps({
        "host": host, "key": INDEXNOW_KEY,
        "keyLocation": f"https://{host}/{INDEXNOW_KEY}.txt",
        "urlList": urls[:10000],
    }).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=payload,
                                 headers={"Content-Type": "application/json; charset=utf-8"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return f"submitted {len(urls[:10000])} URLs (HTTP {r.status})"
    except urllib.error.HTTPError as e:
        return f"IndexNow HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:  # noqa: BLE001
        return f"IndexNow error: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true", help="submit new URLs to IndexNow")
    a = ap.parse_args()

    STATE.parent.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    baseline = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# Portfolio health — {today} (UTC)", ""]
    lines.append("| Property | Homepage | URLs | New URLs | IndexNow |")
    lines.append("|---|---|---|---|---|")
    failures = 0
    new_state = {}
    for host in HOSTS:
        try:
            status, _ = get(f"https://{host}/")
            urls = sitemap_urls(host)
        except Exception as e:  # noqa: BLE001
            failures += 1
            lines.append(f"| {host} | FAIL | — | — | — |")
            print(f"{host}: FAIL {e}")
            continue
        known = set(baseline.get(host, []))
        new = [u for u in urls if u not in known]
        new_state[host] = urls
        result = "—"
        if a.submit and new:
            result = submit_indexnow(host, new)
        lines.append(f"| {host} | {status} | {len(urls):,} | {len(new):,} | {result} |")
        print(f"{host}: {status} {len(urls)} urls, {len(new)} new {('-> ' + result) if a.submit and new else ''}")

    total = sum(len(v) for v in new_state.values())
    lines += ["", f"**Total URLs: {total:,}** across {len(new_state)} properties.", ""]
    if failures:
        lines.append(f"**{failures} propert{'y' if failures == 1 else 'ies'} failing.**")
    (REPORTS / f"health-{today}.md").write_text("\n".join(lines), encoding="utf-8")
    STATE.write_text(json.dumps(new_state, separators=(",", ":")), encoding="utf-8")
    print(f"report: reports/health-{today}.md ({total} urls)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
