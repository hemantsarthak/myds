#!/usr/bin/env python3
"""Generate per-state hospital-rating pages on the GitHub Pages site (docs/hospitals/).

Each page lists the state's top-rated hospitals from the CMS data and links to the matching state page
on the live directory. 51 data-driven pages targeting long-tail "<state> hospital ratings" queries on
the domain a crawler has been told to visit.
"""
import collections
import csv
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache"
BASE = "https://hemantsarthak.github.io/myds"
BEACON = '<script defer src="https://analytics.monetec2.workers.dev/e.js?site=ghpages"></script>'

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hospital ratings in {state} — CMS star ratings</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/hospitals/{code}.html">
{beacon}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"Hospital ratings in {state}","description":"{desc}","url":"{base}/hospitals/{code}.html","author":{{"@type":"Organization","name":"Tekify"}},"publisher":{{"@type":"Organization","name":"Tekify"}}}}</script>
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
<div class="crumbs"><a href="{base}/">Tekify</a> / <a href="{base}/hospitals/">state hospital ratings</a> / {state}</div>
<h1>Hospital ratings in {state}</h1>
<p class="lede">{lede}</p>
{body}
<footer>Data: CMS Provider Data Catalog (public domain). Full directory:
<a href="https://hospitals.tekify.xyz">US Hospitals</a> · <a href="https://tekify.xyz">tekify.xyz</a></footer>
</div></body></html>
"""


def main() -> None:
    rows = list(csv.DictReader((CACHE / "hospital_general.csv").open(encoding="utf-8-sig", errors="replace")))
    by_state = collections.defaultdict(list)
    for r in rows:
        st = (r.get("State") or "").strip()
        if st in STATE_NAMES:
            by_state[st].append(r)
    out = DOCS / "hospitals"
    out.mkdir(parents=True, exist_ok=True)
    index_items = []
    for st in sorted(by_state):
        group = by_state[st]
        rated = []
        for r in group:
            try:
                rating = int(str(r.get("Hospital overall rating")).strip())
            except (TypeError, ValueError):
                continue
            if 1 <= rating <= 5:
                rated.append((rating, r))
        rated.sort(key=lambda x: (-x[0], x[1].get("Facility Name", "")))
        avg = sum(x[0] for x in rated) / len(rated) if rated else 0
        top = rated[:10]
        rows_html = "".join(
            f'<tr><td>{html.escape(r["Facility Name"].title())}</td>'
            f'<td>{html.escape((r.get("City/Town") or "").title())}</td>'
            f'<td>{rating} of 5</td></tr>' for rating, r in top)
        table = (f"<table><tr><th>Hospital</th><th>City</th><th>CMS rating</th></tr>{rows_html}</table>"
                 if rows_html else "<p>No rated hospitals in the data for this state.</p>")
        state = STATE_NAMES[st]
        lede = (f"{len(group)} hospitals in {state}, of which {len(rated)} carry a CMS overall star rating "
                f"(average {avg:.2f} of 5). Below are the highest-rated.")
        body = (f"<h2>Top-rated hospitals</h2>{table}"
                f'<p>See every hospital in {state} with its measure groups, ownership, emergency-services '
                f'flag and contact details: <a href="https://hospitals.tekify.xyz/state/{st.lower()}/">'
                f'{state} hospitals directory</a>.</p>'
                f'<h2>How the rating works</h2><p>CMS combines mortality, safety, readmission, patient '
                f'experience and timely-care measures, each compared with what is expected for similar '
                f'hospitals. Small or specialty hospitals with too few measures are unrated — unrated is '
                f'not a bad rating.</p>'
                f'<p>Compare states: <a href="https://tekify.xyz/insights/hospital-ratings-by-state/">'
                f'which states have the best-rated hospitals?</a></p>')
        desc = f"CMS star ratings for hospitals in {state}: the {len(rated)} rated hospitals, the state average ({avg:.2f}) and the top-rated hospitals."
        (out / f"{st.lower()}.html").write_text(TEMPLATE.format(
            base=BASE, code=st.lower(), state=state, desc=html.escape(desc), lede=html.escape(lede),
            body=body, beacon=BEACON), encoding="utf-8")
        index_items.append((state, st, len(group), len(rated), avg))

    items = "\n".join(
        f'<li><a href="{BASE}/hospitals/{st.lower()}.html">{html.escape(name)}</a> — '
        f'{n} hospitals, {r} rated, average {avg:.2f}</li>' for name, st, n, r, avg in index_items)
    idx = TEMPLATE.format(base=BASE, code="", state="All states",
                          desc="CMS hospital star ratings by state.",
                          lede="Average CMS hospital star ratings by state, with the top-rated hospitals in each.",
                          body=f"<ul>{items}</ul>", beacon=BEACON)
    idx = idx.replace(f'<link rel="canonical" href="{BASE}/hospitals/.html">',
                      f'<link rel="canonical" href="{BASE}/hospitals/">')
    idx = idx.replace("Hospital ratings in All states", "Hospital ratings by state")
    (out / "index.html").write_text(idx, encoding="utf-8")
    print(f"wrote {len(index_items) + 1} state pages")


if __name__ == "__main__":
    main()
