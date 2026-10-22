#!/usr/bin/env python3
"""Generate per-state airport pages on the GitHub Pages site (docs/airports/).

Uses the OurAirports dataset (US states via iso_region) and links to the matching state page on the
live airport directory.
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
<title>Airports in {state} — IATA and ICAO codes</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/airports/{code}.html">
{beacon}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"Airports in {state}","description":"{desc}","url":"{base}/airports/{code}.html","author":{{"@type":"Organization","name":"Tekify"}},"publisher":{{"@type":"Organization","name":"Tekify"}}}}</script>
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
<div class="crumbs"><a href="{base}/">Tekify</a> / <a href="{base}/airports/">airports by state</a> / {state}</div>
<h1>Airports in {state}</h1>
<p class="lede">{lede}</p>
{body}
<footer>Data: OurAirports (public domain). Full directory:
<a href="https://airportcodes.tekify.xyz">Airport Codes</a> · <a href="https://tekify.xyz">tekify.xyz</a></footer>
</div></body></html>
"""


def main() -> None:
    rows = list(csv.DictReader((CACHE / "airports.csv").open(encoding="utf-8-sig", errors="replace")))
    by_state = collections.defaultdict(list)
    for r in rows:
        region = (r.get("iso_region") or "").strip()
        if not region.startswith("US-"):
            continue
        st = region[3:]
        if st in STATE_NAMES:
            by_state[st].append(r)
    out = DOCS / "airports"
    out.mkdir(parents=True, exist_ok=True)
    index_items = []
    for st in sorted(by_state):
        group = by_state[st]
        large = [r for r in group if (r.get("type") or "") in ("large_airport", "medium_airport")]
        large.sort(key=lambda r: (r.get("type") != "large_airport", r.get("name") or ""))
        table = "".join(
            f'<tr><td>{html.escape((r.get("name") or "").title())}</td>'
            f'<td>{html.escape((r.get("iata_code") or "—"))}</td>'
            f'<td>{html.escape((r.get("icao_code") or "—"))}</td>'
            f'<td>{html.escape((r.get("municipality") or "").title())}</td></tr>'
            for r in large[:15])
        body = (f"<h2>Commercial and regional airports</h2>"
                f"<table><tr><th>Airport</th><th>IATA</th><th>ICAO</th><th>City</th></tr>{table}</table>"
                f'<p>See every airport in {STATE_NAMES[st]} — including general aviation fields, heliports '
                f'and seaplane bases — with runways, elevation and the nearest airports: '
                f'<a href="https://airportcodes.tekify.xyz/search/">search the airport directory</a>.</p>'
                f'<h2>Codes</h2><p>IATA codes (three letters) are used by airlines and passengers; ICAO '
                f'codes (four letters) by air-traffic control. The first letter of a US ICAO code is '
                f'usually K.</p>')
        state = STATE_NAMES[st]
        lede = (f"{len(group)} airports and airfields in {state}, of which {len(large)} are large or "
                f"medium commercial airports. Below are the main ones.")
        desc = (f"Airports in {state}: {len(large)} commercial and regional airports with IATA and ICAO "
                f"codes, plus {len(group)} airfields in the dataset.")
        (out / f"{st.lower()}.html").write_text(TEMPLATE.format(
            base=BASE, code=st.lower(), state=state, desc=html.escape(desc),
            lede=html.escape(lede), body=body, beacon=BEACON), encoding="utf-8")
        index_items.append((state, st, len(group), len(large)))

    items = "\n".join(
        f'<li><a href="{BASE}/airports/{st.lower()}.html">{html.escape(name)}</a> — '
        f'{n} airfields, {m} commercial/regional</li>' for name, st, n, m in index_items)
    idx = TEMPLATE.format(base=BASE, code="", state="All states",
                          desc="Airports by US state.", lede="Airports by US state, with IATA and ICAO codes.",
                          body=f"<ul>{items}</ul>", beacon=BEACON)
    idx = idx.replace(f'<link rel="canonical" href="{BASE}/airports/.html">',
                      f'<link rel="canonical" href="{BASE}/airports/">')
    idx = idx.replace("Airports in All states", "Airports by state")
    (out / "index.html").write_text(idx, encoding="utf-8")
    print(f"wrote {len(index_items) + 1} airport state pages")


if __name__ == "__main__":
    main()
