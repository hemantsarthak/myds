#!/usr/bin/env python3
"""Build places.tekify.xyz — US place / county / population directory.

Answers the practical questions behind US place names: which county is this city in, how many
people live there, where is it, and what places are nearby.

Input : .cache/{sub-est2023.csv, gaz/2023_Gaz_place_national.txt, gaz/*counties*.txt,
               geonames-us/cities500.txt}
Output: site/  (~19.2k pages)

Pages
  /place/<slug>-<ST>/    city / town / village / CDP page (top 16k by population)
  /county/<ST>-<slug>/   county page (3,144)
  /state/<ST>/           state page (51)
  /search/  /           search + browse
"""
import collections
import csv
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.sitegen import Site, table, cards, related, faq, esc, slug, human, notice  # noqa: E402

CACHE = ROOT / ".cache"
PLACE_LIMIT = 16000
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
    "MP": "Northern Mariana Islands",
}
PLACE_TYPES = ("city", "town", "village", "borough", "CDP", "municipality", "urban county",
               "consolidated government", "unified government", "balance", "corporation")


def clean(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def split_name(full: str):
    """'Abbeville city' -> ('Abbeville', 'city'); 'Forked Deer CDP' -> ('Forked Deer', 'CDP')."""
    full = clean(full)
    for suf in sorted(PLACE_TYPES, key=len, reverse=True):
        if full.endswith(" " + suf):
            return full[: -len(suf) - 1], suf
    return full, "place"


def titlecase(s: str) -> str:
    s = clean(s).lower()
    small = {"and", "of", "the", "in", "on", "for", "de", "la", "del", "st.", "mt."}
    return " ".join(w if (w in small and i) else (w[:1].upper() + w[1:])
                    for i, w in enumerate(s.split()))


def load():
    rows = list(csv.DictReader((CACHE / "sub-est2023.csv").open(encoding="latin-1")))

    states = {}
    counties = {}
    places = {}
    parts = collections.defaultdict(list)   # (state, place) -> [(county_fips, pop)]
    for r in rows:
        lvl = r["SUMLEV"]
        st, co, pl = r["STATE"], r["COUNTY"], r["PLACE"]
        pop = int(r["POPESTIMATE2023"] or 0)
        if lvl == "040":
            states[st] = {"name": clean(r["NAME"]), "pop": pop}
        elif lvl == "050":
            counties[(st, co)] = {"name": clean(r["NAME"]), "state": st, "pop": pop, "fips": st + co}
        elif lvl == "162":
            places[(st, pl)] = {"name": clean(r["NAME"]), "state": st, "pop": pop}
        elif lvl == "157":
            parts[(st, pl)].append((co, pop))

    # Gazetteer: coordinates, land area, USPS state code keyed by (state fips, place fips)
    gaz = {}
    fips_to_usps = {}
    gaz_file = next((CACHE / "gaz").glob("*place_national.txt"))
    with gaz_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]   # fixed-width header has padding
        for r in reader:
            geoid = r["GEOID"].strip()
            if len(geoid) != 7:
                continue
            st, pl = geoid[:2], geoid[2:]
            usps = r["USPS"].strip()
            fips_to_usps[st] = usps
            gaz[(st, pl)] = {
                "lat": float(r["INTPTLAT"]), "lon": float(r["INTPTLONG"]),
                "area": float(r["ALAND_SQMI"] or 0), "usps": usps,
            }

    # time zones from GeoNames cities500 (key: (USPS, lowercase base name))
    tz = {}
    c500 = CACHE / "geonames-us" / "cities500.txt"
    if c500.exists():
        with c500.open(encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) < 18 or p[8] != "US":
                    continue
                tz.setdefault((p[10].upper(), p[1].lower()), p[17])

    out = []
    for (st, pl), p in places.items():
        g = gaz.get((st, pl))
        if not g:
            continue
        name, kind = split_name(p["name"])
        usps = g["usps"] or fips_to_usps.get(st, "")
        if not usps:
            continue
        county_list = sorted(parts.get((st, pl), []), key=lambda x: -x[1])
        primary = county_list[0][0] if county_list else None
        cname = counties[(st, primary)]["name"] if primary and (st, primary) in counties else ""
        out.append({
            "key": f"{st}{pl}", "name": name, "kind": kind, "state": st, "usps": usps,
            "state_name": STATE_NAMES.get(usps, states.get(st, {}).get("name", usps)),
            "pop": p["pop"], "lat": g["lat"], "lon": g["lon"], "area": g["area"],
            "county_fips": primary, "county": cname,
            "tz": tz.get((usps, name.lower()), ""),
            "counties": [(counties[(st, c)]["name"], c) for c, _ in county_list
                         if (st, c) in counties],
        })
    return states, counties, out, fips_to_usps


