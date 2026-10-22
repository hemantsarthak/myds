#!/usr/bin/env python3
"""traffic.py — REAL edge traffic from Cloudflare zone analytics (read-only).

The self-hosted JS beacon (`ops.py stats`) can only see clients that execute JavaScript, so it is
blind to plain Googlebot/Bingbot fetches, sitemap requests and security scans. This tool reads the
zone's own HTTP analytics over the GraphQL API, which sees every request that reached Cloudflare —
humans, verified crawlers, AI crawlers and scanners.

Usage:
  python scripts/traffic.py                      # last 2 days, summary
  python scripts/traffic.py --days 2 --host zipcodes.tekify.xyz --top 15
  python scripts/traffic.py --json               # machine-readable

Notes:
  * Free-plan GraphQL keeps a short window (≈2 days of httpRequestsAdaptive data); --days >2 just
    asks for more and returns whatever is retained.
  * Needs CF_API_TOKEN and (optionally) CF_ZONE_ID_TEKIFY in shared/.env — the same token the
    other ops scripts use. The token needs "Zone Analytics: Read".
  * Counts are HTTP requests, not pageviews: a page with 20 assets is 1 request here + assets,
    because Cloudflare Pages assets are edge-cached requests too.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"
API = "https://api.cloudflare.com/client/v4"

# UA substrings -> (class, display name). Order matters: first match wins.
CRAWLERS = [
    ("googlebot", "search", "Googlebot"),
    ("google-inspectiontool", "search", "Google-InspectionTool"),
    ("googleother", "ai", "GoogleOther"),
    ("storebot-google", "search", "Storebot-Google"),
    ("bingbot", "search", "Bingbot"),
    ("adidxbot", "search", "AdIdxBot"),
    ("duckduckbot", "search", "DuckDuckBot"),
    ("yandex", "search", "YandexBot"),
    ("baiduspider", "search", "BaiduSpider"),
    ("applebot", "search", "Applebot"),
    ("seznam", "search", "SeznamBot"),
    ("petalbot", "search", "PetalBot"),
    ("claudebot", "ai", "ClaudeBot"),
    ("anthropic", "ai", "Anthropic"),
    ("gptbot", "ai", "GPTBot"),
    ("openai", "ai", "OpenAI"),
    ("perplexity", "ai", "PerplexityBot"),
    ("ccbot", "ai", "CCBot"),
    ("bytespider", "ai", "Bytespider"),
    ("ahrefs", "seo", "AhrefsBot"),
    ("semrush", "seo", "SemrushBot"),
    ("mj12", "seo", "MJ12Bot"),
    ("dotbot", "seo", "DotBot"),
    ("dataforseo", "seo", "DataForSEO"),
    ("l9scan", "scanner", "LeakIX scanner"),
    ("leakix", "scanner", "LeakIX scanner"),
    ("zgrab", "scanner", "zgrab"),
    ("censys", "scanner", "Censys"),
    ("nmap", "scanner", "nmap"),
    ("masscan", "scanner", "masscan"),
    ("curl/", "script", "curl"),
    ("wget", "script", "wget"),
    ("python-requests", "script", "python-requests"),
    ("python-urllib", "script", "python-urllib"),
    ("go-http-client", "script", "go-http"),
    ("okhttp", "script", "okhttp"),
    ("nginx-ssl early hints", "scanner", "nginx-ssl probe"),
    ("headlesschrome", "script", "headless Chrome"),
    ("playwright", "script", "Playwright"),
    ("uptime", "monitor", "uptime monitor"),
    ("pingdom", "monitor", "Pingdom"),
    ("statuscake", "monitor", "StatusCake"),
]


def load_env() -> None:
    for p in (SHARED / ".env", ROOT / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if "CF_API_TOKEN" not in os.environ:
        sys.exit("missing CF_API_TOKEN (shared/.env)")


def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API + "/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        method="POST",
    )
    req.add_header("Authorization", "Bearer " + os.environ["CF_API_TOKEN"])
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"GraphQL HTTP {e.code}: {e.read().decode()[:300]}")
    if body.get("errors"):
        sys.exit("GraphQL error: " + json.dumps(body["errors"])[:400])
    return body["data"]["viewer"]["zones"][0]


def zone_id() -> str:
    zid = os.environ.get("CF_ZONE_ID_TEKIFY")
    if zid:
        return zid
    req = urllib.request.Request(API + "/zones", method="GET")
    req.add_header("Authorization", "Bearer " + os.environ["CF_API_TOKEN"])
    with urllib.request.urlopen(req, timeout=60) as r:
        zones = json.loads(r.read().decode())["result"]
    for z in zones:
        if z["name"] == "tekify.xyz":
            return z["id"]
    sys.exit("zone tekify.xyz not found")


def classify(ua: str) -> tuple:
    low = (ua or "").lower()
    for needle, cls, name in CRAWLERS:
        if needle in low:
            return cls, name
    if "mozilla/" in low and ("chrome/" in low or "safari/" in low or "firefox/" in low):
        return "browser", "browser-UA (unverified)"
    return "other", low[:60] or "(empty UA)"


def window(days: int) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "start": (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def groups(zid: str, dims: str, where: str = "", limit: int = 500, extra: dict | None = None) -> list:
    w = window(int((extra or {}).get("days", 2)))
    variables = {"z": zid, "start": w["start"], "end": w["end"]}
    filters = "datetime_geq:$start, datetime_leq:$end"
    if extra and extra.get("host"):
        filters += ', clientRequestHTTPHost:$host'
        variables["host"] = extra["host"]
    query = f"""
