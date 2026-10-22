#!/usr/bin/env python3
"""Add four more guides to the GitHub Pages site and wire the analytics beacon into every generated
page, so visits (from Bing results or AI assistants) are measurable.
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "https://hemantsarthak.github.io/myds"
BEACON = '<script defer src="https://analytics.monetec2.workers.dev/e.js?site=ghpages"></script>'

GUIDES = [
    dict(
        slug="comparing-colleges-on-net-price",
        title="How to compare US colleges on net price, not sticker price",
        desc="Sticker price tells you little. Average net price — tuition and living costs minus grant "
             "aid — is the number that matters, and the gap between colleges is large.",
        body="""
<p>US colleges publish a sticker price that almost nobody pays. The number that matters is the
<strong>average net price</strong>: tuition, fees, books and living costs minus grant and scholarship
aid. It is what students actually pay, and it varies enormously between colleges with similar sticker
prices.</p>
<h2>What to compare</h2>
<ul>
<li><strong>Net price by family income band.</strong> A college can be expensive on average and cheap
for low-income students, or the reverse.</li>
<li><strong>Graduation and retention rates.</strong> A cheap college that students do not finish is
expensive in the end.</li>
<li><strong>In-state vs out-of-state tuition</strong> at public universities — the difference can be
tens of thousands a year.</li>
</ul>
<h2>Where to find it</h2>
<p>The free <a href="https://colleges.tekify.xyz">US Colleges</a> directory lists 6,056 institutions
with acceptance rates, tuition, average net price by income band, graduation and retention rates, all
from federal IPEDS data. Compare a shortlist side by side rather than relying on a single ranking.</p>
<p><a href="https://colleges.tekify.xyz/search/">Search colleges</a> ·
<a href="https://colleges.tekify.xyz/guides/">more college explainers</a></p>
""",
        related=["what-is-a-zip-code", "free-money-calculators"],
    ),
    dict(
        slug="free-money-calculators",
        title="The money calculators worth bookmarking",
        desc="Loan payments, mortgage costs, retirement withdrawal, debt payoff, take-home pay and "
             "compound growth — each with the formula shown, so you can check the answer yourself.",
        body="""
<p>Most financial questions reduce to a handful of formulas. These calculators show the arithmetic on
the page — the formula, a worked example and the assumptions — so you can verify the result instead of
trusting a black box.</p>
<h2>Borrowing</h2>
<ul>
<li><strong>Loan and mortgage payments</strong> — monthly payment, total interest and an amortisation
schedule.</li>
<li><strong>Refinance break-even</strong> — how many months before the lower rate pays off the closing
costs.</li>
<li><strong>Debt payoff</strong> — how long a balance takes to clear and what extra payments save.</li>
</ul>
<h2>Earning and saving</h2>
<ul>
<li><strong>Take-home pay</strong> — federal brackets, FICA and the standard deduction.</li>
<li><strong>Self-employment tax</strong> — the 15.3% both-halves calculation for 1099 income.</li>
<li><strong>Compound interest and savings goals</strong> — what a monthly contribution becomes.</li>
</ul>
<h2>Retirement</h2>
<p>Retirement withdrawal (the 4% rule), 401(k) growth, dividend income and the nest egg needed for a
target income.</p>
<p>All 75 calculators are free, need no account and run entirely in the browser:
<a href="https://calculators.tekify.xyz">Tekify Calculators</a>.</p>
<p><a href="https://calculators.tekify.xyz/search/">Search calculators</a></p>
""",
        related=["comparing-colleges-on-net-price", "how-cms-hospital-ratings-work"],
    ),
    dict(
        slug="area-codes-explained",
        title="North American area codes: overlays, splits and how to look one up",
        desc="How NANP area codes work, why one city can have several, and how to find where a phone "
             "number is from.",
        body="""
<p>The North American Numbering Plan divides the US, Canada and much of the Caribbean into three-digit
area codes. The format is NXX-NXX-XXXX: area code, central-office code, line number.</p>
<h2>Overlays and splits</h2>
<p>When a region runs out of numbers, regulators either split it (the old code keeps part of the
region) or overlay it (a new code covers the same area and everyone dials ten digits). Overlays are why
one city may have several area codes — New York, Los Angeles and Houston all have several.</p>
<h2>Look up a code</h2>
<p>The free <a href="https://areacodes.tekify.xyz">Area Codes</a> directory covers NANP area codes and
world dialing prefixes, searchable by code, city, state or country, with the places each code
covers.</p>
<h2>Careful with mobile numbers</h2>
<p>Number portability means a phone's area code no longer reliably indicates where its owner lives —
it shows where the number was first assigned. For landlines it is still a good guide.</p>
<p><a href="https://areacodes.tekify.xyz/search/">Search area codes</a> ·
<a href="https://tekify.xyz/insights/airports-by-country/">Airports by country</a></p>
""",
        related=["what-is-a-zip-code", "airport-codes-explained"],
    ),
    dict(
        slug="places-counties-and-zips",
        title="US places, counties and ZIP codes: which geography answers your question",
        desc="Places, counties and ZIP codes are three different maps of the same country. Using the "
             "wrong one is the most common data mistake.",
        body="""
