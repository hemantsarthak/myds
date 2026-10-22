#!/usr/bin/env python3
"""Build areacodes.tekify.xyz — NANPA area codes + world country calling codes.

Answers the questions people actually search:
  "what area code is 201"        -> /area-code/201/
  "what area code is Hackensack" -> /city/nj-hackensack/
  "New Jersey area codes"        -> /state/nj/
  "what country is +44"          -> /country/gb/

Input (.cache, all openly licensed — see fetch_data.py for the exact sources):
  us-zip-codes.csv            41,711 US ZIPs with NANPA area codes  (zipcodes.pro, CC BY 4.0)
  ca-area-code-cities.csv     Canadian area codes by city            (ravisorg, GitHub)
  ca-area-code-geo.csv        Canadian area code centroids
  country-codes.csv           UN M49 country list with dial codes    (public domain / CC)
  geonames-us/cities500.txt   GeoNames city population + time zones  (CC BY 4.0)

Output: site/ (~7.5k pages), sitemap, robots, IndexNow key, ads + analytics via engine.

Pages
  /area-code/<code>/   one per NANP area code (~410, US + Canada + territories)
  /state/<st>/         US states / territories + Canadian provinces (~64)
  /city/<st>-<slug>/   ~6,800 cities with their area codes and ZIP codes
  /country/<iso2>/     ~249 countries and their international dialing codes
  /area-code/ /state/ /city/ /country-codes/   browse indexes
  /guides/             8 hand-written explainers (guides.json)
  /search/  /          search + home
"""
from __future__ import annotations

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
HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------- reference tables
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
PROVINCES = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
    "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
    "SK": "Saskatchewan", "YT": "Yukon",
}
PROVINCE_BY_NAME = {v.lower(): k for k, v in PROVINCES.items()}

# CLDR abbreviates two country names to two letters; use the readable form instead
NAME_FIX = {"GB": "United Kingdom", "US": "United States"}

# fallback time zone per state / province (used when a town is not in GeoNames)
STATE_TZ = {
    "CT": "America/New_York", "DE": "America/New_York", "DC": "America/New_York",
    "FL": "America/New_York", "GA": "America/New_York", "IN": "America/Indiana/Indianapolis",
    "KY": "America/New_York", "ME": "America/New_York", "MD": "America/New_York",
    "MA": "America/New_York", "MI": "America/Detroit", "NH": "America/New_York",
    "NJ": "America/New_York", "NY": "America/New_York", "NC": "America/New_York",
    "OH": "America/New_York", "PA": "America/New_York", "RI": "America/New_York",
    "SC": "America/New_York", "VT": "America/New_York", "VA": "America/New_York",
    "WV": "America/New_York",
    "AL": "America/Chicago", "AR": "America/Chicago", "IL": "America/Chicago",
    "IA": "America/Chicago", "KS": "America/Chicago", "LA": "America/Chicago",
    "MN": "America/Chicago", "MS": "America/Chicago", "MO": "America/Chicago",
    "NE": "America/Chicago", "ND": "America/Chicago", "OK": "America/Chicago",
    "SD": "America/Chicago", "TN": "America/Chicago", "TX": "America/Chicago",
    "WI": "America/Chicago",
    "AZ": "America/Phoenix", "CO": "America/Denver", "MT": "America/Denver",
    "NM": "America/Denver", "UT": "America/Denver", "WY": "America/Denver",
    "ID": "America/Boise", "NV": "America/Los_Angeles", "CA": "America/Los_Angeles",
    "OR": "America/Los_Angeles", "WA": "America/Los_Angeles",
    "AK": "America/Anchorage", "HI": "Pacific/Honolulu",
    "PR": "America/Puerto_Rico", "VI": "America/St_Thomas", "GU": "Pacific/Guam",
    "AS": "Pacific/Pago_Pago", "MP": "Pacific/Saipan",
    "AB": "America/Edmonton", "BC": "America/Vancouver", "MB": "America/Winnipeg",
    "NB": "America/Moncton", "NL": "America/St_Johns", "NS": "America/Halifax",
    "NT": "America/Yellowknife", "NU": "America/Iqaluit", "ON": "America/Toronto",
    "PE": "America/Halifax", "QC": "America/Toronto", "SK": "America/Regina",
    "YT": "America/Whitehorse",
}


def clean(s) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def region_name(code: str) -> str:
    return STATE_NAMES.get(code) or PROVINCES.get(code) or code


# filled in build(): every state / province that has an area code or a town page
REGIONS_ALL: set = set()

# filled in build(): (state, town) -> path, but only for towns that get a page
CITY_PATH: dict = {}
STATE_TOWNS: dict = {}


def town_link(st: str, city: str) -> str:
    p = CITY_PATH.get((st, city))
    return f'<a href="{p}">{esc(city)}</a>' if p else esc(city)


