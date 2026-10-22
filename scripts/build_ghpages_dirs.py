#!/usr/bin/env python3
"""Add a directory page per property to the GitHub Pages site (docs/directories/).

Each page describes one Tekify directory, its scale and what is inside, and links to the live site,
its search, its guides and its JSON index. More real, interlinked pages on a crawled domain.
"""
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "https://hemantsarthak.github.io/myds"

DIRS = [
    dict(slug="ifsc-codes", title="IFSC Codes India", site="https://ifsccodes.tekify.xyz",
         pages="19,511 branch pages", records="183,214 branches in the dataset",
         what="Every Indian bank branch with its IFSC code, bank name, branch, address, district, "
              "state, MICR code and the transfer rails it supports (NEFT, RTGS, IMPS, UPI).",
         use="Look up a code before making a transfer, or find the branch that owns a code.",
         json="https://ifsccodes.tekify.xyz/data/bank/HDFC.json",
         guides="https://ifsccodes.tekify.xyz/guides/"),
    dict(slug="us-zip-codes", title="US ZIP Codes", site="https://zipcodes.tekify.xyz",
         pages="17,759 ZIP pages", records="41,711 ZIP codes in the dataset",
         what="Each ZIP code with its city, state, county, time zone, coordinates and the neighbouring "
              "ZIPs, plus links to the places and area codes that overlap it.",
         use="Resolve a ZIP to a city and county, or check which area codes and places share it.",
         json="https://zipcodes.tekify.xyz/data/zips.json",
         guides="https://zipcodes.tekify.xyz/guides/"),
    dict(slug="us-places", title="US Places & Counties", site="https://places.tekify.xyz",
         pages="19,203 place pages", records="Places and counties with 2023 population estimates",
         what="US cities, towns, villages and counties with 2023 Census population estimates, county "
              "assignment, and the ZIP codes and area codes that fall inside each place.",
         use="Check a place's population and which county it belongs to.",
         json="https://places.tekify.xyz/data/places.json",
         guides="https://places.tekify.xyz/guides/"),
    dict(slug="us-colleges", title="US Colleges", site="https://colleges.tekify.xyz",
         pages="6,056 college pages", records="NCES/IPEDS data for 6,056 institutions",
         what="Acceptance rate, in-state and out-of-state tuition, average net price by family income, "
              "graduation and retention rates, enrollment and campus setting for every US college.",
         use="Compare colleges on what students actually pay, not the sticker price.",
         json="https://colleges.tekify.xyz/data/colleges.json",
         guides="https://colleges.tekify.xyz/guides/"),
    dict(slug="us-hospitals", title="US Hospitals", site="https://hospitals.tekify.xyz",
         pages="5,888 hospital pages", records="CMS data for 5,419 hospitals",
         what="CMS overall star ratings with the five measure groups (mortality, safety, readmission, "
              "patient experience, timely care), hospital type, ownership, emergency-services flag and "
              "contact details.",
         use="Check a hospital's CMS rating and quality groups before scheduling care.",
         json="https://hospitals.tekify.xyz/data/hospitals.json",
         guides="https://hospitals.tekify.xyz/guides/"),
    dict(slug="us-nursing-homes", title="US Nursing Homes", site="https://nursinghomes.tekify.xyz",
         pages="15,056 facility pages", records="CMS data for 14,700+ nursing homes",
         what="Overall, health-inspection, staffing and quality-measure ratings, nurse staffing hours "
              "per resident per day, staff turnover, certified beds and ownership.",
         use="Build a shortlist of nursing homes and compare staffing and inspection results.",
         json="https://nursinghomes.tekify.xyz/data/nursinghomes.json",
         guides="https://nursinghomes.tekify.xyz/guides/"),
    dict(slug="us-home-health", title="US Home Health Agencies", site="https://homehealth.tekify.xyz",
         pages="12,777 agency pages", records="CMS data for 12,400+ agencies",
         what="CMS quality ratings, patient-experience measures, services offered, ownership and "
              "contact details for Medicare-certified home-health agencies.",
         use="Compare home-health agencies on quality and services.",
         json="https://homehealth.tekify.xyz/data/homehealth.json",
         guides="https://homehealth.tekify.xyz/guides/"),
    dict(slug="us-dialysis", title="US Dialysis Centers", site="https://dialysis.tekify.xyz",
         pages="7,809 facility pages", records="CMS data for 7,490 facilities",
         what="CMS five-star ratings with patient survival, hospitalisation, readmission, transfusion "
              "and ED-visit measures, transplant-waitlist percentage, dialysis stations, late-shift flag "
              "and the treatment types offered.",
         use="Compare dialysis facilities on outcomes and the services they offer.",
         json="https://dialysis.tekify.xyz/data/dialysis.json",
         guides="https://dialysis.tekify.xyz/guides/"),
    dict(slug="area-codes", title="Area Codes", site="https://areacodes.tekify.xyz",
         pages="6,954 code pages", records="NANP area codes and world dialing codes",
         what="North American area codes and international dialing prefixes, searchable by code, city, "
              "state or country, with the places each code covers.",
         use="Identify where a phone number is from, or find the dialing prefix for a country.",
         json="https://areacodes.tekify.xyz/data/search.json",
         guides="https://areacodes.tekify.xyz/guides/"),
    dict(slug="airport-codes", title="Airport Codes", site="https://airportcodes.tekify.xyz",
         pages="10,181 airport pages", records="OurAirports data for 10,181 airports",
         what="IATA and ICAO codes, airport type, elevation, runways, coordinates, city and country, "
              "and the nearest airports with distances.",
         use="Look up an airport code, or find airports near a city.",
         json="https://airportcodes.tekify.xyz/data/airports.json",
         guides="https://airportcodes.tekify.xyz/guides/"),
    dict(slug="calculators", title="Calculators", site="https://calculators.tekify.xyz",
         pages="75 calculators", records="Money, salary, health, date and unit tools",
         what="Loan, mortgage, retirement, investing, salary, debt, health, date and conversion "
              "calculators — each with the formula, a worked example, common mistakes and live results.",
         use="Answer a money or health question in one page, without signing up.",
         json=None,
         guides="https://calculators.tekify.xyz/guides/"),
    dict(slug="tekify", title="Tekify hub", site="https://tekify.xyz",
         pages="16 pages", records="The network index",
         what="The index of the whole network: all twelve directories, ten data analyses with charts, "
              "press page, JSON data access and contact.",
         use="Start here to find the right directory or read the data analyses.",
         json=None,
         guides="https://tekify.xyz/insights/"),
]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Tekify data directory</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/directories/{slug}.html">
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
</style>
</head>
<body><div class="wrap">
<div class="crumbs"><a href="{base}/">Tekify</a> / <a href="{base}/directories/">directories</a> / {title}</div>
<h1>{title}</h1>
<p class="lede">{desc}</p>
<table>
<tr><th>Scale</th><td>{pages} · {records}</td></tr>
<tr><th>Live site</th><td><a href="{site}/">{site}</a></td></tr>
<tr><th>What is inside</th><td>{what}</td></tr>
<tr><th>What it is for</th><td>{use}</td></tr>
<tr><th>Search</th><td><a href="{site}/search/">search the directory</a></td></tr>
<tr><th>Guides</th><td><a href="{guides}">explainers</a></td></tr>
{json_row}
</table>
<p>Every record is generated from a documented public dataset and states its source. Pages are static,
fast, and carry no accounts, no cookie walls and no personal-data collection.</p>
<footer>Tekify — free data directories built from public datasets. <a href="https://tekify.xyz/">tekify.xyz</a> ·
<a href="https://github.com/hemantsarthak/myds">source</a></footer>
</div></body></html>
"""


def main() -> None:
    out = DOCS / "directories"
    out.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        desc = f"{d['title']}: {d['pages']} from public data — {d['what'][:120]}..."
        json_row = (f'<tr><th>JSON index</th><td><a href="{d["json"]}">{d["json"]}</a></td></tr>'
                    if d["json"] else "")
        (out / f"{d['slug']}.html").write_text(TEMPLATE.format(
            base=BASE, slug=d["slug"], title=html.escape(d["title"]), desc=html.escape(desc),
            pages=html.escape(d["pages"]), records=html.escape(d["records"]), site=d["site"],
            what=html.escape(d["what"]), use=html.escape(d["use"]), guides=d["guides"],
            json_row=json_row), encoding="utf-8")
    cards = "\n".join(
        f'<li><a href="{BASE}/directories/{d["slug"]}.html">{html.escape(d["title"])}</a> — '
        f'{html.escape(d["pages"])}</li>' for d in DIRS)
    (out / "index.html").write_text(
        TEMPLATE.format(base=BASE, slug="index", title="Directories",
                        desc="All twelve Tekify data directories, what is in each and how to use them.",
                        pages="12 directories", records="121,000+ record pages",
                        site="https://tekify.xyz", what=f"<ul>{cards}</ul>", use="Pick a directory.",
                        guides="https://tekify.xyz/insights/", json_row="").replace(
            "<h1>Directories</h1>", "<h1>Tekify directories</h1>"), encoding="utf-8")
    print("wrote", len(DIRS) + 1, "directory pages")


if __name__ == "__main__":
    main()
