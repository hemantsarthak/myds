#!/usr/bin/env python3
"""Build airport.tekify.xyz — an airport code directory (IATA / ICAO).

Input : ../../.cache/{airports,runways,countries,regions}.csv  (OurAirports, public domain)
Output: site/  (~10k static pages)

Pages
  /airport/<CODE>/   one page per airport (IATA preferred), with runways + nearby airports
  /country/<ISO2>/   one page per country (240)
  /search/           full local search index
  /                  search, stats, popular airports, country grid
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

SITE = "https://airportcodes.tekify.xyz"
BRAND = "Airport Codes"
CACHE = ROOT / ".cache"

SELECTED_TYPES = {"large_airport", "medium_airport", "small_airport", "heliport", "seaplane_base"}


def load():
    airports = list(csv.DictReader((CACHE / "airports.csv").open(encoding="utf-8")))
    runways = list(csv.DictReader((CACHE / "runways.csv").open(encoding="utf-8")))
    countries = {r["code"]: r["name"] for r in
                 csv.DictReader((CACHE / "countries.csv").open(encoding="utf-8"))}
    regions = {r["code"]: r["name"] for r in
               csv.DictReader((CACHE / "regions.csv").open(encoding="utf-8"))}
    by_ident = collections.defaultdict(list)
    for rw in runways:
        by_ident[rw["airport_ident"]].append(rw)

    def fnum(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    out = []
    for r in airports:
        if r["type"] not in SELECTED_TYPES:
            continue
        iata = (r["iata_code"] or "").strip().upper()
        icao = (r["icao_code"] or "").strip().upper()
        ident = (r["ident"] or "").strip().upper()
        if not (iata or icao or ident):
            continue
        if not (iata or r["type"] in ("large_airport", "medium_airport") or r["scheduled_service"] == "yes"):
            continue
        out.append({
            "ident": ident, "iata": iata, "icao": icao,
            "name": (r["name"] or "").strip(),
            "type": r["type"],
            "lat": fnum(r["latitude_deg"]), "lon": fnum(r["longitude_deg"]),
            "elev": r["elevation_ft"].strip(),
            "country": (r["iso_country"] or "").strip().upper(),
            "region": (r["iso_region"] or "").strip().upper(),
            "city": (r["municipality"] or "").strip(),
            "scheduled": r["scheduled_service"] == "yes",
            "home_link": (r["home_link"] or "").strip(),
            "wiki": (r["wikipedia_link"] or "").strip(),
            "runways": [rw for rw in by_ident.get(ident, []) if rw.get("closed") != "1"],
        })
    # codes: IATA preferred, else ICAO, else ident; ensure uniqueness
    used = set()
    reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
                "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
                "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}  # Windows device names break the build
    for a in out:
        code = a["iata"] or a["icao"] or a["ident"]
        if code in used or code in reserved:
            alt = f'{code}-{a["ident"] or a["icao"]}'
            while alt in used or alt in reserved:
                alt += "X"
            code = alt
        used.add(code)
        a["code"] = code
    return out, countries, regions


def distance_km(a, b) -> float:
    if None in (a["lat"], a["lon"], b["lat"], b["lon"]):
        return 1e9
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def runway_rows(a) -> str:
    rows = []
    for rw in sorted(a["runways"], key=lambda r: -(int(r["length_ft"]) if r["length_ft"].isdigit() else 0))[:6]:
        length = rw["length_ft"].strip()
        length_m = f"{int(int(length) * 0.3048):,} m" if length.isdigit() else "—"
        rows.append([esc(length + " ft" if length else "—"), esc(length_m),
                     esc(rw["surface"].strip() or "—"),
                     "Yes" if rw["lighted"] == "1" else "No",
                     esc(rw["le_ident"].strip() or "—")])
    if not rows:
        return ""
    return f"<h2>Runways</h2>{table(['Length', 'Length (m)', 'Surface', 'Lighted', 'Designator'], rows)}"


def build() -> Site:
    airports, countries, regions = load()
    by_country = collections.defaultdict(list)
    for a in airports:
        by_country[a["country"]].append(a)
    # spatial index so nearby lookups stay fast (1 degree buckets)
    grid = collections.defaultdict(list)
    for a in airports:
        if a["lat"] is not None and a["lon"] is not None:
            grid[(int(a["lat"]), int(a["lon"]))].append(a)

    def nearby(a, limit=8):
        if a["lat"] is None or a["lon"] is None:
            return []
        res = []
        for dlat in (-2, -1, 0, 1, 2):
            for dlon in (-2, -1, 0, 1, 2):
                for b in grid.get((int(a["lat"]) + dlat, int(a["lon"]) + dlon), ()):
                    if b is a:
                        continue
                    d = distance_km(a, b)
                    if d <= 300:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    s = Site("airport", BRAND, "airportcodes.tekify.xyz",
             "IATA and ICAO airport codes with runways, location and nearby airports.",
             "Airport codes directory: search any IATA or ICAO airport code to get the airport name, "
             "city, country, coordinates, elevation, runways and nearby airports.",
             nav=[("Search", "/search/"), ("Countries", "/#countries"), ("About", "/about/")],
             source_note="Data: OurAirports open dataset (public domain). Runway and location data are "
                         "updated regularly; always confirm operational details with the airport or operator.")

    top = sorted([a for a in airports if a["iata"]],
                 key=lambda a: (a["type"] != "large_airport", -len(a["runways"]), a["name"]))[:48]
    country_cards = cards([(f"/country/{c}/", esc(countries.get(c, c)), human(len(v)))
                           for c, v in sorted(by_country.items(), key=lambda kv: (-len(kv[1]), kv[0]))])
    home = f"""
