#!/usr/bin/env python3
"""Tiered web search for the moneyds portfolio — no API key, no single point of failure.

Why this exists: the harness `web_search` tool needs a DEEPSEEK_API_KEY that this profile does not
have, and any single free search endpoint eventually rate-limits (Brave returns 429 today, Mojeek
serves a captcha). So search is a CHAIN: try the cheapest/best backend first, detect blocks and
empty parses, and fall through to the next tier.

Tiers (in order)
  1. searxng     local SearXNG JSON API, http://127.0.0.1:8080 — best quality, no rate limit.
                 Only works while the Docker container is running; fails in <1s when it is not.
  2. ddg-lite    DuckDuckGo lite HTML endpoint
  3. ddg-html    DuckDuckGo html endpoint (separate path/limits from lite)
  4. bing        Bing HTML results (different operator, generous limits)
  5. playwright  headless Chromium via the repo's local playwright install — last resort for
                 JS-rendered engines (Brave / DuckDuckGo JS), needs browsers installed

Usage
  python scripts/search.py "cloudflare pages limits"
  python scripts/search.py "nip.io" -n 5 --json
  python scripts/search.py "x" --backend bing          # force one tier
  python scripts/search.py "x" --tiers searxng,ddg-lite
  python scripts/search.py --check                     # health of every tier

Exit status: 0 if a tier returned results, 1 if every tier failed.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
SEARXNG = os.environ.get("SEARXNG_URL", "http://127.0.0.1:8080")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
BLOCK_MARKERS = ("captcha", "are you a robot", "unusual traffic", "too many requests",
                 "blocked", "verify you are human", "rate limit exceeded")

TIERS = ["searxng", "ddg-lite", "ddg-html", "bing", "playwright"]


class BackendError(RuntimeError):
    """A tier refused, blocked, or returned nothing parseable."""


# --------------------------------------------------------------------------- helpers
def _get(url: str, timeout: float, as_json: bool = False):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        raise BackendError(f"HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise BackendError(f"unreachable ({e.__class__.__name__})") from e
    if status in (202, 403, 429):
        raise BackendError(f"blocked (HTTP {status})")
    low = raw[:4000].lower()
    if any(m in low for m in BLOCK_MARKERS):
        raise BackendError("blocked (challenge/captcha page)")
    if as_json:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise BackendError("bad JSON") from e
    return raw


def _text(fragment: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", fragment)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def _ddg_unwrap(href: str) -> str:
    """//duckduckgo.com/l/?uddg=<enc>&rut=... -> real URL."""
    href = html.unescape(href)
    if "uddg=" in href:
        q = urllib.parse.urlparse(href).query
        real = urllib.parse.parse_qs(q).get("uddg")
        if real:
            return real[0]
    if href.startswith("//"):
        return "https:" + href
    return href


def _anchors(body: str, cls: str):
    """All <a> tags whose class contains `cls`: yields (href, inner_html)."""
    out = []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", body, re.S | re.I):
        attrs, inner = m.group(1), m.group(2)
        if re.search(r'class\s*=\s*["\'][^"\']*\b' + re.escape(cls) + r'\b', attrs, re.I):
            hm = re.search(r'href\s*=\s*["\']([^"\']+)', attrs, re.I)
            if hm:
                out.append((hm.group(1), inner))
    return out


# --------------------------------------------------------------------------- tiers
def searxng(query: str, n: int, timeout: float):
    url = f"{SEARXNG}/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "safesearch": "1", "language": "en-US"})
    data = _get(url, timeout, as_json=True)
    results = []
    for r in (data.get("results") or [])[:n]:
        u = r.get("url") or ""
        if not u:
            continue
        results.append({"title": _text(r.get("title") or u), "url": u,
                        "snippet": _text(r.get("content") or "")})
    if not results:
        raise BackendError("no results (is $('#format: json') enabled in SearXNG settings?)")
    return results


def ddg_lite(query: str, n: int, timeout: float):
    url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query})
    body = _get(url, timeout)
    links = _anchors(body, "result-link")
    snippets = [_text(m.group(1)) for m in
                re.finditer(r'(?is)<td[^>]*class=["\']result-snippet["\'][^>]*>(.*?)</td>', body)]
    results = []
    for i, (href, inner) in enumerate(links[:n]):
        u = _ddg_unwrap(href)
        if not u.startswith("http"):
            continue
        results.append({"title": _text(inner), "url": u,
                        "snippet": snippets[i] if i < len(snippets) else ""})
    if not results:
        raise BackendError("no parseable results")
    return results


def ddg_html(query: str, n: int, timeout: float):
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    body = _get(url, timeout)
    links = _anchors(body, "result__a")
    snippets = [_text(m.group(1)) for m in
                re.finditer(r'(?is)<a[^>]*class=["\'][^"\']*result__snippet[^"\']*["\'][^>]*>(.*?)</a>', body)]
    results = []
    for i, (href, inner) in enumerate(links[:n]):
        u = _ddg_unwrap(href)
        if not u.startswith("http"):
            continue
        results.append({"title": _text(inner), "url": u,
                        "snippet": snippets[i] if i < len(snippets) else ""})
    if not results:
        raise BackendError("no parseable results")
    return results