<p>The US has three overlapping geographies that people use interchangeably — and that is the source of
most confusion in address and population data.</p>
<h2>Places (cities, towns, villages)</h2>
<p>Incorporated places are legal entities with boundaries and governments. The Census publishes
population estimates for each. A place can sit in more than one county, and a large metro area contains
many places.</p>
<h2>Counties</h2>
<p>Counties are the main administrative division of a state. Every piece of land belongs to exactly one
county (with a few independent cities as exceptions). Property records, courts and many services are
organised by county.</p>
<h2>ZIP codes</h2>
<p>ZIP codes are postal delivery routes, not legal boundaries. They cross county and city lines, and
they change when the postal service reorganises delivery.</p>
<h2>Which to use</h2>
<ul>
<li><strong>Population of a city</strong> → Census place.</li>
<li><strong>Property, taxes, courts</strong> → county.</li>
<li><strong>Mail delivery</strong> → ZIP code.</li>
<li><strong>School districts and voting precincts</strong> → neither; use their own maps.</li>
</ul>
<p>The free directories: <a href="https://places.tekify.xyz">US Places &amp; Counties</a> (2023
population estimates, county assignment) and <a href="https://zipcodes.tekify.xyz">US ZIP Codes</a>
(city, county, time zone, neighbouring ZIPs).</p>
""",
        related=["what-is-a-zip-code", "area-codes-explained"],
    ),
]

ARTICLE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Tekify guides</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/guides/{slug}.html">
{beacon}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{title}","description":"{desc}","url":"{base}/guides/{slug}.html","author":{{"@type":"Organization","name":"Tekify"}},"publisher":{{"@type":"Organization","name":"Tekify"}},"datePublished":"2026-10-22","dateModified":"2026-10-22"}}</script>
<style>
:root{{--bg:#fff;--fg:#0f172a;--mut:#475569;--line:#e2e8f0;--accent:#2563eb}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0b1220;--fg:#e2e8f0;--mut:#94a3b8;--line:#1e293b;--accent:#60a5fa}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
.wrap{{max-width:780px;margin:0 auto;padding:36px 20px}}
a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}}
h1{{font-size:1.75rem;line-height:1.25;margin:0 0 .4em}}
h2{{font-size:1.2rem;margin:1.8em 0 .4em}}
.lede{{color:var(--mut);font-size:1.05rem}}
.crumbs{{font-size:.9rem;color:var(--mut);margin-bottom:1em}}
footer{{margin-top:2.5em;border-top:1px solid var(--line);padding-top:1em;color:var(--mut);font-size:.9rem}}
.related{{border-top:1px solid var(--line);margin-top:2em;padding-top:1em}}
</style>
</head>
<body><div class="wrap">
<div class="crumbs"><a href="{base}/">Tekify</a> / <a href="{base}/guides/">guides</a> / {title}</div>
<h1>{title}</h1>
<p class="lede">{desc}</p>
{body}
<div class="related"><p><strong>Related guides:</strong> {related}</p>
<p>All Tekify directories are free, source-stated and built from public datasets:
<a href="https://tekify.xyz/">tekify.xyz</a>.</p></div>
<footer>Tekify — free data directories built from public datasets. <a href="https://github.com/hemantsarthak/myds">source</a></footer>
</div></body></html>
"""


def main() -> None:
    out = DOCS / "guides"
    titles = {g["slug"]: g["title"] for g in GUIDES}
    titles.update({
        "how-to-find-an-ifsc-code": "How to find an IFSC code",
        "what-is-a-zip-code": "What a US ZIP code is (and what it is not)",
        "how-cms-hospital-ratings-work": "How CMS hospital star ratings work",
        "choosing-a-nursing-home": "Choosing a nursing home",
        "dialysis-ratings-explained": "Dialysis facility ratings explained",
        "airport-codes-explained": "Airport codes explained: IATA vs ICAO",
    })
    for g in GUIDES:
        rel = " · ".join(f'<a href="{BASE}/guides/{s}.html">{html.escape(titles[s])}</a>'
                         for s in g["related"])
        (out / f"{g['slug']}.html").write_text(ARTICLE_TEMPLATE.format(
            base=BASE, slug=g["slug"], title=html.escape(g["title"]), desc=html.escape(g["desc"]),
            body=g["body"], related=rel, beacon=BEACON), encoding="utf-8")
    # add the new guides to the guides index
    idx = out / "index.html"
    h = idx.read_text(encoding="utf-8")
    extra = "\n".join(f'<li><a href="{BASE}/guides/{g["slug"]}.html">{html.escape(g["title"])}</a> — '
                      f'{html.escape(g["desc"])}</li>' for g in GUIDES)
    if GUIDES[0]["slug"] not in h:
        h = h.replace("</ul>", extra + "\n</ul>", 1)
        idx.write_text(h, encoding="utf-8")
    print("added", len(GUIDES), "guides")


if __name__ == "__main__":
    main()
