#!/usr/bin/env python3
"""Submit every Cloudflare Pages project's *.pages.dev URLs to IndexNow.

Each project serves the portfolio's IndexNow key file at its own root, so the pages.dev host can be
verified. The pages carry a canonical link to the custom domain, so search engines should crawl the
content and consolidate the ranking signal onto tekify.xyz — this is a crawl entry point for 121k pages
on a domain (pages.dev) that crawlers can reach without knowing our custom domain.

Usage: python scripts/indexnow_pagesdev.py [--limit 500] [--endpoint bing|api|both]
"""
import argparse
import json
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "moneyds7f3a9c2e5b1d4f8a6c0e2d9b5a7f1c3e"
UA = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json; charset=utf-8"}
OWN_PROJECTS = ["hub", "ifsc", "airport", "zip", "places", "colleges", "calculators", "areacodes",
                "hospitals", "nursinghomes", "homehealth", "dialysis"]
SKIP = {"pincode-india", "ifsc-india", "solarcalc-tekify"}


def env() -> dict:
    out = {}
    for line in (ROOT / "shared" / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def api(path: str):
    e = env()
    req = urllib.request.Request("https://api.cloudflare.com/client/v4" + path,
                                 headers={"Authorization": f"Bearer {e['CF_API_TOKEN']}"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def get(url: str, timeout: int = 40) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                  timeout=timeout).read()


def submit(host: str, urls: list, endpoints: list) -> None:
    payload = {"host": host, "key": KEY, "keyLocation": f"https://{host}/{KEY}.txt", "urlList": urls}
    body = json.dumps(payload).encode()
    for endpoint in endpoints:
        req = urllib.request.Request(endpoint, data=body, headers=UA, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                print(f"   {endpoint} -> {r.status} ({len(urls)} urls)")
        except urllib.error.HTTPError as e:
            print(f"   {endpoint} -> HTTP {e.code} {e.read()[:120]}")
        except Exception as e:  # noqa: BLE001
            print(f"   {endpoint} -> ERR {str(e)[:80]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--endpoint", default="both", choices=["bing", "api", "both"])
    a = ap.parse_args()
    endpoints = (["https://www.bing.com/indexnow"] if a.endpoint == "bing"
                 else ["https://api.indexnow.org/indexnow"] if a.endpoint == "api"
                 else ["https://www.bing.com/indexnow", "https://api.indexnow.org/indexnow"])

    acct = env()["CF_ACCOUNT_ID"]
    projects = {}
    for page in (1, 2, 3):
        res = api(f"/accounts/{acct}/pages/projects?page={page}")["result"]
        for p in res:
            projects[p["name"]] = p
        if len(res) < 10:
            break
    for name in OWN_PROJECTS:
        p = projects.get(name) or projects.get("myds-" + name) or (projects.get("ifsc") if name == "ifsc" else None)
        if not p:
            print(f"{name}: project not found")
            continue
        if p["name"] in SKIP:
            continue
        host = p["subdomain"]
        try:
            key = get(f"https://{host}/{KEY}.txt").decode().strip()
            if key != KEY:
                print(f"{host}: key file mismatch, skipping")
                continue
        except Exception as e:  # noqa: BLE001
            print(f"{host}: key file error {str(e)[:60]}")
            continue
        try:
            sm = get(f"https://{host}/sitemap.xml").decode("utf-8", "ignore")
            locs = re.findall(r"<loc>([^<]+)</loc>", sm)
            urls = [re.sub(r"^https://[^/]+", f"https://{host}", u) for u in locs[: a.limit]]
        except Exception as e:  # noqa: BLE001
            print(f"{host}: sitemap error {str(e)[:60]}")
            continue
        print(f"{host}: {len(urls)} urls")
        submit(host, urls, endpoints)


if __name__ == "__main__":
    main()
