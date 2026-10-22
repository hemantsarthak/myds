"""Comprehensive live-site audit for every tekify property.

Checks per site: homepage, robots.txt, IndexNow key file, sitemap validity + host correctness,
sample pages (canonical, title/description lengths, h1, JSON-LD, lang, noindex), /search/ wiring,
/guides/ presence, data endpoint, internal links on a sampled page, and basic headers.

Run: python scripts/audit_sites.py [--samples 3]
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from xml.etree import ElementTree

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124"}
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
INDEXNOW_KEY = "moneyds7f3a9c2e5b1d4f8a6c0e2d9b5a7f1c3e"

SITES = {
    "tekify.xyz": dict(kind="hub", data=None, guides=False),
    "ifsccodes.tekify.xyz": dict(kind="data", data="/data/bank/HDFC.json", guides=True),
    "airportcodes.tekify.xyz": dict(kind="data", data="/data/airports.json", guides=True),
    "zipcodes.tekify.xyz": dict(kind="data", data="/data/zips.json", guides=True),
    "places.tekify.xyz": dict(kind="data", data="/data/places.json", guides=True),
    "colleges.tekify.xyz": dict(kind="data", data="/data/colleges.json", guides=True),
    "areacodes.tekify.xyz": dict(kind="data", data="/data/search.json", guides=True),
    "hospitals.tekify.xyz": dict(kind="data", data="/data/hospitals.json", guides=True),
    "nursinghomes.tekify.xyz": dict(kind="data", data="/data/nursinghomes.json", guides=True),
    "homehealth.tekify.xyz": dict(kind="data", data="/data/homehealth.json", guides=True),
    "calculators.tekify.xyz": dict(kind="tools", data=None, guides=True),
}

failures = []
warnings = []


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), dict(r.headers)


def text(body):
    return body.decode("utf-8", "ignore")


def check(cond, msg):
    if not cond:
        failures.append(msg)
    return cond


def audit(host, cfg, samples):
    print(f"\n=== {host} ===")
    # homepage
    try:
        st, body, hdrs = get(f"https://{host}/")
        h = text(body)
    except Exception as e:  # noqa: BLE001
        failures.append(f"{host}: homepage unreachable ({e})")
        return
    check(st == 200, f"{host}: homepage status {st}")
    title = re.search(r"<title>(.*?)</title>", h, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', h)
    canon = re.search(r'<link rel="canonical" href="([^"]*)"', h)
    check(bool(title), f"{host}: no <title>")
    check(bool(desc), f"{host}: no meta description")
    check(bool(canon), f"{host}: no canonical")
    if canon:
        check(canon.group(1).rstrip("/") == f"https://{host}", f"{host}: home canonical is {canon.group(1)}")
    check('<meta name="viewport"' in h, f"{host}: no viewport")
    check("unfoldedtrade" in h or "subtle-injury" in h, f"{host}: no ad script")
    check("analytics.monetec2.workers.dev" in h, f"{host}: no analytics beacon")
    check("tekify network" in h.lower(), f"{host}: no network footer")
    check(len(h) < 400_000, f"{host}: homepage unusually large ({len(h)} bytes)")
    print(f"  home: {st}, title={len(title.group(1)) if title else 0} chars, {len(h)} bytes")

    # robots + key
    try:
        _, rb, _ = get(f"https://{host}/robots.txt")
        robots = text(rb)
        check(f"Sitemap: https://{host}/sitemap.xml" in robots, f"{host}: robots.txt missing own sitemap")
    except Exception as e:  # noqa: BLE001
        failures.append(f"{host}: robots.txt error {e}")
    try:
        st, kb, _ = get(f"https://{host}/{INDEXNOW_KEY}.txt")
        check(st == 200 and INDEXNOW_KEY in text(kb), f"{host}: IndexNow key file bad")
    except Exception as e:  # noqa: BLE001
        failures.append(f"{host}: IndexNow key file error {e}")

    # sitemap
    urls = []
    try:
        st, sb, _ = get(f"https://{host}/sitemap.xml")
        root = ElementTree.fromstring(sb)
        urls = [e.text.strip() for e in root.iter(f"{NS}loc") if e.text]
        check(len(urls) > 0, f"{host}: empty sitemap")
        bad_host = [u for u in urls if not u.startswith(f"https://{host}/")]
        check(not bad_host, f"{host}: sitemap has {len(bad_host)} URLs on other hosts, e.g. {bad_host[:2]}")
        http_urls = [u for u in urls if u.startswith("http://")]
        check(not http_urls, f"{host}: sitemap has http:// URLs")
        check(b"<lastmod>" in sb, f"{host}: sitemap has no <lastmod>")
        xcto = hdrs.get("X-Content-Type-Options") or hdrs.get("x-content-type-options")
        check(bool(xcto), f"{host}: missing X-Content-Type-Options header")
        print(f"  sitemap: {len(urls)} urls")
    except Exception as e:  # noqa: BLE001
        failures.append(f"{host}: sitemap error {e}")

    # sample pages
    import random
    random.seed(hash(host) % 10000)
    picks = random.sample(urls, min(samples, len(urls))) if urls else []
    for u in picks:
        try:
            st, pb, _ = get(u)
            p = text(pb)
            check(st == 200, f"{host}: sample {u} status {st}")
            c = re.search(r'<link rel="canonical" href="([^"]*)"', p)
            check(c and c.group(1).rstrip("/") == u.rstrip("/"), f"{host}: {u} canonical mismatch ({c.group(1) if c else 'none'})")
            t = re.search(r"<title>(.*?)</title>", p, re.S)
            d = re.search(r'<meta name="description" content="([^"]*)"', p)
            check(t and 10 <= len(t.group(1)) <= 80, f"{host}: {u} title length {len(t.group(1)) if t else 0}")
            check(d and 40 <= len(d.group(1)) <= 200, f"{host}: {u} description length {len(d.group(1)) if d else 0}")
            check("<h1" in p, f"{host}: {u} no h1")
            check('application/ld+json' in p, f"{host}: {u} no JSON-LD")
            check('<html lang="en"' in p, f"{host}: {u} no lang attr")
            check('name="robots" content="noindex' not in p, f"{host}: {u} is noindex")
            check("unfoldedtrade" in p or "subtle-injury" in p, f"{host}: {u} missing ad script")
            check("analytics.monetec2.workers.dev" in p, f"{host}: {u} missing analytics")
            check(len(p) < 250_000, f"{host}: {u} page unusually large ({len(p)} bytes)")
            # internal links resolve (up to 3)
            links = re.findall(r'href="(/[^"#?]+)"', p)[:3]
            for l in links:
                try:
                    st2, _, _ = get(f"https://{host}{l}")
                    check(st2 == 200, f"{host}: {u} broken internal link {l} -> {st2}")
                except Exception as e:  # noqa: BLE001
                    failures.append(f"{host}: {u} internal link {l} error {e}")
            print(f"  sample ok: {u}")
        except Exception as e:  # noqa: BLE001
            failures.append(f"{host}: sample {u} error {e}")

    # search page wiring
    if cfg["kind"] == "data":
        try:
            st, sb, _ = get(f"https://{host}/search/")
            s = text(sb)
            check(st == 200, f"{host}: /search/ status {st}")
            check('id="q"' in s, f"{host}: /search/ has no search input")
            if cfg["kind"] == "data":
                check("assets/app.js" in s, f"{host}: /search/ does not load app.js")
            print(f"  search page: {st}, app.js={'assets/app.js' in s}")
        except Exception as e:  # noqa: BLE001
            failures.append(f"{host}: /search/ error {e}")

    # guides
    if cfg["guides"]:
        try:
            st, gb, _ = get(f"https://{host}/guides/")
            check(st == 200, f"{host}: /guides/ status {st}")
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{host}: no /guides/ ({str(e)[:40]})")

    # data endpoint
    if cfg["data"]:
        try:
            st, db, _ = get(f"https://{host}{cfg['data']}")
            check(st == 200 and len(db) > 1000, f"{host}: data endpoint {cfg['data']} bad ({st}, {len(db)}b)")
            try:
                json.loads(db)
            except Exception as e:  # noqa: BLE001
                failures.append(f"{host}: data endpoint {cfg['data']} is not valid JSON ({e})")
        except Exception as e:  # noqa: BLE001
            failures.append(f"{host}: data endpoint error {e}")


def audit_hub_links():
    """The hub must link every property and every link must resolve."""
    try:
        _, body, _ = get("https://tekify.xyz/")
        h = text(body)
        links = re.findall(r'href="(https://[a-z0-9-]+\.tekify\.xyz)/?"', h)
        links = sorted(set(links))
        expected = {f"https://{s}" for s in SITES if s != "tekify.xyz"}
        missing = expected - set(links)
        check(not missing, f"hub: missing property links {sorted(missing)}")
        for l in links:
            try:
                st, _, _ = get(l + "/")
                check(st == 200, f"hub link {l} -> {st}")
            except Exception as e:  # noqa: BLE001
                failures.append(f"hub link {l} error {e}")
        print(f"hub: {len(links)} property links checked")
    except Exception as e:  # noqa: BLE001
        failures.append(f"hub: link audit error {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=3)
    a = ap.parse_args()
    for host, cfg in SITES.items():
        audit(host, cfg, a.samples)
    audit_hub_links()
    print("\n================ SUMMARY ================")
    print(f"failures: {len(failures)}")
    for f in failures:
        print("  FAIL:", f)
    print(f"warnings: {len(warnings)}")
    for w in warnings:
        print("  WARN:", w)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
