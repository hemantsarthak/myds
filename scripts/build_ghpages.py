#!/usr/bin/env python3
"""Generate the GitHub Pages site under docs/ (landing page, dataset cards, analysis pages).

Why: github.io is a domain search engines already crawl. The more real, interlinked pages we publish
there, the better the chance a crawler reaches the links back to the tekify.xyz directories.

Run: python scripts/build_ghpages.py
"""
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "https://hemantsarthak.github.io/myds"

DATASETS = [
    dict(slug="ifsc-codes", title="Indian Bank IFSC Codes", site="https://ifsccodes.tekify.xyz",
         records="183,214 branches", source="Razorpay IFSC dataset (MIT licence)",
         desc="Every Indian bank branch with its IFSC code, address, district, state, MICR code and the "
              "transfer rails it supports (NEFT, RTGS, IMPS, UPI).",
         json="https://ifsccodes.tekify.xyz/data/bank/HDFC.json",
         release="https://github.com/hemantsarthak/myds/releases/download/datasets-v1/ifsc-codes-sample.csv"),
    dict(slug="us-zip-codes", title="US ZIP Codes", site="https://zipcodes.tekify.xyz",
         records="41,711 ZIP codes", source="US Census Bureau / GeoNames (public domain, CC BY 4.0)",
         desc="US ZIP codes with city, state, county, coordinates and population, plus the places and "
              "area codes that overlap each one.",
         json="https://zipcodes.tekify.xyz/data/zips.json",
         release="https://github.com/hemantsarthak/myds/releases/download/datasets-v1/us-zip-codes-sample.csv"),
    dict(slug="cms-hospital-ratings", title="US Hospital Ratings (CMS)", site="https://hospitals.tekify.xyz",
         records="5,419 hospitals", source="CMS Provider Data Catalog (public domain)",
         desc="Every Medicare-certified US hospital with its CMS overall star rating, ownership, type, "
              "emergency-services flag and quality measure counts.",
         json="https://hospitals.tekify.xyz/data/hospitals.json",
         release="https://github.com/hemantsarthak/myds/releases/download/datasets-v1/cms-hospital-ratings-sample.csv"),
    dict(slug="us-dialysis-facilities", title="US Dialysis Facilities (CMS)", site="https://dialysis.tekify.xyz",
         records="7,490 facilities", source="CMS Provider Data Catalog (public domain)",
         desc="Medicare-certified dialysis facilities with the CMS five-star rating, survival, "
              "hospitalisation and readmission measures, services offered and station counts.",
         json="https://dialysis.tekify.xyz/data/dialysis.json",
         release="https://github.com/hemantsarthak/myds/releases/download/datasets-v1/us-dialysis-facilities-sample.csv"),
]

