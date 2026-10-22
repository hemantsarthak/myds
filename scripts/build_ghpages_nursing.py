#!/usr/bin/env python3
"""Generate per-state nursing-home rating pages on the GitHub Pages site (docs/nursing-homes/).

Same pattern as the hospital state pages: state averages, top-rated facilities, links to the live
directory. Targets long-tail "<state> nursing home ratings" queries on the crawl-target domain.
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
<title>Nursing home ratings in {state} — CMS stars and staffing</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/nursing-homes/{code}.html">
{beacon}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"Nursing home ratings in {state}","description":"{desc}","url":"{base}/nursing-homes/{code}.html","author":{{"@type":"Organization","name":"Tekify"}},"publisher":{{"@type":"Organization","name":"Tekify"}}}}</script>
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
<div class="crumbs"><a href="{base}/">Tekify</a> / <a href="{base}/nursing-homes/">state nursing-home ratings</a> / {state}</div>
<h1>Nursing home ratings in {state}</h1>
<p class="lede">{lede}</p>
{body}
<footer>Data: CMS Provider Data Catalog (public domain). Full directory:
<a href="https://nursinghomes.tekify.xyz">US Nursing Homes</a> · <a href="https://tekify.xyz">tekify.xyz</a></footer>
</div></body></html>
"""


def main() -> None:
    rows = list(csv.DictReader((CACHE / "nursing_homes.csv").open(encoding="utf-8-sig", errors="replace")))
    by_state = collections.defaultdict(list)
    for r in rows:
        st = (r.get("State") or "").strip()
        if st in STATE_NAMES:
            by_state[st].append(r)
    out = DOCS / "nursing-homes"
    out.mkdir(parents=True, exist_ok=True)
    index_items = []
    for st in sorted(by_state):
        group = by_state[st]
        rated = []
        for r in group:
            try:
                rating = int(str(r.get("Overall Rating")).strip())
            except (TypeError, ValueError):
                continue
            if 1 <= rating <= 5:
                rated.append((rating, r))
        rated.sort(key=lambda x: (-x[0], x[1].get("Provider Name", "")))
        avg = sum(x[0] for x in rated) / len(rated) if rated else 0
        top = rated[:10]
        rows_html = "".join(
            f'<tr><td>{html.escape(r["Provider Name"].title())}</td>'
            f'<td>{html.escape((r.get("City/Town") or "").title())}</td>'
            f'<td>{rating} of 5</td></tr>' for rating, r in top)
        table = (f"<table><tr><th>Nursing home</th><th>City</th><th>CMS rating</th></tr>{rows_html}</table>"
                 if rows_html else "<p>No rated facilities for this state in the data.</p>")
        state = STATE_NAMES[st]
        lede = (f"{len(group)} nursing homes in {state}, of which {len(rated)} carry a CMS overall star "
                f"rating (average {avg:.2f} of 5). Below are the highest-rated.")
        body = (f"<h2>Top-rated nursing homes</h2>{table}"
                f'<p>See every facility in {state} with staffing hours, turnover, inspection results, beds '
                f'and ownership: <a href="https://nursinghomes.tekify.xyz/state/{st.lower()}/">{state} '
                f'nursing-home directory</a>.</p>'
                f'<h2>What to check beyond the stars</h2><p>Staffing hours per resident and staff turnover '
                f'are often more informative than the overall rating. A facility with adequate hours but '
                f'high turnover struggles to provide consistent care. The directory lists both.</p>'
                f'<p>Compare states: <a href="https://tekify.xyz/insights/nursing-home-staffing-by-state/">'
                f'nursing-home staffing by state</a> · <a href="https://tekify.xyz/insights/largest-nursing-home-chains/">'
                f'largest nursing-home chains</a></p>')
        desc = (f"CMS star ratings for nursing homes in {state}: {len(rated)} rated facilities, state average "
                f"{avg:.2f} of 5, and the top-rated homes.")
        (out / f"{st.lower()}.html").write_text(TEMPLATE.format(
            base=BASE, code=st.lower(), state=state, desc=html.escape(desc), lede=html.escape(lede),
            body=body, beacon=BEACON), encoding="utf-8")
        index_items.append((state, st, len(group), len(rated), avg))

    items = "\n".join(
        f'<li><a href="{BASE}/nursing-homes/{st.lower()}.html">{html.escape(name)}</a> — '
        f'{n} facilities, {r} rated, average {avg:.2f}</li>' for name, st, n, r, avg in index_items)
    idx = TEMPLATE.format(base=BASE, code="", state="All states",
                          desc="CMS nursing-home star ratings by state.",
                          lede="Average CMS nursing-home star ratings by state, with the top-rated homes in each.",
                          body=f"<ul>{items}</ul>", beacon=BEACON)
    idx = idx.replace(f'<link rel="canonical" href="{BASE}/nursing-homes/.html">',
                      f'<link rel="canonical" href="{BASE}/nursing-homes/">')
    idx = idx.replace("Nursing home ratings in All states", "Nursing-home ratings by state")
    (out / "index.html").write_text(idx, encoding="utf-8")
    print(f"wrote {len(index_items) + 1} nursing-home state pages")


if __name__ == "__main__":
    main()
