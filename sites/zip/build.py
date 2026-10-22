#!/usr/bin/env python3
"""Build zipcodes.tekify.xyz — a US ZIP code directory.

Input : ../../.cache/geonames-us/{US.txt,cities500.txt}  (GeoNames, CC BY 4.0)
Output: site/  (~17.8k static pages)

Pages
  /zip/<ZIP>/          one page per ZIP code (selected by city population)
  /state/<ST>/         one page per state / territory
  /city/<city>-<ST>/   top ~700 cities
  /search/             local search over every page
  /                    search + stats + browse
"""
import collections
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.sitegen import Site, table, cards, related, faq, esc, slug, human, notice  # noqa: E402
from engine.guides import add_guides  # noqa: E402

DATA = ROOT / ".cache" / "geonames-us"
ZIP_LIMIT = 17000
CITY_LIMIT = 700

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
    "PR": "Puerto Rico", "VI": "U.S. Virgin Islands", "GU": "Guam", "AS": "American Samoa",
    "MP": "Northern Mariana Islands", "FM": "Micronesia", "MH": "Marshall Islands", "PW": "Palau",
}


def titlecase(s: str) -> str:
    s = (s or "").strip().lower()
    small = {"and", "of", "the", "in", "on", "for", "de", "la", "del"}
    return " ".join(w if (w in small and i) else (w[:1].upper() + w[1:]) for i, w in enumerate(s.split()))


