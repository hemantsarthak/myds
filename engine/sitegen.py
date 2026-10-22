#!/usr/bin/env python3
"""engine/sitegen.py — the static-site engine behind every moneyds property.

One self-contained HTML file per page, inline CSS, zero framework, zero external JS
(except optional analytics + ad tags). Cloudflare Pages serves it at the edge.

Use:

    from engine.sitegen import Site, table, faq, related, ad, notice
    s = Site(slug="airports", brand="Airport Codes", domain="airport.tekify.xyz",
             tagline="...", description="...", nav=[("Airports", "/airport/")])
    s.add("/airport/LHR/", "LHR — Heathrow Airport", "...", "<h1>..</h1>")
    s.write()          # -> sites/airports/site
    s.validate()

Design rules baked in:
* every page: unique title/description, canonical, breadcrumbs, JSON-LD, ad slot
* sitemap.xml (index + chunks above 40k), robots.txt, IndexNow key file, 404, _headers
* `noindex=True` for utility pages that should not rank
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import pathlib
import re
import sys
import unicodedata
from xml.sax.saxutils import escape as xml_escape

ROOT = pathlib.Path(__file__).resolve().parents[1]

try:  # optional, kept in one place
    from engine.ads import AD_HEAD, AD_SLOT_1, AD_SLOT_2, ADS_TXT, MONETIZATION_ON  # type: ignore
except Exception:  # pragma: no cover - ads not provisioned yet
    AD_HEAD, AD_SLOT_1, AD_SLOT_2, ADS_TXT, MONETIZATION_ON = "", "", "", "", False

try:  # self-hosted cookie-free pageview counter (workers/analytics)
    from engine.analytics import analytics_tag  # type: ignore
except Exception:  # pragma: no cover
    def analytics_tag(slug: str) -> str:
        return ""

DEFAULT_INDEXNOW_KEY = "moneyds7f3a9c2e5b1d4f8a6c0e2d9b5a7f1c3e"
CF_ANALYTICS_TOKEN = ""  # set by scripts/ops.py analytics, then rebuild: cookie-free RUM

# The tekify network — cross-linked in every footer (crawl discovery + brand).
NETWORK = [
    ("Pincode India", "https://pincode.tekify.xyz/"),
    ("IFSC Codes", "https://ifsccodes.tekify.xyz/"),
    ("Airport Codes", "https://airportcodes.tekify.xyz/"),
    ("US ZIP Codes", "https://zipcodes.tekify.xyz/"),
    ("Area Codes", "https://areacodes.tekify.xyz/"),
    ("US Hospitals", "https://hospitals.tekify.xyz/"),

    ("US Places", "https://places.tekify.xyz/"),
    ("US Colleges", "https://colleges.tekify.xyz/"),
    ("Calculators", "https://calculators.tekify.xyz/"),
    ("Tekify home", "https://tekify.xyz/"),
]

# --------------------------------------------------------------------------- helpers


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def slug(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "x"


def truncate(s, n) -> str:
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def human(n) -> str:
    return f"{int(n):,}"


def today() -> str:
    return datetime.date.today().isoformat()


# --------------------------------------------------------------------------- html bits


def table(headers, rows, cls="") -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def cards(items, cls="grid") -> str:
    """items: [(href, label, sub)]"""
    out = []
    for href, label, sub in items:
        sub_html = f' <span class="mut">{sub}</span>' if sub else ""
        out.append(f'<a href="{href}">{label}{sub_html}</a>')
    return f'<div class="{cls}">' + "".join(out) + "</div>"


def related(items, title="Related") -> str:
    """items: [(href, label)] rendered as a compact link list."""
    links = " · ".join(f'<a href="{h}">{esc(t)}</a>' for h, t in items)
    return f'<div class="rel"><h2>{esc(title)}</h2><p>{links}</p></div>'


def faq(pairs) -> str:
    body = "".join(f"<h3>{esc(q)}</h3><p>{a}</p>" for q, a in pairs)
    return f'<section class="faq"><h2>Frequently asked questions</h2>{body}</section>'


def notice(text) -> str:
    return f'<p class="note">{text}</p>'


def ad(slot=1) -> str:
    """Reserved ad container. Empty when no network is provisioned (no layout shift)."""
    if not MONETIZATION_ON:
        return ""
    html_ = AD_SLOT_1 if slot == 1 else AD_SLOT_2
    return f'<div class="adslot" id="ad-{slot}">{html_}</div>'


# --------------------------------------------------------------------------- site

CSS = """
:root{--bg:#fff;--fg:#16181d;--mut:#5c6472;--card:#f6f7f9;--line:#e3e6ea;--acc:#1f6feb;--warn:#8a5a00}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e8eaed;--mut:#9aa4b2;--card:#171a20;--line:#252a33;--acc:#6ea8ff;--warn:#e0b060}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:860px;margin:0 auto;padding:0 22px}
header{border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
header .wrap{display:flex;align-items:center;gap:18px;height:56px;flex-wrap:wrap}
.brand{font-weight:700;color:var(--fg);letter-spacing:-.01em}
header nav{display:flex;gap:16px;font-size:14px}header nav a{color:var(--mut)}
main{padding:26px 0 10px}
h1{font-size:30px;line-height:1.2;letter-spacing:-.02em;margin:6px 0 12px}
h2{font-size:20px;margin:34px 0 10px;letter-spacing:-.01em}
h3{font-size:16px;margin:20px 0 6px}
p{margin:10px 0}.lede{font-size:17px;color:var(--mut);max-width:66ch}
.mut{color:var(--mut)}.note{background:var(--card);border-left:3px solid var(--acc);padding:10px 14px;border-radius:0 8px 8px 0;font-size:14px;color:var(--mut)}
.crumbs{font-size:13px;color:var(--mut);margin-top:18px}
.crumbs a{color:var(--mut)}
.tw{overflow-x:auto;margin:16px 0;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--card);font-size:13px;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px;margin:14px 0}
.grid a{padding:10px 12px;background:var(--card);border:1px solid var(--line);border-radius:8px;font-size:14px;color:var(--fg)}
.grid a:hover{border-color:var(--acc);text-decoration:none}
.rel{margin-top:36px;border-top:1px solid var(--line);padding-top:8px;font-size:14.5px}
.faq h3{margin-bottom:2px}
.adslot{margin:26px 0;text-align:center;min-height:0}
footer{border-top:1px solid var(--line);margin-top:50px;padding:24px 0 40px;color:var(--mut);font-size:13px;background:var(--card)}
footer .wrap{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center}
footer a{color:var(--mut)}
input[type=search]{width:100%;padding:13px 15px;font-size:16px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--fg);margin:6px 0 18px}
input[type=search]:focus{outline:2px solid var(--acc);outline-offset:1px}
.stat{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:13px;margin:0 6px 6px 0;color:var(--mut)}
@media(max-width:560px){h1{font-size:25px}.wrap{padding:0 16px}}
"""


class Site:
    def __init__(self, slug_: str, brand: str, domain: str, tagline: str, description: str,
                 nav=None, lang="en", accent="#1f6feb", source_note: str = "",
                 analytics_token: str = CF_ANALYTICS_TOKEN, indexnow_key: str = DEFAULT_INDEXNOW_KEY,
                 author: str = "tekify.xyz"):
        self.slug = slug_
        self.brand = brand
        self.domain = domain.rstrip("/")
        self.base = "https://" + self.domain
        self.tagline = tagline
        self.description = description
        self.nav = list(nav or [])
        self.lang = lang
        self.accent = accent
        self.source_note = source_note
        self.analytics_token = analytics_token
        self.indexnow_key = indexnow_key
        self.author = author
        self.pages: dict[str, dict] = {}
        self.extra_files: dict[str, str] = {}

    # -- page creation ------------------------------------------------------
    def add(self, path: str, title: str, desc: str, body: str, *,
            crumbs=None, jsonld=None, extra_head: str = "", noindex=False,
            lastmod=None, og_type="website") -> None:
        path = self._norm(path)
        if path in self.pages:
            return
        self.pages[path] = dict(title=title, desc=desc, body=body, crumbs=crumbs or [],
                                jsonld=jsonld, extra_head=extra_head, noindex=noindex,
                                lastmod=lastmod or today(), og_type=og_type)

    @staticmethod
    def _norm(path: str) -> str:
        path = path.strip("/")
        if not path:
            return "index.html"
        if "." in path.rsplit("/", 1)[-1]:
            return path
        return path + "/index.html"

    # -- rendering ----------------------------------------------------------
    def _crumbs_html(self, crumbs) -> str:
        if not crumbs:
            return ""
        parts = [f'<a href="/">Home</a>'] + [
            f'<a href="{u}">{esc(t)}</a>' if u else esc(t) for t, u in crumbs]
        return '<div class="crumbs">' + " &rsaquo; ".join(parts) + "</div>"

    def _head(self, title, desc, canonical, noindex, og_type, extra_head) -> str:
        robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
        ads_head = AD_HEAD if MONETIZATION_ON else ""
        an = analytics_tag(self.slug)
        return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(truncate(desc, 158))}">
<link rel="canonical" href="{canonical}">
{robots}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(truncate(desc, 158))}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{esc(self.brand)}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="{self.accent}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>%E2%9C%A6</text></svg>">
<style>{CSS}</style>
{ads_head}
{an}
{extra_head}"""

    def _page_html(self, path, page) -> str:
        rel = path[:-len("index.html")] if path.endswith("index.html") else path
        canonical = self.base + "/" + rel
        ld = ""
        blocks = []
        if page["jsonld"]:
            blocks.append(page["jsonld"])
        if page["crumbs"]:
            blocks.append({"@context": "https://schema.org", "@type": "BreadcrumbList",
                           "itemListElement": [
                               {"@type": "ListItem", "position": i + 1, "name": t,
                                "item": self.base + (u or "/")}
                               for i, (t, u) in enumerate([("Home", "/")] + list(page["crumbs"]))]})
        blocks.append({"@context": "https://schema.org", "@type": "WebSite",
                       "name": self.brand, "url": self.base + "/"})
        for b in blocks:
            ld += '<script type="application/ld+json">' + json.dumps(b, separators=(",", ":")) + "</script>\n"
        nav = "".join(f'<a href="{u}">{esc(t)}</a>' for t, u in self.nav)
        footer_links = "".join(
            f'<a href="{u}">{esc(t)}</a>' for t, u in
            [("About", "/about/"), ("Privacy", "/privacy/"), ("Contact", "/contact/"), ("Sitemap", "/sitemap.xml")])
        net_links = "".join(
            f'<a href="{u}">{esc(t)}</a>' for t, u in NETWORK if u.rstrip("/") != self.base.rstrip("/"))
        note = f"<p>{self.source_note}</p>" if self.source_note else ""
        return f"""<!doctype html>
<html lang="{self.lang}">
<head>
{self._head(page['title'], page['desc'], canonical, page['noindex'], page['og_type'], page['extra_head'])}
{ld}</head>
<body>
<header><div class="wrap">
  <a class="brand" href="/">{esc(self.brand)}</a>
  <nav>{nav}</nav>
</div></header>
<main class="wrap">
{self._crumbs_html(page['crumbs'])}
{page['body']}
{ad(1)}
{ad(2)}
</main>
<footer><div class="wrap">
  {footer_links}
  <span class="mut netsep">Tekify network:</span> {net_links}
  {note}
  <span class="mut">© {datetime.date.today().year} {esc(self.brand)} · {esc(self.domain)}</span>
</div></footer>
</body>
</html>"""

    # -- boilerplate pages ---------------------------------------------------
    def add_standard_pages(self, extra_about: str = "") -> None:
        """About / Privacy / Contact — required for ad networks and E-E-A-T."""
        self.add("/about/", f"About {self.brand}",
                 f"What {self.brand} is, where its data comes from and how it is maintained.",
                 f"<h1>About {self.brand}</h1><p>{esc(self.tagline)}</p>"
                 f"<p>{esc(self.description)}</p>{extra_about}"
                 f"<p>This site is run by an automated publishing system. Pages are generated from "
                 f"structured data and refreshed regularly; every page states its data source.</p>"
                 f"<h2>Data &amp; corrections</h2><p>{esc(self.source_note) or 'Data is compiled from public sources.'} "
                 f"If you spot an error, contact us and it will be corrected in the next data refresh.</p>",
                 crumbs=[("About", None)])
        self.add("/privacy/", f"Privacy Policy — {self.brand}",
                 f"How {self.brand} handles data, cookies and advertising.",
                 "<h1>Privacy Policy</h1>"
                 "<p>This site does not require an account and does not ask for personal information.</p>"
                 "<h2>Analytics</h2><p>We use cookie-free, aggregated traffic statistics "
                 "(Cloudflare Web Analytics). No cross-site tracking identifiers are set.</p>"
                 "<h2>Advertising</h2><p>This site is supported by advertising. Advertising partners may set "
                 "cookies or use device identifiers to serve and measure ads. Where required by law, consent is "
                 "requested before personalised advertising. You can opt out of personalised ads through your "
                 "browser or platform settings, and in the EU/UK through the consent dialog.</p>"
                 "<h2>Log data</h2><p>Like any web server, our host processes technical request data "
                 "(IP address, user agent, URL) for security and delivery. It is not used to identify visitors.</p>"
                 "<h2>Third-party sites</h2><p>Links to other websites are outside our control; review their "
                 "privacy policies separately.</p>"
                 "<h2>Contact</h2><p>Questions: see the <a href=\"/contact/\">contact page</a>.</p>",
                 crumbs=[("Privacy", None)])
        self.add("/contact/", f"Contact {self.brand}",
                 f"How to reach the team behind {self.brand}.",
                 f"<h1>Contact</h1><p>Email: <strong>hello@{esc(self.domain)}</strong></p>"
                 "<p>We read everything. Data corrections and removal requests are prioritised and are usually "
                 "handled within a week.</p>"
                 "<p>For advertising and partnerships, use the same address with subject “ads”.</p>",
                 crumbs=[("Contact", None)])

    # -- extra files (js, json, text) ---------------------------------------
    def add_file(self, path: str, content: str) -> None:
        """Attach a raw file (search index, JS, JSON) to the deploy output."""
        self.extra_files[path.lstrip("/")] = content

    # -- write --------------------------------------------------------------
    def write(self, out_dir=None) -> pathlib.Path:
        out = pathlib.Path(out_dir) if out_dir else (ROOT / "sites" / self.slug / "site")
        if out.exists():
            import shutil
            import time
            for attempt in range(4):
                try:
                    shutil.rmtree(out)
                    break
                except PermissionError:
                    if attempt == 3:
                        print("WARN: output dir locked (OneDrive/sync?); overwriting in place")
                    else:
                        time.sleep(1.5 * (attempt + 1))
        out.mkdir(parents=True, exist_ok=True)
        for path, page in self.pages.items():
            p = out / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(self._page_html(path, page), encoding="utf-8")
        for rel, content in self.extra_files.items():
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        self._write_sitemaps(out)
        self._write_misc(out)
        return out

    def _write_sitemaps(self, out: pathlib.Path) -> None:
        urls = []
        for path, page in self.pages.items():
            if page["noindex"]:
                continue
            rel = path[:-len("index.html")] if path.endswith("index.html") else path
            loc = self.base + "/" + rel
            urls.append((loc, page["lastmod"]))
        ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
        chunks = [urls[i:i + 40000] for i in range(0, len(urls), 40000)] or [[]]
        if len(chunks) == 1:
            body = "".join(f"<url><loc>{xml_escape(l)}</loc><lastmod>{d}</lastmod></url>" for l, d in chunks[0])
            (out / "sitemap.xml").write_text(
                f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="{ns}">{body}</urlset>', encoding="utf-8")
            return
        idx = []
        for i, chunk in enumerate(chunks, 1):
            body = "".join(f"<url><loc>{xml_escape(l)}</loc><lastmod>{d}</lastmod></url>" for l, d in chunk)
            (out / f"sitemap-{i}.xml").write_text(
                f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="{ns}">{body}</urlset>', encoding="utf-8")
            idx.append(f"{self.base}/sitemap-{i}.xml")
        items = "".join(f"<sitemap><loc>{xml_escape(u)}</loc></sitemap>" for u in idx)
        (out / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="{ns}">{items}</sitemapindex>',
            encoding="utf-8")

    def _write_misc(self, out: pathlib.Path) -> None:
        (out / "robots.txt").write_text(
            "User-agent: *\nAllow: /\n\n"
            f"Sitemap: {self.base}/sitemap.xml\n", encoding="utf-8")
        (out / f"{self.indexnow_key}.txt").write_text(self.indexnow_key, encoding="utf-8")
        (out / "404.html").write_text(self._page_html("/404.html", dict(
            title=f"Page not found — {self.brand}", desc="Page not found",
            body='<h1>Page not found</h1><p>That URL does not exist. Try the '
                 '<a href="/">home page</a>.</p>',
            crumbs=[], jsonld=None, extra_head="", noindex=True, lastmod=today(), og_type="website")),
            encoding="utf-8")
        (out / "_headers").write_text(
            "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: SAMEORIGIN\n"
            "  Referrer-Policy: strict-origin-when-cross-origin\n"
            "  Permissions-Policy: geolocation=(), microphone=(), camera=()\n\n"
            "/data/*\n  Cache-Control: public, max-age=3600\n\n"
            "/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n", encoding="utf-8")
        if MONETIZATION_ON and ADS_TXT:
            (out / "ads.txt").write_text(ADS_TXT, encoding="utf-8")

    # -- validation ---------------------------------------------------------
    def validate(self, max_files=19000) -> bool:
        ok = True
        titles, descs = {}, {}
        internal = {"/" + (p[:-len("index.html")] if p.endswith("index.html") else p)
                    for p in self.pages}
        for path, page in self.pages.items():
            t = re.sub(r"\s+", " ", page["title"]).strip().lower()
            d = re.sub(r"\s+", " ", page["desc"]).strip().lower()
            titles[t] = titles.get(t, 0) + 1
            descs[d] = descs.get(d, 0) + 1
        dup_titles = sum(c - 1 for c in titles.values() if c > 1)
        dup_descs = sum(c - 1 for c in descs.values() if c > 1)
        if dup_titles:
            dup_keys = [k for k, c in titles.items() if c > 1][:5]
            for k in dup_keys:
                sample = [p for p in self.pages if re.sub(r"\s+", " ", self.pages[p]["title"]).strip().lower() == k][:3]
                print(f"WARN duplicate title: {k[:70]!r} -> {sample}")
            print(f"WARN duplicate titles: {dup_titles}"); ok = False
        if dup_descs:
            print(f"WARN duplicate descriptions: {dup_descs}"); ok = False
        if len(self.pages) > max_files - 60:
            print(f"FAIL too many pages for Pages Free: {len(self.pages)}"); ok = False
        broken = []
        sample = list(self.pages.items())
        for path, page in sample:
            for href in re.findall(r'href="(/[^"#?]*)"', page["body"]):
                if href not in internal and not href.endswith(".xml") and not href.endswith(".json"):
                    broken.append((path, href))
                    if len(broken) > 20:
                        break
        if broken:
            print(f"WARN broken internal links: {len(broken)} e.g. {broken[:5]}")
        print(f"VALIDATE: {len(self.pages)} pages, dup titles {dup_titles}, dup descs {dup_descs}, "
              f"broken {len(broken)} -> {'clean' if ok and not broken else 'issue'}")
        return ok and not broken


def cli():  # pragma: no cover
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate"])
    ap.add_argument("dir")
    a = ap.parse_args()
    d = pathlib.Path(a.dir)
    pages = len(list(d.rglob("index.html")))
    print(f"{pages} html pages in {d}")


if __name__ == "__main__":
    cli()