<h1>Airport codes, runways and locations</h1>
<p class="lede">Search {human(len(airports))} airports by IATA or ICAO code, city, name or country.
<span class="stat">{human(sum(1 for a in airports if a['iata']))} IATA codes</span>
<span class="stat">{human(sum(1 for a in airports if a['icao']))} ICAO codes</span>
<span class="stat">{len(by_country)} countries</span></p>
<input type="search" id="q" placeholder="LHR, JFK, Heathrow, Tokyo…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2>Major airports</h2>
{cards([(f"/airport/{a['code']}/", f"{esc(a['code'])} — {esc(a['name'])}",
        esc(a["city"] or countries.get(a["country"], ""))) for a in top])}
<h2 id="countries">Browse by country</h2>
{country_cards}
<h2>IATA vs ICAO codes</h2>
<p><strong>IATA codes</strong> are the three-letter codes passengers see on tickets and baggage tags
(LHR, JFK, HND). <strong>ICAO codes</strong> are the four-letter codes used by air traffic control
and flight planning (EGLL, KJFK, RJTT). Many airports have both; smaller airfields and heliports
often only have an ICAO or local code. This directory lists both, plus runway and location data.</p>
"""
    s.add("/", "Airport Codes — Search IATA & ICAO Codes Worldwide",
          "Search airport codes worldwide: IATA and ICAO codes with airport name, city, country, "
          "coordinates, runways and nearby airports.", home)

    s.add("/search/", "Search Airport Codes — IATA, ICAO, City or Country",
          "Search the airport code database by IATA code, ICAO code, airport name, city or country.",
          """<h1>Search airport codes</h1>