INSIGHTS = [
    ("hospital-ratings-by-state", "Which US states have the best-rated hospitals?",
     "CMS hospital star ratings aggregated by state: Utah has 79% of rated hospitals at four stars or "
     "better, Mississippi 13%."),
    ("hospitals-by-ownership", "Hospital star ratings by ownership type",
     "Average CMS ratings for non-profit, for-profit and government hospitals."),
    ("hospitals-with-emergency-departments", "Which US hospitals have emergency departments?",
     "4,494 of 5,418 hospitals report emergency services (83%), with a state-by-state table."),
    ("nursing-home-staffing-by-state", "Nursing-home staffing ratings by state",
     "Average staffing and overall ratings for nursing homes, by state."),
    ("largest-nursing-home-chains", "America's largest nursing-home chains",
     "10,184 chain-affiliated facilities across 611 chains, ranked by size and rating."),
    ("dialysis-ratings-nationally", "US dialysis facilities: the national rating picture",
     "How CMS five-star dialysis ratings are distributed nationally."),
    ("indian-bank-branch-networks", "Which Indian banks have the most branches?",
     "The IFSC dataset counted by bank, with shares of the national total."),
    ("indian-bank-branches-by-state", "Indian bank branches by state",
     "183,208 IFSC codes by state — the geography of the banking network."),
    ("us-zip-codes-by-state", "US ZIP codes by state",
     "How the postal geography is distributed across states."),
    ("airports-by-country", "Which countries have the most airports?",
     "86,258 airports by country from the OurAirports dataset."),
]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Tekify</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/{path}">
<style>
:root{{--bg:#fff;--fg:#0f172a;--mut:#475569;--line:#e2e8f0;--accent:#2563eb}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0b1220;--fg:#e2e8f0;--mut:#94a3b8;--line:#1e293b;--accent:#60a5fa}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
.wrap{{max-width:820px;margin:0 auto;padding:36px 20px}}
a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}}
h1{{font-size:1.75rem;line-height:1.25;margin:0 0 .3em}}
.lede{{color:var(--mut);font-size:1.05rem}}
.crumbs{{font-size:.9rem;color:var(--mut);margin-bottom:1em}}
table{{border-collapse:collapse;width:100%;margin:1em 0}}
td,th{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
footer{{margin-top:2.5em;border-top:1px solid var(--line);padding-top:1em;color:var(--mut);font-size:.9rem}}
code{{background:rgba(127,127,127,.12);padding:1px 4px;border-radius:4px}}
</style>
</head>
<body><div class="wrap">
<div class="crumbs"><a href="{base}/">Tekify</a> / {crumb}</div>
<h1>{h1}</h1>
<p class="lede">{desc}</p>
{body}
<footer>Tekify — free data directories built from public datasets. <a href="https://tekify.xyz/">tekify.xyz</a> ·
<a href="https://github.com/hemantsarthak/myds">source</a></footer>
</div></body></html>
"""


def write(path: str, title: str, desc: str, h1: str, body: str, crumb: str) -> str:
    url = BASE + "/" + path
    out = DOCS / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEMPLATE.format(title=html.escape(title), desc=html.escape(desc),
                                   base=BASE, path=path, h1=html.escape(h1), body=body,
                                   crumb=crumb), encoding="utf-8")
    return url


def main() -> None:
    urls = [BASE + "/"]

    # ---- datasets index + cards
    cards = "\n".join(
        f'<li><a href="{BASE}/datasets/{d["slug"]}.html">{html.escape(d["title"])}</a> — '
        f'{html.escape(d["records"])} <span style="color:var(--mut)">{html.escape(d["source"])}</span></li>'
        for d in DATASETS)
    urls.append(write("datasets/index.html", "Open datasets — Tekify",
                      "Dataset cards and samples for the public data behind the Tekify directories.",
                      "Open datasets",
                      f"<ul>{cards}</ul>", '<a href="datasets/">datasets</a>'))
    for d in DATASETS:
        body = f"""
<table>
<tr><th>Records</th><td>{html.escape(d["records"])}</td></tr>
<tr><th>Source</th><td>{html.escape(d["source"])}</td></tr>
<tr><th>Live directory</th><td><a href="{d["site"]}">{d["site"]}</a></td></tr>
<tr><th>JSON index</th><td><a href="{d["json"]}">{html.escape(d["json"])}</a></td></tr>
<tr><th>Sample CSV</th><td><a href="{d["release"]}">download from GitHub Releases</a></td></tr>
</table>
<p>Each record has its own page on the live directory, with the fields that matter and links to the
surrounding records. The dataset card, licence and column list are in the
<a href="https://github.com/hemantsarthak/myds/tree/main/datasets/{d["slug"]}">repository</a>.</p>
"""
        urls.append(write(f"datasets/{d['slug']}.html", d["title"], d["desc"], d["title"], body,
                          f'<a href="datasets/">datasets</a> / {html.escape(d["title"])}'))

    # ---- insights index + pages
    links = "\n".join(f'<li><a href="{BASE}/insights/{slug}.html">{html.escape(title)}</a></li>'
                      for slug, title, _ in INSIGHTS)
    urls.append(write("insights/index.html", "Data analyses — Tekify",
                      "Short data-driven analyses computed from the public datasets behind the directories.",
                      "Data analyses", f"<ul>{links}</ul>", '<a href="insights/">insights</a>'))
    for slug, title, desc in INSIGHTS:
        body = (f'<p>{html.escape(desc)}</p>'
                f'<p>Read the full analysis with tables and charts: '
                f'<a href="https://tekify.xyz/insights/{slug}/">tekify.xyz/insights/{slug}/</a></p>'
                f'<p>Every number is computed at build time from the source dataset named on the page.</p>')
        urls.append(write(f"insights/{slug}.html", title, desc, title, body,
                          f'<a href="insights/">insights</a> / {html.escape(title)}'))

    # ---- sitemap
    entries = "\n".join(f"  <url><loc>{u}</loc><lastmod>2026-10-22</lastmod></url>" for u in urls)
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n", encoding="utf-8")
    print(f"generated {len(urls)} pages + sitemap under {DOCS}")


if __name__ == "__main__":
    main()