query($z:String!,$start:Time!,$end:Time!{' $host:String!' if extra and extra.get('host') else ''}){{
  viewer {{ zones(filter:{{zoneTag:$z}}) {{
    httpRequestsAdaptiveGroups(limit:{limit}, filter:{{{filters}{where}}}, orderBy:[count_DESC]) {{
      count dimensions {{ {dims} }}
    }} }} }} }}"""
    return gql(query, variables)["httpRequestsAdaptiveGroups"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--host", help="limit to one hostname, e.g. zipcodes.tekify.xyz")
    ap.add_argument("--top", type=int, default=10, help="rows per table")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    load_env()
    zid = zone_id()
    ctx = {"days": args.days, "host": args.host}

    by_host = groups(zid, "clientRequestHTTPHost", extra=ctx)
    by_ua = groups(zid, "userAgent", limit=1000, extra=ctx)
    by_status = groups(zid, "edgeResponseStatus", extra=ctx)

    classes: dict = {}
    named: dict = {}
    total = 0
    for row in by_ua:
        n = row["count"]
        total += n
        ua = row["dimensions"]["userAgent"] or ""
        cls, name = classify(ua)
        c = classes.setdefault(cls, {"requests": 0, "names": {}})
        c["requests"] += n
        c["names"][name] = c["names"].get(name, 0) + n
        if cls in ("search", "ai", "seo"):
            named[name] = named.get(name, 0) + n

    # Named-crawler census: any Googlebot/Bingbot/etc. row, even below the top-1000 cutoff.
    census = {}
    for needle, cls, name in CRAWLERS:
        if cls not in ("search", "ai"):
            continue
        census[name] = sum(
            r["count"] for r in by_ua
            if needle in (r["dimensions"]["userAgent"] or "").lower()
        )

    status = {r["dimensions"]["edgeResponseStatus"]: r["count"] for r in by_status}
    hosts = [
        (r["dimensions"]["clientRequestHTTPHost"], r["count"]) for r in by_host
    ]

    if args.json:
        print(json.dumps({
            "window_days": args.days,
            "total_requests": total,
            "by_host": [{"host": h, "requests": n} for h, n in hosts],
            "by_class": {k: v["requests"] for k, v in sorted(classes.items(), key=lambda kv: -kv[1]["requests"])},
            "named_crawlers": census,
            "status": status,
        }, indent=2))
        return

    print(f"Cloudflare edge traffic — last {args.days}d"
          + (f" — host {args.host}" if args.host else "") + f" — {total:,} requests\n")
    print("By class:")
    for cls, v in sorted(classes.items(), key=lambda kv: -kv[1]["requests"]):
        pct = 100 * v["requests"] / total if total else 0
        top = ", ".join(f"{n} {k}" for k, n in sorted(v["names"].items(), key=lambda kv: -kv[1])[:3])
        print(f"  {cls:<10} {v['requests']:>8,}  {pct:5.1f}%   ({top})")
    print("\nSearch / AI crawlers seen:")
    for name, n in sorted(census.items(), key=lambda kv: -kv[1]):
        mark = "  <-- " if name in ("Googlebot", "Bingbot") else ""
        print(f"  {name:<20} {n:>7,}{mark}")
    if not any(census.values()):
        print("  NONE")
    print("\nBy host:")
    for host, n in hosts[: args.top + 2]:
        print(f"  {host:<32} {n:>8,}")
    print("\nStatus codes:")
    for code, n in sorted(status.items(), key=lambda kv: -kv[1]):
        print(f"  {code:<5} {n:>8,}")
    if args.host:
        print(f"\nTop paths on {args.host}:")
        for r in groups(zid, "clientRequestPath edgeResponseStatus", limit=args.top, extra=ctx):
            d = r["dimensions"]
            print(f"  {r['count']:>6,}  {d['edgeResponseStatus']}  {d['clientRequestPath'][:90]}")


if __name__ == "__main__":
    main()