def distance_km(a, b) -> float:
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def build() -> Site:
    states, counties, all_places, fips_to_usps = load()
    places = sorted(all_places, key=lambda p: (-p["pop"], p["name"]))[:PLACE_LIMIT]
    # assign unique slugs
    used = collections.Counter()
    for p in places:
        base = f'{slug(p["name"])}-{p["usps"].lower()}'
        used[base] += 1
        p["url"] = f"/place/{base}/" if used[base] == 1 else f'/place/{base}-{used[base]}/'

    name_counts = collections.Counter((p["name"], p["usps"]) for p in places)

    county_places = collections.defaultdict(list)
    for p in places:
        if p["county_fips"]:
            county_places[(p["state"], p["county_fips"])].append(p)
    state_places = collections.defaultdict(list)
    for p in places:
        state_places[p["usps"]].append(p)
    grid = collections.defaultdict(list)
    for p in places:
        grid[(int(p["lat"]), int(p["lon"]))].append(p)

    def nearby(p, limit=8):
        res = []
        for dlat in (-2, -1, 0, 1, 2):
            for dlon in (-2, -1, 0, 1, 2):
                for b in grid.get((int(p["lat"]) + dlat, int(p["lon"]) + dlon), ()):
                    if b["key"] == p["key"]:
                        continue
                    d = distance_km(p, b)
                    if d <= 60:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    county_url = {(st, co): f"/county/{fips_to_usps.get(st, st).lower()}-{slug(c['name'])}/"
                  for (st, co), c in counties.items()}
    state_url = {usps: f"/state/{usps.lower()}/" for usps in {p["usps"] for p in places}}

    s = Site("places", "US Places", "places.tekify.xyz",
             "US cities towns and counties: population, county and location.",
             "Look up any US city, town or county: which county it belongs to, its 2023 population "
             "estimate, land area, coordinates, time zone and the places around it.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("About", "/about/")],
             source_note="Population: US Census Bureau Vintage 2023 estimates. Boundaries and "
                         "coordinates: US Census Bureau 2023 Gazetteer. Time zones: GeoNames (CC BY).")

    states_sorted = sorted({p["usps"] for p in places},
                           key=lambda u: -sum(x["pop"] for x in state_places[u]))
    counties_sorted = sorted(counties.items(), key=lambda kv: -kv[1]["pop"])[:48]
    home = f"""
<h1>US places, counties and population</h1>
<p class="lede">Find any US city, town or county: the county it belongs to, its 2023 population
estimate, coordinates and time zone.
<span class="stat">{human(len(places))} places</span>
<span class="stat">{human(len(counties))} counties</span>
<span class="stat">{len(states_sorted)} states</span></p>
<input type="search" id="q" placeholder="Austin, Brooklyn, Travis County…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2>Largest counties</h2>
{cards([(county_url[k], esc(v["name"]), human(v["pop"])) for k, v in counties_sorted])}
<h2 id="states">Browse by state</h2>
{cards([(state_url[u], esc(STATE_NAMES.get(u, u)), human(sum(x["pop"] for x in state_places[u]))) for u in states_sorted])}
<h2>Places and counties</h2>
<p>A US place is a named population centre — an incorporated city, town, village, borough, or a
Census-designated place. Every place sits inside one or more counties, and counties sit inside
states. This directory maps all three layers using the Census Bureau's official population
estimates (Vintage 2023) and gazetteer, so you can answer questions like “what county is
Springfield in?” or “how big is Frisco, Texas?” without guessing.</p>
{notice("Population figures are July 1, 2023 estimates. A place that spans counties appears under "
        "its primary county, with the others listed on its page.")}
"""
    s.add("/", "US Places & Counties — Population, County and Location",
          "Search 16,000 US cities, towns and Census places plus 3,144 counties: population "
          "estimates, county, coordinates, land area and time zone.", home)

    s.add("/search/", "Search US Places and Counties",
          "Search US cities, towns, Census-designated places and counties by name, state or county.",
          """<h1>Search US places</h1>
<p class="lede">Type a place name, county or state code. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Austin, Brooklyn, Travis County, TX…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- state pages
    for usps in states_sorted:
        sname = STATE_NAMES.get(usps, usps)
        group = sorted(state_places[usps], key=lambda p: -p["pop"])
        co_in = collections.Counter((p["state"], p["county_fips"]) for p in group if p["county_fips"])
        co_cards = cards([(county_url[k], esc(counties[k]["name"]), human(counties[k]["pop"]))
                          for k, _n in sorted(co_in.items(), key=lambda kv: -kv[1])[:40]])
        body = f"""
<h1>Places in {esc(sname)}</h1>
<p class="lede">{human(len(group))} indexed places and {human(len(co_in))} counties in
{esc(sname)}. Population estimates are for 2023.</p>
<h2>Largest places in {esc(sname)}</h2>
{cards([(p["url"], esc(p["name"]), f'{human(p["pop"])} · {esc(p["county"])}') for p in group[:60]])}
<h2>Counties in {esc(sname)}</h2>
{co_cards}
{related([("/#states", "All states"), ("/search/", "Search all places")])}
"""
        s.add(f"/state/{usps.lower()}/", f"Places in {sname} — Cities, Towns & Counties",
              f"Cities, towns and counties in {sname}: {human(len(group))} places with 2023 "
              f"population estimates, county assignment and county list.",
              body, crumbs=[("States", "/#states"), (sname, None)])

    # ---- county pages
    for (st, co), c in counties.items():
        usps = fips_to_usps.get(st, st)
        sname = STATE_NAMES.get(usps, usps)
        cname = c["name"]
        plist = sorted(county_places.get((st, co), []), key=lambda p: -p["pop"])
        body = f"""
<h1>{esc(cname)}, {esc(sname)}</h1>
<p class="lede">{esc(cname)} is a county in {esc(sname)} with an estimated population of
{human(c["pop"])} in 2023. {human(len(plist))} cities, towns and Census places in it are
indexed here.</p>
<h2>Largest places in {esc(cname)}</h2>
{cards([(p["url"], esc(p["name"]), human(p["pop"])) for p in plist[:40]]) or "<p>No indexed places.</p>"}
<h2>About {esc(cname)}</h2>
<p>{esc(cname)} is one of the counties of {esc(sname)}. County governments in {esc(sname)} handle
local services such as courts, property records and elections; cities and towns inside the county
run their own municipal services. Population figures come from the Census Bureau's Vintage 2023
estimates, which are updated annually.</p>
{related([(state_url.get(usps, "/#states"), f"All places in {sname}"), ("/search/", "Search places")])}
"""
        url = county_url[(st, co)]
        s.add(url, f"{cname}, {usps} — Population & Cities",
              f"{cname} county, {sname}: population {human(c['pop'])} (2023 estimate) and the cities, "
              f"towns and Census places inside it.", body,
              crumbs=[("States", "/#states"), (sname, state_url.get(usps)), (cname, None)])

    # ---- place pages
    for p in places:
        sname = p["state_name"]
        county = p["county"]
        county_link = county_url.get((p["state"], p["county_fips"])) if p["county_fips"] else None
        near = nearby(p)
        same_county = [x for x in county_places.get((p["state"], p["county_fips"]), [])
                       if x["key"] != p["key"]][:10]
        rows = table(["Field", "Value"], [
            ["Place name", f'<strong>{esc(p["name"])}</strong>'],
            ["Type", esc(p["kind"])],
            ["State", f'<a href="{state_url[p["usps"]]}">{esc(sname)} ({esc(p["usps"])})</a>'],
            ["County", f'<a href="{county_link}">{esc(county)}</a>' if county_link else (esc(county) or "—")],
            ["Population (2023 est.)", human(p["pop"])],
            ["Land area", f'{p["area"]:,.2f} sq mi ({p["area"] * 2.58999:,.2f} km²)'],
            ["Coordinates", f'{p["lat"]:.4f}, {p["lon"]:.4f}'],
            ["Time zone", esc(p["tz"] or "—")],
        ])
        others = ""
        if len(p["counties"]) > 1:
            others = ("<p class=\"mut\">This place also extends into " +
                      ", ".join(esc(n) for n, _c in p["counties"][1:]) + ".</p>")
        body = f"""
<h1>{esc(p["name"])}{(' (' + esc(p["kind"]) + ')') if name_counts[(p["name"], p["usps"])] > 1 else ''}, {esc(sname)}</h1>
<p class="lede">{esc(p["name"])} is a {esc(p["kind"])} in
{esc(county) + ', ' if county else ''}{esc(sname)}, with an estimated population of
{human(p["pop"])} in 2023. It sits at {p["lat"]:.4f}, {p["lon"]:.4f}
{('in the ' + esc(p["tz"]) + ' time zone') if p["tz"] else ''}.</p>
{rows}
{others}
<h2>Where is {esc(p["name"])}?</h2>
<p>{esc(p["name"])} is located in {esc(sname)}{', in ' + esc(county) if county else ''}.
The coordinates above can be pasted directly into any map service. The nearest indexed places are
listed below, which is a useful check when two states share a place name.</p>
<h2>Nearby places</h2>
{cards([(b["url"], esc(b["name"]), f'{d:,.0f} km · {esc(b["usps"])}') for d, b in near]) or "<p>—</p>"}
{('<h2>Other places in ' + esc(county) + '</h2>' + cards([(x["url"], esc(x["name"]), human(x["pop"])) for x in same_county])) if same_county else ''}
{related([(state_url[p["usps"]], f"All places in {sname}"), ("/search/", "Search US places"),
          (county_link, county) if county_link else ("/", "Home")])}
{faq([
    (f'What county is {p["name"]}, {p["usps"]} in?',
     f'{esc(p["name"])} is in {esc(county)}, {esc(sname)}.'),
    (f'What is the population of {p["name"]}, {p["usps"]}?',
     f'The 2023 Census Bureau estimate is {human(p["pop"])}.'),
    (f'What time zone is {p["name"]} in?',
     f'{esc(p["name"])} is in the {esc(p["tz"] or "US local")} time zone.'),
])}
"""
        ptitle = (f'{p["name"]}, {p["usps"]} — Population, County & Location'
                  if name_counts[(p["name"], p["usps"])] == 1
                  else f'{p["name"]} ({p["kind"]}), {p["usps"]} — '
                       f'{p["county"] if p["county"] else p["url"].strip("/").split("/")[-1]}')
        s.add(p["url"], ptitle,
              f'{p["name"]}, {sname}: population {human(p["pop"])} (2023), '
              f'{county if county else "county n/a"}, coordinates, land area and nearby places.',
              body, crumbs=[("States", "/#states"), (sname, state_url[p["usps"]]),
                            (p["name"], None)])

    # ---- index + js
    s.add_file("/data/places.json", json.dumps(
        [[p["name"], p["usps"], p["county"], p["pop"], p["url"]] for p in places],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(places))} places and {human(len(counties))} counties. "
                    f"Population: US Census Bureau Vintage 2023 estimates (public domain). Location and "
                    f"area: 2023 Census Gazetteer. Time zones: GeoNames (CC BY 4.0). County assignment "
                    f"comes from the Census place-to-county relationship file; a place that crosses "
                    f"counties shows its primary county and lists the others.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/places.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' places indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(p){return (p[0]+' '+p[1]+' '+p[2]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML=out.length?'<div class="grid">'+out.slice(0,40).map(function(p){
      return '<a href="'+p[4]+'">'+esc(p[0])+' <span class="mut">'+esc(p[1])+' · '+esc(p[2])+'</span></a>';
    }).join('')+'</div>':'<p class="mut">No place found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
