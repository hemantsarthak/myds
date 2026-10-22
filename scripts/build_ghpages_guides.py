#!/usr/bin/env python3
"""Add original explainer guides to the GitHub Pages site (docs/guides/).

These are unique pages (not duplicated on tekify.xyz) that answer common questions and link to the
matching directory. They give the github.io site — the one domain a search engine has now been asked
to crawl — real content to rank, and every page is a doorway to a tekify.xyz property.
"""
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "https://hemantsarthak.github.io/myds"

GUIDES = [
    dict(
        slug="how-to-find-an-ifsc-code",
        title="How to find an IFSC code (and what each part means)",
        desc="What an IFSC code is, how the eleven characters break down, and how to look up any Indian "
             "bank branch's code safely before a transfer.",
        body="""
<p>An IFSC (Indian Financial System Code) identifies one specific bank branch. It is eleven characters:
four letters for the bank, a zero, and six characters for the branch. NEFT, RTGS and IMPS transfers
all need it, and it is printed on cheque books and account statements.</p>
<h2>Reading the code</h2>
<p>Take <code>HDFC0000001</code>: <code>HDFC</code> is the bank, the fifth character is always
<code>0</code>, and <code>000001</code> identifies the branch. Because the bank part is repeated across
every branch, a code that starts with the right letters can still point at the wrong branch.</p>
<h2>Look it up before you transfer</h2>
<p>Check the code against the branch record — bank, branch name, address, district and MICR code —
rather than trusting a code copied from a message. The free directory at
<a href="https://ifsccodes.tekify.xyz">IFSC Codes India</a> lists 19,511 branches with those fields,
searchable by code, bank, city or district.</p>
<h2>Common mistakes</h2>
<ul>
<li><strong>Confusing the MICR code with the IFSC code.</strong> MICR is a nine-digit cheque-clearing
code; IFSC is eleven characters and used for electronic transfers.</li>
<li><strong>Using a closed branch's code.</strong> Merged banks keep old codes active for a while but
transfers may be redirected; check the branch is still open.</li>
<li><strong>Typing the code by hand.</strong> Copy it, then verify the branch name on the record.</li>
</ul>
<p><a href="https://ifsccodes.tekify.xyz/search/">Search the IFSC directory</a> ·
<a href="https://ifsccodes.tekify.xyz/guides/">more IFSC explainers</a></p>
""",
        related=["what-is-a-zip-code", "how-cms-hospital-ratings-work"],
    ),
    dict(
        slug="what-is-a-zip-code",
        title="What a US ZIP code is (and what it is not)",
        desc="ZIP codes are postal delivery routes, not legal boundaries. What the five digits mean, why "
             "ZIPs and counties do not line up, and how to resolve one.",
        body="""
<p>A US ZIP code is a five-digit postal code: the first digit identifies a group of states, the next two
a sectional centre facility, and the last two a delivery area. ZIP+4 adds four digits for a specific
block or building.</p>
<h2>ZIP codes are routes, not places</h2>
<p>ZIP codes describe mail delivery, so they do not map cleanly onto cities or counties. One ZIP can
span several counties; a city can contain dozens of ZIPs; and some ZIPs cross state lines. That is why
address databases and census tools often disagree — they are reconciling two different geographies.</p>
<h2>Resolving a ZIP</h2>
<p>The free <a href="https://zipcodes.tekify.xyz">US ZIP Codes</a> directory shows each ZIP's primary
city, county, time zone, coordinates and neighbouring ZIPs, and links to the places and area codes that
overlap it. A compact JSON index is served at <code>/data/zips.json</code>.</p>
<h2>Why it matters</h2>
<ul>
<li>Sales tax and insurance rates are set by address, not ZIP — two houses in one ZIP can pay
different rates.</li>
<li>School districts and voting precincts ignore ZIP boundaries entirely.</li>
<li>For population and county data, use Census places and counties, not ZIPs.</li>
</ul>
<p><a href="https://zipcodes.tekify.xyz/search/">Search ZIP codes</a> ·
<a href="https://places.tekify.xyz">US places and counties</a></p>
""",
        related=["how-to-find-an-ifsc-code", "airport-codes-explained"],
    ),
    dict(
        slug="how-cms-hospital-ratings-work",
        title="How CMS hospital star ratings work",
        desc="What the five CMS measure groups are, how the overall rating is built, and three things the "
             "rating does not tell you.",
        body="""
<p>Medicare's Care Compare gives every US hospital an overall rating from one to five stars. It is built
from five groups of measures: mortality, safety of care, hospital readmission, patient experience and
timely and effective care. Each measure is compared with what CMS expects for hospitals treating
similar patients, then combined.</p>
<h2>Read the groups, not just the stars</h2>
<p>A hospital can be strong on survival and weak on readmission. The overall rating hides that trade-off,
so open the individual groups on the facility page before drawing conclusions. Small, rural and
specialty hospitals are often unrated because they report too few measures — unrated is not a bad
rating.</p>
<h2>What the rating does not tell you</h2>
<ul>
<li>Whether <em>your</em> surgeon or procedure is good at that hospital.</li>
<li>Emergency-department waiting times.</li>
<li>Whether the hospital is in your insurance network.</li>
</ul>
<p>Use it as one input alongside a referral and your network. The free
<a href="https://hospitals.tekify.xyz">US Hospitals</a> directory lists 5,888 hospitals with the
measure groups, ownership, emergency-services flag and contact details, built from CMS data.</p>
<p><a href="https://tekify.xyz/insights/hospital-ratings-by-state/">Which states have the best-rated
hospitals?</a> · <a href="https://hospitals.tekify.xyz/search/">Search hospitals</a></p>
""",
        related=["choosing-a-nursing-home", "dialysis-ratings-explained"],
    ),
    dict(
        slug="choosing-a-nursing-home",
        title="Choosing a nursing home: what the CMS rating does and does not tell you",
        desc="Health inspections, staffing and quality measures behind the CMS nursing-home rating — and "
             "what to ask when you visit.",
        body="""
<p>CMS rates nursing homes on three dimensions — health inspections, staffing and quality measures —
plus an overall rating. For families comparing options, staffing is often the most informative: it
covers nurse hours per resident per day and how often staff turn over.</p>
<h2>What to look at first</h2>
<ul>
<li><strong>Staffing hours and turnover.</strong> Consistent carers matter more than a brochure; high
turnover is a warning sign.</li>
<li><strong>Inspection results.</strong> Deficiencies are listed by scope and severity.</li>
<li><strong>Quality measures.</strong> Falls, pressure ulcers, antipsychotic use and similar outcomes.</li>
</ul>
<h2>What the rating does not capture</h2>
<p>Food, activities, the atmosphere of the building, or whether the home accepts your family member's
insurance. Those need a visit, a meal and questions. Use the rating to build a shortlist, not to make
the decision.</p>
<p>The free <a href="https://nursinghomes.tekify.xyz">US Nursing Homes</a> directory covers 15,056
facilities with ratings, staffing, beds, ownership and contact details from CMS.</p>
<p><a href="https://tekify.xyz/insights/nursing-home-staffing-by-state/">Nursing-home staffing by
state</a> · <a href="https://nursinghomes.tekify.xyz/search/">Search nursing homes</a></p>
""",
        related=["how-cms-hospital-ratings-work", "dialysis-ratings-explained"],
    ),
    dict(
        slug="dialysis-ratings-explained",
        title="Dialysis facility ratings explained",
        desc="The measures behind the CMS five-star dialysis rating, and the practical details worth "
             "checking when choosing a centre.",
        body="""
<p>CMS rates dialysis facilities from one to five stars using standardised measures: patient survival,
hospitalisation, hospital readmission, transfusion, emergency-department visits and the percentage of
patients waitlisted for a kidney transplant.</p>
<h2>Better than expected, as expected, worse than expected</h2>
<p>Each measure compares the facility with national expectations adjusted for its patients, so a small
rural centre and a large urban one are judged on their own case mix. The overall stars combine the
measures, but the individual results are worth reading separately.</p>
<h2>Practical details that matter as much</h2>
<ul>
<li>Whether the facility offers in-centre haemodialysis, peritoneal dialysis and home-haemodialysis
training.</li>
<li>How many stations it runs and whether it has a late shift.</li>
<li>Distance and travel time for three sessions a week.</li>
</ul>
<p>The free <a href="https://dialysis.tekify.xyz">US Dialysis Centers</a> directory lists 7,490
facilities with every measure, the services offered, station counts and phone numbers from CMS data.</p>
<p><a href="https://tekify.xyz/insights/dialysis-ratings-nationally/">The national rating picture</a> ·
<a href="https://dialysis.tekify.xyz/search/">Search dialysis facilities</a></p>
""",
        related=["how-cms-hospital-ratings-work", "choosing-a-nursing-home"],
    ),
    dict(
        slug="airport-codes-explained",
        title="Airport codes explained: IATA vs ICAO",
        desc="Why airports have two codes, how each is built, and how to look up an airport with its "
             "runways and nearby alternatives.",
        body="""
<p>Airports usually have two codes: a three-letter IATA code used by airlines and passengers (LHR, JFK)
and a four-letter ICAO code used by air-traffic control (EGLL, KJFK).</p>
<h2>How the codes are built</h2>
<p>IATA codes are assigned for commercial branding and are not systematic — some are obvious
(LHR for Heathrow), others are historical. ICAO codes are regional: the first letter identifies the
region (K for the contiguous US, E for northern Europe), followed by a country and airport
identifier.</p>
<h2>Look up either code</h2>
<p>The free <a href="https://airportcodes.tekify.xyz">Airport Codes</a> directory covers 10,181
airports from the OurAirports dataset: IATA and ICAO codes, type, elevation, runways, coordinates, city
and country, and the nearest airports with distances.</p>
<h2>Why nearby airports matter</h2>
<p>Cheap fares often involve a secondary airport an hour away. Each airport page lists the nearest
airports with distances, so the trade-off is visible before booking.</p>
<p><a href="https://airportcodes.tekify.xyz/search/">Search airports</a> ·
<a href="https://tekify.xyz/insights/airports-by-country/">Which countries have the most airports?</a></p>
""",
        related=["what-is-a-zip-code", "how-to-find-an-ifsc-code"],
    ),
]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Tekify guides</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/guides/{slug}.html">
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
code{{background:rgba(127,127,127,.12);padding:1px 4px;border-radius:4px}}
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
    out.mkdir(parents=True, exist_ok=True)
    titles = {g["slug"]: g["title"] for g in GUIDES}
    for g in GUIDES:
        rel = " · ".join(f'<a href="{BASE}/guides/{s}.html">{html.escape(titles[s])}</a>'
                         for s in g["related"])
        (out / f"{g['slug']}.html").write_text(TEMPLATE.format(
            base=BASE, slug=g["slug"], title=html.escape(g["title"]), desc=html.escape(g["desc"]),
            body=g["body"], related=rel), encoding="utf-8")
    cards = "\n".join(f'<li><a href="{BASE}/guides/{g["slug"]}.html">{html.escape(g["title"])}</a> — '
                      f'{html.escape(g["desc"])}</li>' for g in GUIDES)
    index_body = f"<ul>{cards}</ul>"
    (out / "index.html").write_text(TEMPLATE.format(
        base=BASE, slug="index", title="Guides", desc="Explainers on IFSC codes, ZIP codes, CMS ratings, "
        "nursing homes, dialysis and airport codes.", body=index_body, related="").replace(
        f'<link rel="canonical" href="{BASE}/guides/index.html">', f'<link rel="canonical" href="{BASE}/guides/">'),
        encoding="utf-8")
    print("wrote", len(GUIDES) + 1, "guide pages")


if __name__ == "__main__":
    main()
