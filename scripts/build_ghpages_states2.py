#!/usr/bin/env python3
"""Generate per-state dialysis-facility and college pages on the GitHub Pages site.

Same pattern as the hospital/nursing-home state pages: state averages, top-rated facilities/colleges,
links to the live directory. Targets long-tail "<state> dialysis" and "<state> colleges" queries on the
crawl-target domain.
"""
import collections
import csv
import html
import pathlib
import zipfile

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
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}/{section}/{code}.html">
{beacon}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{h1}","description":"{desc}","url":"{base}/{section}/{code}.html","author":{{"@type":"Organization","name":"Tekify"}},"publisher":{{"@type":"Organization","name":"Tekify"}}}}</script>
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
<div class="crumbs"><a href="{base}/">Tekify</a> / <a href="{base}/{section}/">{section_title}</a> / {state}</div>
<h1>{h1}</h1>
<p class="lede">{lede}</p>
{body}
<footer>{footer}</footer>
</div></body></html>
"""


def write_pages(section: str, section_title: str, title_tpl: str, h1_tpl: str, desc_tpl: str,
                footer: str, state_items: dict) -> None:
    out = DOCS / section
    out.mkdir(parents=True, exist_ok=True)
    index_items = []
    for st, data in sorted(state_items.items()):
        name = STATE_NAMES[st]
        body = data["body"].format(site=data["site"], st=st.lower(), state=name)
        (out / f"{st.lower()}.html").write_text(TEMPLATE.format(
            base=BASE, section=section, code=st.lower(), state=name,
            title=title_tpl.format(state=name), h1=h1_tpl.format(state=name),
            desc=html.escape(desc_tpl.format(state=name, n=data["n"], rated=data["rated"], avg=data["avg"])),
            lede=html.escape(data["lede"].format(state=name)), body=body, beacon=BEACON,
            section_title=section_title, footer=footer), encoding="utf-8")
        index_items.append((name, st, data["n"], data["rated"], data["avg"]))
    items = "\n".join(
        f'<li><a href="{BASE}/{section}/{st.lower()}.html">{html.escape(name)}</a> — '
        f'{n} listed, {rated} rated, average {avg:.2f}</li>' for name, st, n, rated, avg in index_items)
    idx = TEMPLATE.format(base=BASE, section=section, code="", state="All states",
                          title=section_title, h1=section_title,
                          desc=html.escape(f"{section_title} — all states."),
                          lede=f"{section_title} across the United States.",
                          body=f"<ul>{items}</ul>", beacon=BEACON,
                          section_title=section_title, footer=footer)
    idx = idx.replace(f'<link rel="canonical" href="{BASE}/{section}/.html">',
                      f'<link rel="canonical" href="{BASE}/{section}/">')
    (out / "index.html").write_text(idx, encoding="utf-8")
    print(f"{section}: {len(index_items) + 1} pages")


def dialysis_pages() -> None:
    rows = list(csv.DictReader((CACHE / "dialysis.csv").open(encoding="utf-8-sig", errors="replace")))
    by_state = collections.defaultdict(list)
    for r in rows:
        st = (r.get("State") or "").strip()
        if st in STATE_NAMES:
            by_state[st].append(r)
    items = {}
    for st, group in by_state.items():
        rated = []
        for r in group:
            try:
                v = int(str(r.get("Five Star")).strip())
            except (TypeError, ValueError):
                continue
            if 1 <= v <= 5:
                rated.append((v, r))
        rated.sort(key=lambda x: (-x[0], x[1].get("Facility Name", "")))
        avg = sum(x[0] for x in rated) / len(rated) if rated else 0
        top = "".join(
            f'<tr><td>{html.escape((r.get("Facility Name") or "").title())}</td>'
            f'<td>{html.escape((r.get("City/Town") or "").title())}</td><td>{v} of 5</td></tr>'
            for v, r in rated[:10])
        items[st] = dict(
            n=len(group), rated=len(rated), avg=avg, site="https://dialysis.tekify.xyz",
            lede=f"{len(group)} dialysis facilities in {{state}}, {len(rated)} with a CMS five-star "
                 f"rating (average {avg:.2f}). Below are the highest-rated.",
            body="<h2>Top-rated dialysis facilities</h2><table><tr><th>Facility</th><th>City</th>"
                 "<th>CMS rating</th></tr>" + top + "</table>"
                 "<p>See every facility in {state} with survival, hospitalisation, readmission and "
                 "transfusion measures, services offered and station counts: "
                 '<a href="{site}/state/{st}/">{state} dialysis directory</a>.</p>'
                 '<h2>Beyond the stars</h2><p>Check whether a facility offers peritoneal dialysis and '
                 "home-haemodialysis training, how many stations it runs and whether it has a late shift — "
                 "those details often matter more than a half-star difference.</p>"
                 '<p>Compare: <a href="https://tekify.xyz/insights/dialysis-ratings-nationally/">the '
                 "national dialysis rating picture</a></p>")
    write_pages("dialysis", "Dialysis facilities by state",
                "Dialysis facility ratings in {state} — CMS five-star data",
                "Dialysis facilities in {state}",
                "CMS five-star ratings for dialysis facilities in {state}: {rated} rated facilities, average {avg:.2f}, top-rated centres listed.",
                "Data: CMS Provider Data Catalog (public domain). Full directory: "
                '<a href="https://dialysis.tekify.xyz">US Dialysis Centers</a> · '
                '<a href="https://tekify.xyz">tekify.xyz</a>', items)


def college_pages() -> None:
    hd_path = next((CACHE / "ipeds").glob("HD2023.csv"), None)
    if not hd_path:
        with zipfile.ZipFile(CACHE / "ipeds" / "HD2023.zip") as z:
            with z.open("HD2023.csv") as f:
                import io
                rows = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")))
    else:
        rows = list(csv.DictReader(hd_path.open(encoding="utf-8-sig", errors="replace")))
    by_state = collections.defaultdict(list)
    for r in rows:
        st = (r.get("STABBR") or "").strip()
        if st in STATE_NAMES and (r.get("SECTOR") or "") in ("1", "2"):
            by_state[st].append(r)
    items = {}
    for st, group in by_state.items():
        group.sort(key=lambda r: r.get("INSTNM") or "")
        top = "".join(f"<tr><td>{html.escape((r.get('INSTNM') or '').title())}</td>"
                      f"<td>{'Public' if r.get('SECTOR') == '1' else 'Private non-profit'}</td></tr>"
                      for r in group[:12])
        items[st] = dict(
            n=len(group), rated=len(group), avg=0.0, site="https://colleges.tekify.xyz",
            lede=f"{len(group)} four-year colleges and universities in {{state}} (public and private "
                 f"non-profit). Below are the institutions in the directory.",
            body="<h2>Colleges in {state}</h2><table><tr><th>Institution</th><th>Sector</th></tr>"
                 + top + "</table>"
                 "<p>See each college's acceptance rate, tuition, average net price by income band and "
                 'graduation rate: <a href="{site}/state/{st}/">{state} college directory</a>.</p>'
                 '<h2>What to compare</h2><p>Sticker price tells you little — compare average net price '
                 "after aid and graduation rates before deciding.</p>")
    write_pages("colleges", "Colleges by state",
                "Colleges and universities in {state}",
                "Colleges in {state}",
                "Four-year colleges in {state}: {n} institutions listed with admissions, tuition, net price and graduation data.",
                "Data: NCES/IPEDS (public domain). Full directory: "
                '<a href="https://colleges.tekify.xyz">US Colleges</a> · '
                '<a href="https://tekify.xyz">tekify.xyz</a>', items)


def main() -> None:
    dialysis_pages()
    college_pages()


if __name__ == "__main__":
    main()