def load():
    cities = collections.defaultdict(int)      # (state, city lower) -> population
    tz = {}                                    # (state, city lower) -> timezone
    with (DATA / "cities500.txt").open(encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 15 or p[8] != "US":
                continue
            pop = int(p[14] or 0)
            key = (p[10].upper(), p[1].lower())
            if pop > cities.get(key, 0):
                cities[key] = pop
            if p[17] if len(p) > 17 else None:
                tz.setdefault(key, p[17])
    rows = []
    with (DATA / "US.txt").open(encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 11:
                continue
            zipc, place, state = p[1], p[2], p[4].upper()
            try:
                lat, lon = float(p[9]), float(p[10])
            except ValueError:
                continue
            key = (state, place.lower())
            rows.append({
                "zip": zipc, "place": titlecase(place), "state": state,
                "state_name": STATE_NAMES.get(state, state),
                "county": titlecase(p[5]), "lat": lat, "lon": lon,
                "pop": cities.get(key, 0), "tz": tz.get(key, ""),
                "accuracy": p[11] if len(p) > 11 else "",
            })
    return rows


def distance_km(a, b) -> float:
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def build() -> Site:
    rows = load()
    # rank: biggest city population first, then lower ZIP (usually older/central)
    ranked = sorted(rows, key=lambda r: (-r["pop"], r["zip"]))
    selected = ranked[:ZIP_LIMIT]
    sel_by_city = collections.defaultdict(list)
    for r in selected:
        sel_by_city[(r["state"], r["place"])].append(r)
    all_by_city = collections.defaultdict(list)
    for r in rows:
        all_by_city[(r["state"], r["place"])].append(r)
    all_by_state = collections.defaultdict(list)
    for r in selected:
        all_by_state[r["state"]].append(r)
    city_rank = {k: i for i, (k, v) in enumerate(
        sorted(all_by_city.items(), key=lambda kv: (-max(x["pop"] for x in kv[1]), -len(kv[1]), kv[0])))}
    city_page_set = set(list(city_rank)[:CITY_LIMIT])
    grid = collections.defaultdict(list)
    for r in selected:
        grid[(int(r["lat"]), int(r["lon"]))].append(r)
    sel_codes = {r["zip"] for r in selected}

    def nearby(r, limit=8):
        res = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for b in grid.get((int(r["lat"]) + dlat, int(r["lon"]) + dlon), ()):
                    if b["zip"] == r["zip"]:
                        continue
                    d = distance_km(r, b)
                    if d <= 80:
                        res.append((d, b))
        res.sort(key=lambda x: (x[1]["state"] != r["state"], x[0]))
        return res[:limit]

    s = Site("zip", "US ZIP Codes", "zipcodes.tekify.xyz",
             "US ZIP code directory: city, county, state, time zone and nearby ZIPs.",
             "Look up any US ZIP code: the city and state it belongs to, county, coordinates, "
             "population, time zone and the neighbouring ZIP codes around it.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("About", "/about/"), ("Guides", "/guides/")],
             source_note="Data: GeoNames postal and place datasets (CC BY 4.0), derived from USPS and "
                         "US Census Bureau data. ZIP boundaries change; verify with USPS for mail.")

    top_cities = sorted(all_by_city.items(), key=lambda kv: city_rank[kv[0]])[:60]
    home = f"""
<h1>US ZIP code lookup</h1>
<p class="lede">Find the city, county, state and time zone of any US ZIP code — plus the ZIPs
around it. <span class="stat">{human(len(rows))} ZIP codes</span>
<span class="stat">{human(len(all_by_state))} states &amp; territories</span>
<span class="stat">{human(len(all_by_city))} cities</span></p>
<input type="search" id="q" placeholder="90210, Austin, Miami…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2>Popular cities</h2>
{cards([(f"/city/{slug(c)}-{st}/", esc(c), human(len(all_by_city[(st, c)]))) for (st, c), _ in top_cities])}
<h2 id="states">Browse by state</h2>
{cards([(f"/state/{st}/", esc(STATE_NAMES.get(st, st)), human(len(v)))
        for st, v in sorted(all_by_state.items(), key=lambda kv: (-len(kv[1]), kv[0]))])}
<h2>What a ZIP code contains</h2>
<p>A ZIP code is a five-digit postal code that groups addresses for mail delivery. It is assigned
to a delivery area rather than a legal boundary, so a single ZIP can cross city or county lines.
This directory maps each ZIP to its primary place name, county, state and time zone from public
GeoNames data, and lists the ZIPs immediately around it.</p>
"""
    s.add("/", "US ZIP Code Lookup — City, County, State &amp; Time Zone",
          "Look up any US ZIP code: city, county, state, coordinates, population and time zone, "
          "plus the ZIP codes nearby.", home)

    s.add("/search/", "Search US ZIP Codes — City, County or State",
          "Search all US ZIP codes by code, city, county or state abbreviation.",
          """<h1>Search ZIP codes</h1>
<p class="lede">Type a ZIP, city, county or state. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="90210, Brooklyn, Travis County, TX…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- state pages
    for st, group in sorted(all_by_state.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        sname = STATE_NAMES.get(st, st)
        cities_here = collections.Counter((r["state"], r["place"]) for r in group)
        top = sorted(cities_here.items(), key=lambda kv: (-kv[1], kv[0]))[:48]
        body = f"""
<h1>ZIP codes in {esc(sname)}</h1>
<p class="lede">{human(len(group))} ZIP codes across {human(len(cities_here))} cities in {esc(sname)}.
Pick a city or search a specific code.</p>
<h2>Cities in {esc(sname)}</h2>
{cards([(f"/city/{slug(c)}-{st}/", esc(c), human(n)) for (_, c), n in top if (st, c) in city_page_set])}
<h2>ZIP codes in {esc(sname)} — notes</h2>
<p>ZIP codes in {esc(sname)} begin with {"" if not group else "prefixes such as " + ", ".join(sorted({r["zip"][:2] for r in group})[:6])}.
Each code is tied to a primary post office or delivery area, so a single ZIP may cover more than one
census place. Use the search box above for any specific code.</p>
{related([("/", "All states"), ("/search/", "Search all ZIP codes")])}
"""
        s.add(f"/state/{st}/", f"ZIP Codes in {sname} — Full List",
              f"All {human(len(group))} ZIP codes in {sname} by city, with county, population and "
              f"time zone details for each code.", body,
              crumbs=[("States", "/#states"), (sname, None)])

    # ---- city pages
    for (st, city), group in sorted(all_by_city.items(), key=lambda kv: city_rank[kv[0]])[:CITY_LIMIT]:
        sname = STATE_NAMES.get(st, st)
        group = sorted(group, key=lambda r: r["zip"])
        rows_html = table(["ZIP", "County", "Population", "Time zone"],
                          [[f'<a href="/zip/{r["zip"]}/">{r["zip"]}</a>' if r["zip"] in sel_codes else r["zip"],
                            esc(r["county"]), human(r["pop"]) if r["pop"] else "—", esc(r["tz"])]
                           for r in group[:120]])
        body = f"""
<h1>ZIP codes in {esc(city)}, {esc(sname)}</h1>
<p class="lede">{esc(city)} has {human(len(group))} ZIP codes in this directory.
Each ZIP is listed with its county, population and time zone.</p>
{rows_html}
<h2>About {esc(city)} ZIP codes</h2>
<p>ZIP codes in {esc(city)} are part of the USPS delivery network for {esc(sname)}. The codes above
are ordered numerically; each links to a page with coordinates, nearby ZIPs and more detail.
{('Population shown is the estimated population of the city: ' + human(max(r["pop"] for r in group)) + '.') if max(r["pop"] for r in group) else ''}</p>
{related([(f"/state/{st}/", f"All ZIP codes in {sname}"), ("/search/", "Search all ZIP codes")])}
"""
        s.add(f"/city/{slug(city)}-{st}/", f"ZIP Codes in {city}, {st} — Full List",
              f"ZIP codes for {city}, {st}: {human(len(group))} codes with county, population and "
              f"time zone. Find the ZIP for any {city} address.", body,
              crumbs=[("States", "/#states"), (sname, f"/state/{st}/"), (city, None)])

    # ---- zip pages
    for r in selected:
        city_has_page = (r["state"], r["place"]) in city_page_set
        near = nearby(r)
        near_cards = cards([(f"/zip/{b['zip']}/", b["zip"], f"{d:,.1f} km · {esc(b['place'])}")
                            for d, b in near])
        same_city = [x for x in sel_by_city[(r["state"], r["place"])] if x["zip"] != r["zip"]][:12]
        rows_html = table(["Field", "Value"], [
            ["ZIP code", f'<strong>{esc(r["zip"])}</strong>'],
            ["City / place", esc(r["place"])],
            ["State", f'<a href="/state/{r["state"]}/">{esc(r["state_name"])}</a>'],
            ["County", esc(r["county"] or "—")],
            ["Coordinates", f'{r["lat"]}, {r["lon"]}'],
            ["Time zone", esc(r["tz"] or "—")],
            ["City population", human(r["pop"]) if r["pop"] else "—"],
            ["ZIP type", "PO box / unique" if r["accuracy"] in ("3", "4", "5", "6") else "Standard area"],
        ])
        body = f"""
<h1>ZIP Code {esc(r["zip"])} — {esc(r["place"])}, {esc(r["state_name"])}</h1>
<p class="lede">ZIP code {esc(r["zip"])} belongs to {esc(r["place"])}, {esc(r["state_name"])}
{('(county: ' + esc(r["county"]) + ')') if r["county"] else ''}. It sits at latitude {r["lat"]},
longitude {r["lon"]}{(' in the ' + esc(r["tz"]) + ' time zone') if r["tz"] else ''}.</p>
{rows_html}
<h2>What is ZIP code {esc(r["zip"])}?</h2>
<p>{esc(r["zip"])} is a five-digit ZIP code used by the United States Postal Service for
{esc(r["place"])}, {esc(r["state_name"])}. It is one of {human(len(all_by_city[(r["state"], r["place"])]))}
ZIP codes associated with {esc(r["place"])} in this dataset. The delivery area is served from the
local post office network, so the ZIP can cover more than one neighbourhood or even
cross a city line.</p>
{f'<h2>ZIP codes in the same city</h2>{cards([(f"/zip/{x["zip"]}/", x["zip"], esc(x["county"])) for x in same_city])}' if same_city else ''}
<h2>Nearby ZIP codes</h2>
{near_cards or "<p>No neighbouring ZIP codes indexed.</p>"}
{related([(f'/city/{slug(r["place"])}-{r["state"]}/', f"All ZIP codes in {r['place']}") if city_has_page else ("/search/", "Search ZIP codes"),
          (f'/state/{r["state"]}/', f"All ZIP codes in {r['state_name']}"), ("/search/", "Search all ZIP codes")])}
{faq([
    (f'What city is ZIP code {r["zip"]} in?',
     f'ZIP code {esc(r["zip"])} is in {esc(r["place"])}, {esc(r["state_name"])}.'),
    (f'What county is {r["zip"]} in?',
     f'{esc(r["zip"])} belongs to {esc(r["county"] or "an unlisted county")} in {esc(r["state_name"])}.'),
    (f'What time zone is ZIP code {r["zip"]} in?',
     f'{esc(r["zip"])} is in the {esc(r["tz"] or "local US")} time zone.'),
])}
"""
        s.add(f'/zip/{r["zip"]}/', f'ZIP Code {r["zip"]} — {r["place"]}, {r["state"]}, {r["county"]} County',
              f'ZIP code {r["zip"]} is in {r["place"]}, {r["state_name"]} ({r["county"] or "county n/a"}). '
              f'Coordinates, time zone, city population and nearby ZIP codes.',
              body, crumbs=[("States", "/#states"), (r["state_name"], f'/state/{r["state"]}/'),
                            (r["zip"], None)])

    s.add_file("/data/zips.json", json.dumps(
        [[r["zip"], r["place"], r["state"], r["county"], r["pop"], r["tz"]] for r in selected],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(rows))} ZIP codes from the GeoNames postal dataset "
                    f"and {human(len(all_by_city))} US place names from GeoNames cities500, both "
                    f"CC BY 4.0. Population figures are city estimates. ZIP delivery areas are not "
                    f"legal boundaries and change over time.</p>")
    add_guides(s)
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/zips.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' ZIP codes indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(z){return (z[0]+' '+z[1]+' '+z[2]+' '+z[3]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML=out.length?'<div class="grid">'+out.slice(0,40).map(function(z){
      return '<a href="/zip/'+z[0]+'/">'+z[0]+' — '+esc(z[1])+' <span class="mut">'+esc(z[2])+'</span></a>';
    }).join('')+'</div>':'<p class="mut">No ZIP found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