def fnum(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def haversine(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def tz_short(tz: str) -> str:
    """'America/New_York' -> 'Eastern'. Unknown stays as-is."""
    m = {"New_York": "Eastern", "Chicago": "Central", "Denver": "Mountain", "Los_Angeles": "Pacific",
         "Phoenix": "Mountain (no DST)", "Anchorage": "Alaska", "Honolulu": "Hawaii",
         "Edmonton": "Mountain", "Vancouver": "Pacific", "Winnipeg": "Central", "Toronto": "Eastern",
         "Halifax": "Atlantic", "St_Johns": "Newfoundland", "Regina": "Central (no DST)",
         "Moncton": "Atlantic", "Yellowknife": "Mountain", "Iqaluit": "Eastern",
         "Whitehorse": "Mountain", "Puerto_Rico": "Atlantic", "St_Thomas": "Atlantic",
         "Guam": "Chamorro", "Pago_Pago": "Samoa", "Saipan": "Chamorro",
         "Indiana/Indianapolis": "Eastern", "Detroit": "Eastern", "Boise": "Mountain"}
    city = tz.split("/")[-1]
    return m.get(city, city.replace("_", " "))


# ---------------------------------------------------------------- load
def load_geonames():
    """(country, admin1, city) -> time zone, and -> population (GeoNames cities500)."""
    tz, pop = {}, {}
    p = CACHE / "geonames-us" / "cities500.txt"
    if not p.exists():
        return tz, pop
    with p.open(encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 18:
                continue
            cc, admin1, name = parts[8], parts[10].strip().upper(), parts[1].strip().lower()
            if cc not in ("US", "CA"):
                continue
            key = (cc, admin1, name)
            tz.setdefault(key, parts[17].strip())
            try:
                n = int(parts[14] or 0)
            except ValueError:
                n = 0
            if n > pop.get(key, 0):
                pop[key] = n
    return tz, pop


def load_us_zips():
    rows, missing = [], 0
    p = CACHE / "us-zip-codes.csv"
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            codes = [c.strip() for c in (r.get("area_codes") or "").split("|") if c.strip().isdigit()]
            if not codes:
                missing += 1
                continue
            try:
                pop = int((r.get("population") or "").strip() or 0)
            except ValueError:
                pop = 0
            rows.append({
                "zip": clean(r["zip"]), "city": clean(r["city"]), "state": clean(r["state"]),
                "state_name": clean(r.get("state_name")), "county": clean(r.get("county_name")),
                "lat": fnum(r.get("lat")), "lng": fnum(r.get("lng")), "pop": pop, "codes": codes,
            })
    print(f"loaded {len(rows):,} US ZIPs with area codes ({missing:,} without)")
    return rows


def aggregate_us(zips, tzmap):
    codes = {}
    towns = {}
    for z in zips:
        st, city, pop = z["state"], z["city"], z["pop"]
        if not st or not city:
            continue
        key = (st, city)
        t = towns.get(key)
        tz = tzmap.get(("US", st, city.lower()), "")
        if t is None:
            t = towns[key] = {"state": st, "city": city, "pop": 0, "zips": [], "codes": set(),
                              "county": collections.Counter(), "lats": [], "lngs": [], "tz": collections.Counter()}
        t["pop"] += pop
        t["zips"].append(z["zip"])
        t["codes"].update(z["codes"])
        if z["county"]:
            t["county"][z["county"]] += 1
        if z["lat"] is not None and z["lng"] is not None:
            t["lats"].append(z["lat"])
            t["lngs"].append(z["lng"])
        if tz:
            t["tz"][tz] += 1
        for code in z["codes"]:
            d = codes.get(code)
            if d is None:
                d = codes[code] = {"country": "US", "regions": collections.Counter(),
                                   "towns": collections.Counter(), "counties": collections.Counter(),
                                   "zips": 0, "pop": 0, "co": collections.Counter(),
                                   "lats": [], "lngs": [], "tz": collections.Counter()}
            d["regions"][st] += 1
            d["towns"][key] += 1
            d["zips"] += 1
            d["pop"] += pop
            if z["county"]:
                d["counties"][z["county"]] += 1
            if z["lat"] is not None and z["lng"] is not None:
                d["lats"].append(z["lat"])
                d["lngs"].append(z["lng"])
            if tz:
                d["tz"][tz] += 1
            for other in z["codes"]:
                if other != code:
                    d["co"][other] += 1
    return codes, towns


def add_canada(codes, towns, tzmap, popmap):
    p = CACHE / "ca-area-code-cities.csv"
    if not p.exists():
        print("WARN: no Canadian area code data")
        return
    seen = set()
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f):
            if len(r) < 6:
                continue
            code, city, province = r[0].strip(), r[1].strip(), r[2].strip()
            lat, lng = fnum(r[4]), fnum(r[5])
            if not (code.isdigit() and city and len(code) == 3):
                continue
            prov = PROVINCE_BY_NAME.get(province.lower(), "")
            if not prov:
                continue
            tz = tzmap.get(("CA", prov, city.lower()), "") or STATE_TZ.get(prov, "")
            pop = popmap.get(("CA", prov, city.lower()), 0)
            key = (prov, city)
            seen.add(key)
            t = towns.get(key)
            if t is None:
                t = towns[key] = {"state": prov, "city": city, "pop": 0, "zips": [], "codes": set(),
                                  "county": collections.Counter(), "lats": [], "lngs": [], "tz": collections.Counter()}
            t["pop"] += pop
            t["codes"].add(code)
            if lat is not None and lng is not None:
                t["lats"].append(lat)
                t["lngs"].append(lng)
            if tz:
                t["tz"][tz] += 1
            d = codes.get(code)
            if d is None:
                d = codes[code] = {"country": "CA", "regions": collections.Counter(),
                                   "towns": collections.Counter(), "counties": collections.Counter(),
                                   "zips": 0, "pop": 0, "co": collections.Counter(),
                                   "lats": [], "lngs": [], "tz": collections.Counter()}
            d["regions"][prov] += 1
            d["towns"][key] += 1
            d["pop"] += pop
            if lat is not None and lng is not None:
                d["lats"].append(lat)
                d["lngs"].append(lng)
            if tz:
                d["tz"][tz] += 1
    # co-located Canadian codes: codes that share a town
    for key, t in towns.items():
        if t["state"] in PROVINCES:
            for a in t["codes"]:
                for b in t["codes"]:
                    if a != b:
                        codes[a]["co"][b] += 1
    print(f"added {len(seen):,} Canadian towns")


def finalize(codes, towns):
    for code, d in codes.items():
        n = len(d["lats"])
        d["lat"] = sum(d["lats"]) / n if n else None
        d["lon"] = sum(d["lngs"]) / n if n else None
        d["main_region"] = d["regions"].most_common(1)[0][0] if d["regions"] else ""
    for t in towns.values():
        n = len(t["lats"])
        t["lat"] = sum(t["lats"]) / n if n else None
        t["lon"] = sum(t["lngs"]) / n if n else None
        t["main_county"] = t["county"].most_common(1)[0][0] if t["county"] else ""
        t["main_tz"] = t["tz"].most_common(1)[0][0] if t["tz"] else STATE_TZ.get(t["state"], "")
    # overlay-ish groups: codes that serve the same towns (>=40% of this code's towns)
    for code, d in codes.items():
        thresh = max(1, int(0.4 * max(1, d["zips"] if d["country"] == "US" else len(d["towns"]))))
        d["shares"] = sorted((o for o, c in d["co"].items() if c >= thresh),
                             key=lambda o: -d["co"][o])


def load_countries():
    p = CACHE / "country-codes.csv"
    out = []
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            a2 = clean(r.get("ISO3166-1-Alpha-2")).upper()
            dial = clean(r.get("Dial"))
            name = NAME_FIX.get(a2) or clean(r.get("CLDR display name")) or clean(r.get("UNTERM English Short"))
            if not (a2 and dial and name):
                continue
            dials = [clean(x) for x in dial.split(",") if clean(x)]
            out.append({
                "iso2": a2, "iso3": clean(r.get("ISO3166-1-Alpha-3")).upper(), "name": name,
                "official": clean(r.get("official_name_en")),
                "dial": dials[0], "dials": dials,
                "region": clean(r.get("Region Name")), "subregion": clean(r.get("Sub-region Name")),
                "capital": clean(r.get("Capital")), "languages": clean(r.get("Languages")),
                "currency": clean(r.get("ISO4217-currency_alphabetic_code")),
                "currency_name": clean(r.get("ISO4217-currency_name")),
                "tld": clean(r.get("TLD")),
            })
    out.sort(key=lambda c: c["name"])
    print(f"loaded {len(out)} countries with dialing codes")
    return out


# ---------------------------------------------------------------- page bodies
def area_code_body(code, d, towns, codes, ccodes):
    region = region_name(d["main_region"])
    country = "the United States" if d["country"] == "US" else "Canada"
    tzs = [tz_short(t) for t, _ in d["tz"].most_common(2)]
    tz_txt = " and ".join(tzs) if tzs else tz_short(STATE_TZ.get(d["main_region"], ""))
    town_keys = [k for k, _ in d["towns"].most_common()]
    town_entries = [towns[k] for k in town_keys if k in towns]
    top_towns = sorted(town_entries, key=lambda t: -t["pop"])[:12]
    names = [t["city"] for t in top_towns[:3]]
    name_txt = ", ".join(names[:-1]) + (" and " + names[-1] if len(names) > 1 else (names[0] if names else region))
    shares = d.get("shares") or []

    lede = (f"{code} is a North American Numbering Plan area code for {region}, {country}. "
            f"It covers about {human(d['pop'])} people in {human(len(town_entries))} towns")
    if d["zips"]:
        lede += f" and {human(d['zips'])} ZIP codes"
    lede += f", including {name_txt}."

    facts = [
        ["Area code", f"<strong>{code}</strong>"],
        ["Country", "United States (+1)" if d["country"] == "US" else "Canada (+1)"],
        ["State / province", f'<a href="/state/{d["main_region"].lower()}/">{esc(region)}</a>'],
        ["Type", "Shares its towns with " + ", ".join(shares[:4]) if shares
         else "Standalone (no other NANP code covers the same towns)"],
        ["Time zone", esc(tz_txt)],
        ["Population covered", human(d["pop"])],
        ["Towns covered", human(len(town_entries))],
    ]
    if d["zips"]:
        facts.append(["ZIP codes", human(d["zips"])])
    if d["lat"] is not None:
        facts.append(["Approx. centre", f'{d["lat"]:.3f}, {d["lon"]:.3f}'])

    rows = [[town_link(t["state"], t["city"]),
             esc(t["main_county"]), human(t["pop"]) if t["pop"] else "—",
             human(len(t["zips"])) if t["zips"] else "—"] for t in top_towns]
    towns_tbl = table(["Town", "County", "Population", "ZIP codes"], rows) if rows else ""

    cty_rows = [[esc(c), human(n)] for c, n in d["counties"].most_common(12)]
    counties_tbl = table(["County", "ZIP codes"], cty_rows) if cty_rows else ""

    share_cards = cards([(f"/area-code/{c}/", c, f"{human(len(ccodes[c]['towns']))} towns")
                         for c in shares if c in ccodes]) if shares else ""
    near = []
    if d["lat"] is not None:
        for other, od in codes.items():
            if other == code or od["lat"] is None:
                continue
            near.append((haversine((d["lat"], d["lon"]), (od["lat"], od["lon"])), other))
        near.sort()
        near = near[:6]
    near_cards = cards([(f"/area-code/{o}/", o, f"{dist:,.0f} km") for dist, o in near]) if near else ""

    body = f"""
<h1>{code} Area Code — {esc(region)}</h1>
<p class="lede">{lede}</p>
{table(["Field", "Value"], facts)}
<h2>Where area code {code} is used</h2>
<p>Area code {code} is assigned to {esc(region)}, {country}, inside the North American Numbering
Plan. Numbers in the code are written <strong>({code}) NXX-XXXX</strong> at home and
<strong>+1 {code} NXX-XXXX</strong> when dialled from outside Canada and the United States.
Since the NANP moved to 10-digit dialling you must always include the area code, even for a local
call.</p>
{f'<p>Other area codes in this footprint: <strong>' + ", ".join(shares) + '</strong>. They serve towns '
 f'in the same territory, so a single street can contain numbers from more than one code. '
 f'That is normal in the NANP and does not change how you dial.</p>' if shares else ''}
<h2>Towns and cities in area code {code}</h2>
<p>The {human(len(town_entries))} towns below are the largest in the {code} footprint, ranked by
population. Every one of them links to its own page with the full list of area codes and ZIP codes
for that town.</p>
{towns_tbl}
{counties_tbl and "<h2>Counties covered</h2>" + counties_tbl}
{share_cards and "<h2>Other area codes serving the same towns</h2>" + share_cards}
{near_cards and "<h2>Nearby area codes</h2>" + near_cards}
<h2>How to dial area code {code}</h2>
<ul>
<li><strong>Within North America:</strong> {code} + 7-digit number ({code}-NXX-XXXX). The leading
1 is optional on a mobile phone and required on most landlines for long-distance.</li>
<li><strong>From abroad:</strong> your country's international prefix, then 1, then {code}, then the
7-digit number — for example 00 1 {code} NXX-XXXX from most of Europe.</li>
</ul>
{related([(f'/state/{d["main_region"].lower()}/', f"All area codes in {region}"),
          ("/area-code/", "Every NANP area code"),
          ("/guides/", "How NANP numbering works")])}
"""
    answers = [
        (f"What area code is {code}?",
         f"{code} is a North American Numbering Plan area code assigned to {esc(region)}, {country}. "
         f"It covers about {human(d['pop'])} people in {human(len(town_entries))} towns."),
        (f"Is {code} a US or Canadian area code?",
         f"{code} is a {'United States' if d['country'] == 'US' else 'Canadian'} area code. "
         f"Canada and the United States share the +1 country code, so both are part of the same "
         f"numbering plan."),
        (f"What time zone is area code {code} in?",
         f"Area code {code} is in the {esc(tz_txt)} time zone."),
        ("Do I have to dial 10 digits?",
         "Yes. Every NANP call now requires the area code plus the seven-digit number, even for a "
         "local call."),
    ]
    body += faq(answers)
    return body


def city_body(key, t, codes):
    st, city = key
    region = region_name(st)
    my_codes = sorted(t["codes"])
    main = [codes[c] for c in my_codes if c in codes]
    biggest = max(main, key=lambda d: d["pop"]) if main else None
    if len(my_codes) == 1:
        served = "area code " + my_codes[0]
    elif len(my_codes) == 2:
        served = "area codes " + " and ".join(my_codes)
    else:
        served = "area codes " + ", ".join(my_codes[:-1]) + " and " + my_codes[-1]
    lede = (f"{city} is served by {served}. It is in {esc(region)}"
            + (f", {esc(t['main_county'])}" if t["main_county"] else "") + ".")
    if t["pop"]:
        lede += f" About {human(t['pop'])} people live in its {human(len(t['zips']))} ZIP codes."
    tz_txt = tz_short(t["main_tz"]) if t["main_tz"] else ""

    facts = [["Area code(s)", ", ".join(f'<a href="/area-code/{c}/">{c}</a>' for c in my_codes)] if len(my_codes) <= 4
             else ["Area code(s)", ", ".join(my_codes[:8]) + " …"],
             ["State / province", f'<a href="/state/{st.lower()}/">{esc(region)}</a>']]
    if t["main_county"]:
        facts.append(["County", esc(t["main_county"])])
    if t["pop"]:
        facts.append(["Population", human(t["pop"])])
    facts.append(["ZIP codes", human(len(t["zips"])) if t["zips"] else "—"])
    if tz_txt:
        facts.append(["Time zone", esc(tz_txt)])
    if t["lat"] is not None:
        facts.append(["Coordinates", f'{t["lat"]:.4f}, {t["lon"]:.4f}'])

    code_rows = [[f'<a href="/area-code/{c}/">{c}</a>',
                  esc(region_name(codes[c]["main_region"])) if c in codes else "",
                  human(codes[c]["pop"]) if c in codes else "—",
                  ("Yes" if c in (biggest["shares"] if biggest else []) else "—") if c in codes else ""]
                 for c in my_codes]
    code_tbl = table(["Area code", "Main state", "Population covered", "Overlap"], code_rows)

    zip_links = ", ".join(f'<a href="https://zipcodes.tekify.xyz/zip/{z}/">{z}</a>' for z in t["zips"][:40])
    if len(t["zips"]) > 40:
        zip_links += f" … and {human(len(t['zips']) - 40)} more"

    # nearby towns in the same state that actually have a page
    near = []
    if t["lat"] is not None:
        for k2, t2 in STATE_TOWNS.get(st, []):
            if k2 == key or t2["lat"] is None or k2 not in CITY_PATH:
                continue
            near.append((haversine((t["lat"], t["lon"]), (t2["lat"], t2["lon"])), k2, t2))
        near.sort()
        near = near[:8]
    near_cards = cards([(CITY_PATH[k2], esc(t2["city"]),
                         ", ".join(sorted(t2["codes"]))[:26]) for _, k2, t2 in near])

    return f"""
<h1>{esc(city)}, {esc(st)} Area Codes</h1>
<p class="lede">{lede}</p>
{table(["Field", "Value"], facts)}
<h2>What area code is {esc(city)} in?</h2>
{code_tbl}
{("<h2>ZIP codes in the code footprint</h2><p>" + zip_links + "</p>") if zip_links else ""}
{("<h2>Nearby towns and their area codes</h2>" + near_cards) if near_cards else ""}
<h2>How to dial</h2>
<p>Dial <strong>{my_codes[0]} + 7 digits</strong> for a number in {esc(city)}, or
<strong>+1 {my_codes[0]} ...</strong> from abroad. Ten-digit dialling is required everywhere in the
North American Numbering Plan.</p>
{related([(f'/state/{st.lower()}/', f"All area codes in {region}"),
          (f'/area-code/{my_codes[0]}/', f"About area code {my_codes[0]}"),
          ("/area-code/", "Every NANP area code")])}
"""


def state_body(code, codes, towns, countries):
    name = region_name(code)
    mine = sorted([(c, d) for c, d in codes.items() if d["main_region"] == code or d["regions"].get(code)],
                  key=lambda x: -x[1]["pop"])
    rows = [[f'<a href="/area-code/{c}/">{c}</a>',
             ", ".join(t["city"] for t in
                       sorted([towns[k] for k in codes[c]["towns"]
                               if k in towns and (towns[k]["state"] == code or not
                                                  [x for x in codes[c]["towns"] if x in towns and towns[x]["state"] == code])],
                              key=lambda t: -t["pop"])[:3]),
             human(codes[c]["pop"]), human(codes[c]["zips"]),
             ", ".join(codes[c]["shares"][:2]) or "—"] for c, _ in mine]
    t = towns
    city_cards = cards([(CITY_PATH[k], esc(v["city"]), ", ".join(sorted(v["codes"]))) for k, v in
                        sorted(((k, v) for k, v in t.items() if k[0] == code and k in CITY_PATH),
                               key=lambda kv: -kv[1]["pop"])[:40]])
    total_pop = sum(d["pop"] for _, d in mine)
    return f"""
<h1>{esc(name)} Area Codes — {len(mine)} Codes</h1>
<p class="lede">{esc(name)} has {len(mine)} North American Numbering Plan area
code{"s" if len(mine) != 1 else ""}, covering about {human(total_pop)} people. The table lists each
code with its largest towns, population and overlaps.</p>
<h2>All area codes in {esc(name)}</h2>
{table(["Area code", "Largest towns", "Population", "ZIP codes", "Overlaps"], rows)}
<h2>Largest cities in {esc(name)}</h2>
{city_cards}
{related([("/state/", "All states and provinces"), ("/area-code/", "Every area code"),
          ("/guides/", "Numbering plan guides")])}
{faq([(f"How many area codes does {name} have?", f"{name} uses {len(mine)} area codes."),
      (f"What is the main area code in {name}?",
       f"{mine[0][0]} covers the largest population in {name}." if mine else f"{name} has one area code."),
      ("How do I find the area code for a town?",
       "Open the town in the city list above; each town page lists every area code assigned to it.")])}
"""


def country_body(c, by_region):
    dial = c["dial"]
    nanp = dial.startswith("1")
    digits = dial.replace("-", " ")
    facts = [["Country", esc(c["name"])],
             ["Dialling code", f"<strong>+{esc(dial)}</strong>"],
             ["ISO code", esc(c["iso2"]) + (" / " + esc(c["iso3"]) if c["iso3"] else "")]]
    if c["region"]:
        facts.append(["Region", esc(c["region"]) + (f" · {esc(c['subregion'])}" if c["subregion"] else "")])
    if c["capital"]:
        facts.append(["Capital", esc(c["capital"])])
    if c["languages"]:
        facts.append(["Languages", esc(c["languages"])])
    if c["currency"]:
        facts.append(["Currency", esc(c["currency"]) + (f" — {esc(c['currency_name'])}" if c["currency_name"] else "")])
    if c["tld"]:
        facts.append(["Internet TLD", esc(c["tld"])])

    others = [x for x in c["dials"][1:]]
    siblings = cards([(f"/country/{x['iso2'].lower()}/", esc(x["name"]), "+" + esc(x["dial"]))
                      for x in by_region if x["iso2"] != c["iso2"]][:18])

    how = f"""
<p>To call {esc(c['name'])} from another country, dial your international access prefix, then
<strong>{esc(digits.lstrip('+'))}</strong>, then the local number.</p>
<ul>
<li><strong>From the United States or Canada:</strong> 011 {esc(digits)}, then the local number.</li>
<li><strong>From most other countries:</strong> 00 {esc(digits)}, then the local number (some
countries use 0011, 010 or another carrier prefix — check your operator).</li>
<li><strong>From a mobile phone abroad:</strong> +{esc(digits)} works on almost every network.</li>
</ul>"""
    if nanp:
        how += (f"""<p>{esc(c['name'])} uses the North American Numbering Plan, so numbers are
<strong>+1 + area code + 7 digits</strong>. Dialling is exactly the same as calling the US or
Canada, and 10-digit dialling applies.</p>""")

    faq_pairs = [
        (f"What country is +{dial}?",
         f"+{dial} is the international dialling code for {esc(c['name'])}"
         + (f", with capital {esc(c['capital'])}" if c["capital"] else "") + "."),
        (f"How do I call {c['name']} from the US?",
         f"Dial 011, then {esc(digits)}, then the local number. From a mobile phone you can also dial "
         f"+{esc(digits)} followed by the local number."),
    ]
    if nanp:
        faq_pairs.append((f"Is calling {c['name']} the same as calling the US?",
                          "Yes for dialling. Numbers use +1, a 3-digit area code and 7 digits, "
                          "but your carrier may still bill it as an international call."))
    body = f"""
<h1>{esc(c['name'])} Country Code — +{esc(dial)}</h1>
<p class="lede">+{esc(dial)} is the international dialling code for {esc(c['name'])}.
Numbers in {esc(c['name'])} start with this prefix when dialled from abroad.</p>
{table(["Field", "Value"], facts)}
<h2>How to call {esc(c['name'])}</h2>
{how}
{('<p>Other codes for the same country: ' + ', '.join('+' + esc(d) for d in others) + '.</p>') if others else ''}
<h2>Other countries in {esc(c['region'] or 'the world')}</h2>
{siblings}
{related([("/country-codes/", "All country calling codes"), ("/guides/", "How international dialling works")])}
{faq(faq_pairs)}
"""
    return body


# ---------------------------------------------------------------- build
def build():
    zips = load_us_zips()
    tzmap, popmap = load_geonames()
    codes, towns = aggregate_us(zips, tzmap)
    add_canada(codes, towns, tzmap, popmap)
    finalize(codes, towns)
    REGIONS_ALL.clear()
    for d in codes.values():
        REGIONS_ALL.update(r for r in d["regions"] if r)
    REGIONS_ALL.update(t["state"] for t in towns.values() if t["state"])
    countries = load_countries()

    global towns_all
    towns_all = towns

    # limit city pages: the ones with real population, plus every Canadian town in the source
    us_cities = sorted(((k, v) for k, v in towns.items() if v["state"] not in PROVINCES),
                       key=lambda kv: -kv[1]["pop"])[:6000]
    ca_cities = sorted(((k, v) for k, v in towns.items() if v["state"] in PROVINCES),
                       key=lambda kv: -kv[1]["pop"])[:800]
    city_sel = us_cities + ca_cities
    print(f"area codes {len(codes)}, towns {len(towns):,}, city pages {len(city_sel):,}, countries {len(countries)}")

    # resolve city URLs up front so every other page only links to towns that exist
    CITY_PATH.clear()
    STATE_TOWNS.clear()
    seen_paths = set()
    for key, t in city_sel:
        p = f"/city/{key[0].lower()}-{slug(key[1])}/"
        if p in seen_paths:
            continue
        seen_paths.add(p)
        CITY_PATH[key] = p
    for key, t in towns.items():
        STATE_TOWNS.setdefault(t["state"], []).append((key, t))
    city_sel = [kt for kt in city_sel if kt[0] in CITY_PATH]

    s = Site(slug_="areacodes", brand="Area Codes & Dialing Codes",
             domain="areacodes.tekify.xyz",
             tagline="North American area codes and international dialling codes, with the towns, "
                     "ZIP codes and time zones behind each one.",
             description="Look up any US, Canadian or international dialling code: which towns an "
                         "area code covers, its county, time zone, ZIP codes and how to dial it.",
             nav=[("Area codes", "/area-code/"), ("States", "/state/"), ("Cities", "/city/"),
                  ("Countries", "/country-codes/"), ("Guides", "/guides/")],
             accent="#1f6feb",
             source_note="Area codes and ZIP coverage from zipcodes.pro (CC BY 4.0); Canadian codes "
                         "from the Area-Code-Geolocation-Database; country codes from the UN M49 list; "
                         "time zones and populations from GeoNames (CC BY 4.0).")

    # --- area code pages
    for code, d in sorted(codes.items(), key=lambda kv: kv[0]):
        if d["lat"] is None and not d["towns"]:
            continue
        region = region_name(d["main_region"])
        s.add(f"/area-code/{code}/", f"{code} Area Code — {region} Towns, Counties & Time Zone",
              f"Area code {code} covers {region} in "
              f"{'the US' if d['country'] == 'US' else 'Canada'}: "
              f"{len(d['towns'])} towns, {human(d['pop'])} people"
              + (f", {human(d['zips'])} ZIP codes" if d["zips"] else "")
              + f". Time zone, overlays and how to dial.",
              area_code_body(code, d, towns, codes, codes),
              crumbs=[("Area codes", "/area-code/"), (region, f"/state/{d['main_region'].lower()}/"),
                      (code, None)])

    # --- state / province pages
    for st in sorted(REGIONS_ALL):
        nm = region_name(st)
        n = sum(1 for d in codes.values() if st in d["regions"])
        s.add(f"/state/{st.lower()}/", f"{nm} Area Codes — All {n} Codes",
              f"Every area code in {nm}: {n} NANP codes with population, largest towns and overlaps, "
              f"plus a city list.",
              state_body(st, codes, towns, countries),
              crumbs=[("States", "/state/"), (nm, None)])

    # --- city pages
    made = 0
    for key, t in city_sel:
        st, city = key
        path = CITY_PATH[key]
        s.add(path, f"{city}, {st} Area Codes — {', '.join(sorted(t['codes']))}",
              f"{city}, {st} uses area code {', '.join(sorted(t['codes']))}. "
              f"County, population, ZIP codes, time zone and how to dial.",
              city_body(key, t, codes),
              crumbs=[("States", "/state/"), (region_name(st), f"/state/{st.lower()}/"), (city, None)])
        made += 1
    print(f"city pages written: {made:,}")

    # --- country pages
    by_region = collections.defaultdict(list)
    for c in countries:
        by_region[c["region"] or "Other"].append(c)
    for c in countries:
        s.add(f"/country/{c['iso2'].lower()}/", f"{c['name']} Dialing Code +{c['dial']} & How to Call",
              f"+{c['dial']} is the country calling code for {c['name']}. Capital, region, currency, "
              f"internet TLD and step-by-step dialling instructions.",
              country_body(c, by_region[c["region"] or "Other"]),
              crumbs=[("Country codes", "/country-codes/"), (c["name"], None)])

    # --- indexes
    add_home(s, codes, towns, city_sel, countries)
    add_indexes(s, codes, towns, countries, city_sel, by_region)
    add_guides(s)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>US area-code coverage is derived from {human(len(zips))} ZIP "
                    f"codes mapped to NANPA rate centres, published as open data by "
                    f'<a href="https://zipcodes.pro/download">zipcodes.pro</a> under CC BY 4.0. '
                    f"Canadian area codes come from the open Area-Code-Geolocation-Database. Country "
                    f"dialling codes come from the UN M49 country list. Time zones and populations "
                    f"come from <a href=\"https://www.geonames.org/\">GeoNames</a> (CC BY 4.0). "
                    f"Area codes are assigned by NANPA and change over time; this directory is "
                    f"regenerated from the underlying data so corrections appear on the next build.</p>")
    s.add_file("/data/search.json", json.dumps(search_index(codes, towns, city_sel, countries),
                                              separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    return s


towns_all = {}


def search_index(codes, towns, city_sel, countries):
    out = []
    for code, d in codes.items():
        out.append([code, f"Area code {code} — {region_name(d['main_region'])}", f"/area-code/{code}/"])
    for key, t in city_sel:
        st = key[0]
        out.append([t["city"], f"{st} · area code {', '.join(sorted(t['codes']))}",
                    CITY_PATH.get(key) or f"/city/{st.lower()}-{slug(t['city'])}/"])
    for code in sorted(REGIONS_ALL):
        out.append([region_name(code), f"State area codes ({code})", f"/state/{code.lower()}/"])
    for c in countries:
        out.append([c["name"], f"Country code +{c['dial']}", f"/country/{c['iso2'].lower()}/"])
    return out


POPULAR = ["US", "CA", "GB", "IN", "AU", "DE", "FR", "MX", "CN", "JP", "BR", "IE"]


def add_home(s, codes, towns, city_sel, countries):
    regions = REGIONS_ALL
    top = sorted(((c, d) for c, d in codes.items() if d["pop"]), key=lambda kv: -kv[1]["pop"])[:20]
    rows = [[f'<a href="/area-code/{c}/">{c}</a>', esc(region_name(d["main_region"])),
             human(d["pop"]), human(len(d["towns"]))] for c, d in top]
    by_iso = {c["iso2"]: c for c in countries}
    popular = [by_iso[i] for i in POPULAR if i in by_iso]
    body = f"""
<h1>Area Codes &amp; Country Dialing Codes</h1>
<p class="lede">{len(codes)} North American area codes and {len(countries)} international country
codes, each page showing the towns, counties, ZIP codes, time zone and dialling instructions behind
the number.</p>
<input type="search" id="q" placeholder="Search an area code, town, state or +country code" autocomplete="off">
<p class="mut" id="status">Type to search {human(len(towns))} towns, {len(codes)} area codes and {len(countries)} country codes.</p>
<div id="res"></div>
<p>
<span class="stat">{len(codes)} NANP area codes</span>
<span class="stat">{len(regions)} states &amp; provinces</span>
<span class="stat">{human(len(towns))} towns</span>
<span class="stat">{len(countries)} country codes</span>
</p>
{cards([("/area-code/", "All area codes", "A–Z by state"),
        ("/state/", "By state / province", f"{len(regions)} regions"),
        ("/city/", "By city", f"{human(len(city_sel))} city pages"),
        ("/country-codes/", "Country codes", f"{len(countries)} countries"),
        ("/guides/", "Guides", "How numbering works"),
        ("/search/", "Search", "Full directory")])}
<h2>Largest area codes by population</h2>
{table(["Area code", "State", "Population", "Towns"], rows)}
<h2>Popular country codes</h2>
{cards([(f"/country/{c['iso2'].lower()}/", esc(c["name"]), "+" + esc(c["dial"])) for c in popular])}
<h2>How to read a page here</h2>
<p>Each area-code page is built from ZIP-code data: it lists the towns an area code covers, the
counties those towns fall in, the population in the covered ZIP codes and the time zone. Because
US and Canadian codes share the <strong>+1</strong> country code, the country is stated explicitly on
every page. Overlapping codes are flagged, since a single town can be served by several area codes.</p>
{notice("Ten-digit dialling (area code + number) is required throughout the North American Numbering "
        "Plan, including for local calls.")}
"""
    s.add("/", "Area Codes & Country Dialing Codes — Lookup by Code, City or State",
          f"Look up any US or Canadian area code ({len(codes)} codes) or international country code "
          f"({len(countries)} countries): towns covered, time zone, ZIP codes and how to dial.",
          body)


def add_indexes(s, codes, towns, countries, city_sel, by_region):
    # /area-code/
    groups = collections.defaultdict(list)
    for code, d in sorted(codes.items()):
        groups[region_name(d["main_region"])].append(code)
    blocks = []
    for nm, lst in sorted(groups.items()):
        blocks.append(f"<h2>{esc(nm)}</h2>" + cards(
            [(f"/area-code/{c}/", c, human(len(codes[c]["towns"]))) for c in lst]))
    s.add("/area-code/", "All Area Codes — Full NANP List by State",
          "Every North American Numbering Plan area code, grouped by state and province, with town "
          "counts and links to full coverage pages.",
          f"<h1>All area codes</h1><p class=\"lede\">{len(codes)} NANP area codes covering the "
          f"United States, Canada and US territories, grouped by state and province.</p>" + "".join(blocks),
          crumbs=[("Area codes", None)])

    # /state/
    st_items = []
    for st in sorted(REGIONS_ALL):
        n = sum(1 for d in codes.values() if st in d["regions"])
        st_items.append((f"/state/{st.lower()}/", esc(region_name(st)), f"{n} codes"))
    s.add("/state/", "Area Codes by State and Province", "All US states, territories and Canadian "
          "provinces, with how many area codes each one uses and a link to the full list.",
          "<h1>Area codes by state and province</h1><p class=\"lede\">Pick a state or province to see "
          "every area code it uses, with population and overlap data.</p>" + cards(st_items),
          crumbs=[("States", None)])

    # /city/
    top = sorted(city_sel, key=lambda kv: -kv[1]["pop"])[:300]
    s.add("/city/", "Area Codes by City — Find a City's Area Code", "Look up the area code for a US "
          "or Canadian city: the 300 largest cities plus a search box over every city page.",
          f"<h1>Area codes by city</h1><p class=\"lede\">The 300 largest cities in the directory. "
          f"Use <a href=\"/search/\">search</a> for any of the {len(city_sel):,} city pages.</p>"
          + cards([(f"/city/{k[0].lower()}-{slug(v['city'])}/", esc(v["city"]),
                    f"{k[0]} · {', '.join(sorted(v['codes']))}") for k, v in top]),
          crumbs=[("Cities", None)])

    # /country-codes/
    blocks = []
    for region in sorted(by_region):
        blocks.append(f"<h2>{esc(region or 'Other')}</h2>" + cards(
            [(f"/country/{c['iso2'].lower()}/", esc(c["name"]), "+" + esc(c["dial"]))
             for c in sorted(by_region[region], key=lambda x: x["name"])]))
    s.add("/country-codes/", "All Country Calling Codes — International Dialing Codes List",
          "Every international dialing code by country and region: +1 North America, +44 UK, +91 "
          "India and 240 more, with how to call each one.",
          f"<h1>Country calling codes</h1><p class=\"lede\">All {len(countries)} countries with an "
          f"international dialling code, grouped by region. The code shown is the country's primary "
          f"prefix when dialling from abroad.</p>" + "".join(blocks),
          crumbs=[("Country codes", None)])

    # /search/
    s.add("/search/", "Search Area Codes, Cities and Country Codes", "Search the area code directory "
          "by code, town, state or country dialling code.",
          """<h1>Search area codes</h1>
<p class="lede">Type an area code, a town, a state or a country dialling code.</p>
<input type="search" id="q" placeholder="e.g. 201, Hackensack, New Jersey, +44" autocomplete="off">
<p class="mut" id="status">Start typing to search.</p>
<div id="res"></div>""",
          crumbs=[("Search", None)])


def add_guides(s):
    p = HERE / "guides.json"
    if not p.exists():
        print("WARN: sites/areacodes/guides.json missing — placeholder guides index only")
        s.add("/guides/", f"Guides — {s.brand}",
              "Explainers on area codes, country codes, overlays and 10-digit dialling.",
              "<h1>Guides</h1><p class=\"lede\">Explainers of how telephone numbering works.</p>"
              "<p>These guides are being written and will appear here shortly.</p>",
              crumbs=[("Guides", None)])
        return 0
    items = json.loads(p.read_text(encoding="utf-8"))
    for g in items:
        rel = [(lbl, url) for lbl, url in (g.get("rel") or [])]
        body = (f"<h1>{esc(g['h1'])}</h1><p class=\"lede\">{g['lede']}</p>{g['body']}"
                + (faq([tuple(x) for x in g.get("faq") or []]) if g.get("faq") else "")
                + (related(rel, "Where to go next") if rel else ""))
        s.add(f"/guides/{g['slug']}/", g["title"], g["desc"], body,
              crumbs=[("Guides", "/guides/"), (g["h1"], None)])
    index = ("<h1>Guides</h1><p class=\"lede\">Short, accurate explainers of how telephone numbering "
             "works — written so the directory pages make sense.</p>"
             + cards([(f"/guides/{g['slug']}/", esc(g["h1"]), esc(g["desc"][:70]) + "…") for g in items]))
    s.add("/guides/", f"Guides — {s.brand}",
          "Explainers on area codes, country codes, overlays and 10-digit dialling: how the numbering "
          "plan works and how to dial correctly.", index, crumbs=[("Guides", None)])
    print(f"guides added: {len(items)}")
    return len(items) + 1


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q||!res)return;
  var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/search.json').then(function(r){return r.json()}).then(function(d){
      idx=d;loading=false; if(st)st.textContent=d.length.toLocaleString()+' entries indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v){res.innerHTML='';return;}
    if(!idx){load();return;}
    var out=idx.filter(function(c){return (c[0]+' '+c[1]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML=out.length?'<div class="grid">'+out.slice(0,60).map(function(c){
      return '<a href="'+c[2]+'">'+esc(c[0])+' <span class="mut">'+esc(c[1])+'</span></a>';
    }).join('')+'</div>':'<p class="mut">Nothing found. Try a 3-digit area code or a town name.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,140);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