def bing(query: str, n: int, timeout: float):
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query, "count": max(n, 10)})
    body = _get(url, timeout)
    results = []
    for block in re.split(r'(?i)<li class="b_algo"', body)[1:]:
        block = block.split('<li class="b_algo"')[0]
        hm = re.search(r'(?is)<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block)
        if not hm:
            continue
        u = html.unescape(hm.group(1))
        if not u.startswith("http"):
            continue
        pm = re.search(r"(?is)<p[^>]*>(.*?)</p>", block)
        results.append({"title": _text(hm.group(2)), "url": u,
                        "snippet": _text(pm.group(1)) if pm else ""})
        if len(results) >= n:
            break
    if not results:
        raise BackendError("no parseable results")
    return results


PW_JS = ROOT / "scripts" / "playwright_search.mjs"


def playwright(query: str, n: int, timeout: float):
    if not PW_JS.exists():
        raise BackendError("scripts/playwright_search.mjs missing")
    try:
        proc = subprocess.run(
            ["node", str(PW_JS), query, str(n)],
            capture_output=True, text=True, timeout=max(timeout, 25),
            cwd=str(ROOT), encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise BackendError("node not found")
    except subprocess.TimeoutExpired:
        raise BackendError("playwright timeout")
    if proc.returncode != 0:
        raise BackendError(f"playwright exit {proc.returncode}: {(proc.stderr or '').strip()[:120]}")
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise BackendError("playwright produced no JSON")
    if not data:
        raise BackendError("playwright found no results")
    return [{"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("snippet", "")} for r in data[:n] if r.get("url")]


BACKENDS = {"searxng": searxng, "ddg-lite": ddg_lite, "ddg-html": ddg_html,
            "bing": bing, "playwright": playwright}


# --------------------------------------------------------------------------- chain
def search(query: str, n: int = 10, tiers=None, timeout: float = 12.0, verbose=False):
    """Try tiers in order. Returns (results, backend, attempts)."""
    order = tiers or TIERS
    attempts, seen = [], set()
    for name in order:
        fn = BACKENDS.get(name)
        if fn is None:
            attempts.append({"backend": name, "ok": False, "error": "unknown tier"})
            continue
        t0 = time.time()
        try:
            results = fn(query, n, timeout)
        except BackendError as e:
            attempts.append({"backend": name, "ok": False, "ms": int((time.time() - t0) * 1000),
                             "error": str(e)})
            if verbose:
                print(f"  [{name}] skipped: {e}", file=sys.stderr)
            continue
        except Exception as e:  # never let an unexpected error kill the chain
            attempts.append({"backend": name, "ok": False, "ms": int((time.time() - t0) * 1000),
                             "error": f"{e.__class__.__name__}: {e}"})
            if verbose:
                print(f"  [{name}] error: {e}", file=sys.stderr)
            continue
        # de-duplicate across the page, keep order
        uniq = []
        for r in results:
            key = r["url"].split("#")[0].rstrip("/")
            if key and key not in seen:
                seen.add(key)
                uniq.append(r)
        if uniq:
            attempts.append({"backend": name, "ok": True, "ms": int((time.time() - t0) * 1000),
                             "results": len(uniq)})
            return uniq[:n], name, attempts
        attempts.append({"backend": name, "ok": False, "error": "empty"})
    return [], None, attempts


def check(timeout: float = 6.0) -> int:
    print(f"search tier health (query 'cloudflare pages limits', {timeout}s per tier):")
    bad = 0
    for name in TIERS:
        t0 = time.time()
        try:
            res = BACKENDS[name]("cloudflare pages limits", 3, timeout)
            print(f"  {name:<11} OK    {len(res)} results  {int((time.time() - t0) * 1000)} ms")
        except BackendError as e:
            print(f"  {name:<11} DOWN  {e}")
            bad += name != "searxng"      # searxng being down is expected when Docker is off
        except Exception as e:
            print(f"  {name:<11} ERR   {e}")
            bad += 1
    print(f"usable tiers: {len(TIERS) - bad}/{len(TIERS)}")
    return 0 if bad < len(TIERS) - 1 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Tiered web search (SearXNG -> DDG -> Bing -> Playwright)")
    ap.add_argument("query", nargs="?", help="search query")
    ap.add_argument("-n", type=int, default=10, help="results to return (default 10)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--backend", help="force one tier (%s)" % ", ".join(TIERS))
    ap.add_argument("--tiers", help="comma-separated tier order, e.g. searxng,ddg-lite,bing")
    ap.add_argument("--timeout", type=float, default=12.0, help="seconds per tier")
    ap.add_argument("--check", action="store_true", help="probe every tier and exit")
    ap.add_argument("-v", "--verbose", action="store_true", help="show skipped tiers on stderr")
    args = ap.parse_args()

    if args.check:
        return check(args.timeout)
    if not args.query:
        ap.error("query required (or use --check)")

    tiers = [args.backend] if args.backend else (
        [t.strip() for t in args.tiers.split(",") if t.strip()] if args.tiers else None)
    results, backend, attempts = search(args.query, args.n, tiers, args.timeout, args.verbose)

    if args.json:
        print(json.dumps({"query": args.query, "backend": backend,
                          "results": results, "attempts": attempts},
                         indent=2, ensure_ascii=False))
    else:
        if not results:
            print(f"no results for {args.query!r} — every tier failed:", file=sys.stderr)
            for a in attempts:
                print(f"  {a['backend']:<11} {a.get('error', '')}", file=sys.stderr)
            return 1
        print(f"{len(results)} results for {args.query!r} via {backend}")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r['title']}\n   {r['url']}")
            if r["snippet"]:
                print(f"   {r['snippet'][:220]}")
        if args.verbose:
            print("\ntiers tried: " + ", ".join(f"{a['backend']}={a.get('error', 'ok')}"
                                                for a in attempts), file=sys.stderr)
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