<p class="lede">Type any code, airport name, city or country. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="LHR, EGLL, Heathrow, Tokyo…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- country pages
    for cc, group in sorted(by_country.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        cname = countries.get(cc, cc)
        group = sorted(group, key=lambda a: (a["type"] != "large_airport", a["name"]))
        by_region = collections.defaultdict(list)
        for a in group:
            by_region[regions.get(a["region"], a["region"] or "Other")].append(a)
        region_blocks = ""
        for rname, agroup in sorted(by_region.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:60]:
            links = " · ".join(
                f'<a href="/airport/{a["code"]}/">{esc(a["code"])}</a> {esc(a["name"])}'
                for a in agroup[:50])
            region_blocks += f"<h3>{esc(rname)}</h3><p>{links}</p>\n"
        body = f"""
<h1>Airports in {esc(cname)}</h1>
<p class="lede">{human(len(group))} airports, heliports and airfields in {esc(cname)}
({len(by_region)} regions). Every entry links to codes, coordinates, elevation and runways.</p>
{region_blocks}
<h2>Largest airports in {esc(cname)}</h2>
{cards([(f"/airport/{a['code']}/", f"{esc(a['code'])} — {esc(a['name'])}", esc(a['city'])) for a in group[:24]])}
{related([("/#countries", "All countries")])}
"""
        s.add(f"/country/{cc}/", f"Airports in {cname} — Airport Codes",
              f"Airport codes and locations in {cname}: {human(len(group))} airports with IATA/ICAO codes, "
              f"cities, coordinates and runways.",
              body, crumbs=[("Countries", "/#countries"), (cname, None)])

    # ---- airport pages
    for a in airports:
        cname = countries.get(a["country"], a["country"])
        rname = regions.get(a["region"], a["region"] or "")
        rows = [["IATA code", f"<strong>{esc(a['iata'])}</strong>" if a["iata"] else "—"],
                ["ICAO code", f"<strong>{esc(a['icao'])}</strong>" if a["icao"] else "—"],
                ["Airport name", esc(a["name"])],
                ["Type", esc(a["type"].replace("_", " "))],
                ["City / municipality", esc(a["city"] or "—")],
                ["Country", f'<a href="/country/{a["country"]}/">{esc(cname)}</a>'],
                ["Region", esc(rname or "—")],
                ["Coordinates", f'{a["lat"]}, {a["lon"]}' if a["lat"] is not None else "—"],
                ["Elevation", esc((a["elev"] + " ft") if a["elev"] else "—")],
                ["Scheduled service", "Yes" if a["scheduled"] else "No"]]
        links = []
        if a["home_link"]:
            links.append(f'<a href="{esc(a["home_link"])}" rel="nofollow noopener" target="_blank">Official website</a>')
        if a["wiki"]:
            links.append(f'<a href="{esc(a["wiki"])}" rel="nofollow noopener" target="_blank">Wikipedia</a>')
        near = nearby(a)
        near_html = cards([(f"/airport/{b['code']}/", f"{esc(b['code'])} — {esc(b['name'])}",
                            f"{d:,.0f} km · {esc(b['city'])}") for d, b in near])
        codes = " and ".join(x for x in [
            (f"IATA code <strong>{esc(a['iata'])}</strong>" if a["iata"] else ""),
            (f"ICAO code <strong>{esc(a['icao'])}</strong>" if a["icao"] else "")] if x) or "no published code"
        body = f"""
<h1>{esc(a["name"])} ({esc(a["code"])})</h1>
<p class="lede">{esc(a["name"])} is a {esc(a["type"].replace("_", " "))}
{'in ' + esc(a["city"]) + ', ' if a["city"] else 'in '}{esc(cname)}. It has {codes}.</p>
{table(["Field", "Value"], rows)}
{runway_rows(a)}
<h2>Location</h2>
<p>{esc(a["name"])} sits at latitude {a["lat"]}, longitude {a["lon"]}
{'at an elevation of ' + esc(a["elev"]) + ' ft' if a["elev"] else ''}
{f'in {esc(rname)}' if rname else ''}, {esc(cname)}. The coordinates above can be pasted directly
into a map service.</p>
<h2>Nearby airports</h2>
{near_html or "<p>No other indexed airports within 300 km.</p>"}
{related([(f'/country/{a["country"]}/', f'All airports in {cname}'), ("/search/", "Search all airport codes")])}
{('<p>' + " · ".join(links) + '</p>') if links else ''}
{faq([
    (f'What is the airport code for {a["name"]}?',
     f'{esc(a["name"])} uses ' + codes + '.'),
    (f'Where is {a["name"]}?',
     f'{esc(a["name"])} is located in {esc(a["city"] or "unknown city")}, {esc(cname)}, at '
     f'{a["lat"]}, {a["lon"]}.'),
    ('What is the difference between IATA and ICAO codes?',
     'IATA codes are the three-letter passenger-facing codes printed on tickets; ICAO codes are the '
     'four-letter codes used for flight planning and air traffic control.'),
])}
"""
        s.add(f'/airport/{a["code"]}/', f'{a["code"]} — {a["name"]}, {a["city"] or cname}',
              f'{a["name"]} ({a["code"]}) in {a["city"] or cname}, {cname}: '
              f'IATA {a["iata"] or "n/a"}, ICAO {a["icao"] or "n/a"}, coordinates, elevation, runways '
              f'and nearby airports.',
              body, crumbs=[("Countries", "/#countries"), (cname, f'/country/{a["country"]}/'),
                            (f'{a["code"]} — {a["name"]}', None)])

    # ---- search index + js
    s.add_file("/data/airports.json", json.dumps(
        [[a["code"], a["iata"], a["icao"], a["name"], a["city"], countries.get(a["country"], a["country"])]
         for a in airports], separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)

    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(airports))} airports, heliports and airfields from the "
                    f"OurAirports public-domain dataset ({len(by_country)} countries). The dataset is "
                    f"maintained by a volunteer community from official aviation publications and is "
                    f"updated regularly. Runway data is included where published.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/airports.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' airports indexed.';});
  }
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(a){return (a[0]+' '+a[1]+' '+a[2]+' '+a[3]+' '+a[4]+' '+a[5]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML = out.length? '<div class="grid">'+out.slice(0,40).map(function(a){
      return '<a href="/airport/'+encodeURIComponent(a[0])+'/">'+esc(a[1]||a[2]||a[0])+' — '+esc(a[3])+' <span class="mut">'+esc(a[4]||a[5])+'</span></a>';
    }).join('')+'</div>' : '<p class="mut">No airport found for that search.</p>';
  }
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
