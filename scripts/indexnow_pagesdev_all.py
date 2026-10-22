#!/usr/bin/env python3
"""Submit ALL pages.dev URLs for every project whose IndexNow key verification has completed.

Batches of up to 10,000 URLs per request (IndexNow limit). This gives Bing a complete crawl map of the
portfolio on a host it already crawls; each page carries a canonical to the custom domain.

Usage: python scripts/indexnow_pagesdev_all.py [--sleep 2]
"""
import argparse
import json
import pathlib
import re
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "moneyds7f3a9c2e5b1d4f8a6c0e2d9b5a7f1c3e"
UA = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json; charset=utf-8"}
HOSTS = [
    "hub-1xy.pages.dev", "ifsc-b55.pages.dev", "myds-airport.pages.dev", "myds-zip.pages.dev",
    "myds-places.pages.dev", "myds-colleges.pages.dev", "myds-calculators.pages.dev",
    "myds-areacodes.pages.dev", "myds-hospitals.pages.dev", "myds-nursinghomes.pages.dev",
    "myds-homehealth.pages.dev", "myds-dialysis.pages.dev",
]
BATCH = 10000


def get(url: str, timeout: int = 60) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                  timeout=timeout).read()


def post(endpoint: str, payload: dict) -> tuple:
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode(), headers=UA, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, b""
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:160]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleep", type=float, default=2.0)
    a = ap.parse_args()
    total = 0
    for host in HOSTS:
        try:
            sm = get(f"https://{host}/sitemap.xml").decode("utf-8", "ignore")
            locs = re.findall(r"<loc>([^<]+)</loc>", sm)
            urls = [re.sub(r"^https://[^/]+", f"https://{host}", u) for u in locs]
        except Exception as e:  # noqa: BLE001
            print(f"{host}: sitemap error {str(e)[:70]}")
            continue
        ok = 0
        for i in range(0, len(urls), BATCH):
            batch = urls[i:i + BATCH]
            payload = {"host": host, "key": KEY, "keyLocation": f"https://{host}/{KEY}.txt",
                       "urlList": batch}
            status, body = post("https://www.bing.com/indexnow", payload)
            if status in (200, 202):
                ok += len(batch)
                print(f"{host}: {len(batch)} urls -> {status}")
            else:
                print(f"{host}: {len(batch)} urls -> HTTP {status} {body[:100]}")
                break
            time.sleep(a.sleep)
        total += ok
    print(f"total accepted: {total}")


if __name__ == "__main__":
    main()
