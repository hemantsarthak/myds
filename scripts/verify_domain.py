#!/usr/bin/env python3
"""Add a Google Search Console DNS verification record (and the Bing Webmaster one) in one command.

Both services verify a DOMAIN property by asking for a TXT record; we control tekify.xyz DNS via the
Cloudflare API, so the only thing a human must do is paste the token from the service's UI.

Usage:
  python scripts/verify_domain.py --google "google-site-verification=XXXX"
  python scripts/verify_domain.py --bing   "msvalidate.01=XXXX"
  python scripts/verify_domain.py --show          # list current verification TXT records

After running, click "Verify" in the service UI (GSC: Add property -> Domain -> DNS verification).
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]


def env() -> dict:
    out = {}
    for line in (ROOT / "shared" / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def api(method: str, path: str, body=None):
    e = env()
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {e['CF_API_TOKEN']}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read().decode() or "{}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--google", help='TXT value from GSC, e.g. "google-site-verification=..."')
    ap.add_argument("--bing", help='TXT value from Bing WMT, e.g. "msvalidate.01=..."')
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    e = env()
    zone = e["CF_ZONE_ID_TEKIFY"]
    recs = api("GET", f"/zones/{zone}/dns_records?type=TXT")
    existing = [r["content"].strip('"') for r in recs.get("result", [])]
    if a.show:
        for c in existing:
            print(c)
        return 0
    todo = []
    if a.google:
        todo.append(a.google.strip('"'))
    if a.bing:
        todo.append(a.bing.strip('"'))
    if not todo:
        sys.exit("nothing to do: pass --google and/or --bing, or --show")
    for value in todo:
        if value in existing:
            print("exists:", value)
            continue
        r = api("POST", f"/zones/{zone}/dns_records",
                {"type": "TXT", "name": "tekify.xyz", "content": value, "ttl": 3600})
        print(("created: " + value) if r.get("success") else ("error: " + json.dumps(r)[:300]))
    print("\nNow click Verify in the service UI. Records currently present:")
    for c in existing + todo:
        print("  ", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
