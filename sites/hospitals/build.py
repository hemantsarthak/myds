#!/usr/bin/env python3
"""Build hospitals.tekify.xyz — a US hospital directory from CMS data.

Answers the questions people search for a hospital: where it is, how to call it, what type it is,
whether it has emergency services, and what its CMS quality ratings and measures look like.

Input : .cache/hospital_general.csv (CMS Provider Data, public domain) + GeoNames US postal data
        (already used by the zip/places sites) for city coordinates.
Output: site/ (~6k pages)

Pages
  /hospital/<slug>/   one page per hospital (5,419)
  /state/<ST>/        hospitals in a state (52)
  /city/<city>-<ST>/  hospitals in a city (top 400)
  /rating/<n>/        hospitals with a given CMS overall rating (1-5)
  /guides/            two explainers (inline)
  /search/  /         search + home
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

from engine.sitegen import Site, table, cards, related, faq, esc, slug, human, notice, seo_title  # noqa: E402

CACHE = ROOT / ".cache"
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
GROUPS = [
    ("Mortality", "MORT", "Deaths among patients treated for serious conditions"),
    ("Safety of care", "Safety", "Infections, complications and other harm events"),
    ("Readmission", "READM", "Patients who return to hospital soon after discharge"),
    ("Patient experience", "Pt Exp", "How patients rate communication and the hospital stay"),
    ("Timely & effective care", "TE", "How quickly and appropriately care is delivered"),
]


def clean(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def titlecase(s: str) -> str:
    s = clean(s).lower()
    small = {"of", "the", "and", "at", "in", "for", "on", "a", "an", "de", "la", "&"}
    return " ".join(w if (w in small and i) else (w[:1].upper() + w[1:]) for i, w in enumerate(s.split()))


def load():
    rows = list(csv.DictReader((CACHE / "hospital_general.csv").open(encoding="utf-8-sig")))
    # zip -> coordinates from GeoNames (for nearby hospitals)
    coords = {}
    geo = CACHE / "geonames-us" / "US.txt"
    if geo.exists():
        with geo.open(encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) > 10:
                    try:
                        coords.setdefault(p[1], (float(p[9]), float(p[10])))
                    except ValueError:
                        pass
    out = []
    for r in rows:
        name = clean(r["Facility Name"])
        if not name:
            continue
        zc = clean(r["ZIP Code"])[:5]
        lat, lon = coords.get(zc, (None, None))
        groups = {}
        for label, key, _desc in GROUPS:
            better = r.get(f"Count of {key} Measures Better")
            same = r.get(f"Count of {key} Measures No Different")
            worse = r.get(f"Count of {key} Measures Worse")
            if better or same or worse:
                groups[label] = (better or "0", same or "0", worse or "0")
        out.append({
            "id": clean(r["Facility ID"]), "name": titlecase(name),
            "address": titlecase(r["Address"]), "city": titlecase(r["City/Town"]),
            "state": clean(r["State"]), "zip": zc, "county": titlecase(r["County/Parish"]),
            "phone": clean(r["Telephone Number"]), "type": clean(r["Hospital Type"]),
            "owner": clean(r["Hospital Ownership"]),
            "emergency": clean(r["Emergency Services"]).lower() == "yes",
            "birthing": clean(r["Meets criteria for birthing friendly designation"]).lower() == "y",
            "rating": clean(r["Hospital overall rating"]),
            "lat": lat, "lon": lon, "groups": groups,
        })
    return out


def distance_km(a, b) -> float:
    if None in (a["lat"], a["lon"], b["lat"], b["lon"]):
        return 1e9
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def stars(rating) -> str:
    try:
        n = int(rating)
    except ValueError:
        return "Not rated"
    if not 1 <= n <= 5:
        return "Not rated"
    return "★" * n + "☆" * (5 - n) + f" ({n} of 5)"


def build() -> Site:
    hospitals = load()
    hospitals.sort(key=lambda h: (-(int(h["rating"]) if h["rating"].isdigit() else 0), h["name"]))
    used = collections.Counter()
    for h in hospitals:
        base = slug(h["name"])
        used[base] += 1
        h["url"] = (f"/hospital/{base}/" if used[base] == 1
                    else f"/hospital/{base}-{slug(h['city'])}/" if used[base] == 2
                    else f"/hospital/{base}-{h['id']}/")
    name_city = collections.Counter((h["name"], h["city"]) for h in hospitals)
    for h in hospitals:
        h["label"] = (h["name"] if name_city[(h["name"], h["city"])] == 1
                      else f'{h["name"]} (Facility {h["id"]})')

    by_state = collections.defaultdict(list)
    by_city = collections.defaultdict(list)
    by_rating = collections.defaultdict(list)
    for h in hospitals:
        by_state[h["state"]].append(h)
        by_city[(h["state"], h["city"])].append(h)
        if h["rating"].isdigit():
            by_rating[int(h["rating"])].append(h)
    city_rank = {k: i for i, (k, v) in enumerate(sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0])))}
    city_limit = 400
    city_pages = {k for k, _ in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]}
    state_url = {st: f"/state/{st.lower()}/" for st in by_state}
    city_url = {k: f"/city/{slug(k[1])}-{k[0].lower()}/" for k in city_pages}
    grid = collections.defaultdict(list)
    for h in hospitals:
        if h["lat"] is not None:
            grid[(int(h["lat"]), int(h["lon"]))].append(h)

    def nearby(h, limit=6):
        if h["lat"] is None:
            return []
        res = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for b in grid.get((int(h["lat"]) + dlat, int(h["lon"]) + dlon), ()):
                    if b["id"] == h["id"]:
                        continue
                    d = distance_km(h, b)
                    if d <= 80:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    s = Site("hospitals", "US Hospitals", "hospitals.tekify.xyz",
             "US hospital directory: location, contact, type, emergency services and CMS ratings.",
             "Look up any US hospital: address and phone, hospital type and ownership, emergency "
             "services, CMS overall star rating and quality measure results, plus nearby hospitals.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("Ratings", "/#ratings"), ("Guides", "/guides/")],
             source_note="Data: Centers for Medicare & Medicaid Services (CMS) Provider Data Catalog, "
                         "Hospital General Information (public domain), plus GeoNames coordinates. "
                         "Ratings are CMS overall hospital quality star ratings.")

    home = f"""
<h1>US hospitals: locations, services and CMS ratings</h1>
<p class="lede">Find any hospital in the United States — address and phone, type and ownership,
emergency services, and the CMS overall quality rating.
<span class="stat">{human(len(hospitals))} hospitals</span>
<span class="stat">{human(len(by_state))} states &amp; territories</span>
<span class="stat">{human(sum(len(v) for v in by_rating.values()))} rated</span></p>
<input type="search" id="q" placeholder="Johns Hopkins, Cleveland Clinic, Miami…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2 id="ratings">Browse by CMS rating</h2>
{cards([(f"/rating/{n}/", stars(str(n)), human(len(by_rating[n]))) for n in (5, 4, 3, 2, 1)])}
<h2>Largest states by hospital count</h2>
{cards([(state_url[st], esc(STATE_NAMES.get(st, st)), human(len(v))) for st, v in sorted(by_state.items(), key=lambda kv: -len(kv[1]))[:24]])}
<h2>What the CMS rating means</h2>
<p>CMS publishes an overall hospital quality star rating from 1 to 5 for hospitals that report
enough measures. It summarises five groups — mortality, safety of care, readmission, patient
experience, and timely &amp; effective care — each built from dozens of individual measures. A
5-star hospital performs well across groups relative to national averages; 1 star means it performs
worse. The rating is a comparison tool, not a verdict: small hospitals, specialty hospitals and
those with too few cases are often unrated.</p>
{notice("This directory reproduces official CMS data. It is not medical advice — for an emergency, "
        "call 911 or go to the nearest emergency department.")}
"""
    s.add("/", "US Hospitals — Ratings, Services and Locations",
          "Search 5,400 US hospitals: CMS overall star rating, quality measures, emergency services, "
          "hospital type, ownership, address and phone.", home)

    s.add("/search/", "Search US Hospitals by Name, City or State",
          "Search the US hospital directory by name, city, county or state.",
          """<h1>Search US hospitals</h1>
<p class="lede">Type a hospital name, city, county or state. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Johns Hopkins, Houston, Cleveland…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- guides
    s.add("/guides/what-is-the-cms-hospital-rating/", "What Is the CMS Hospital Star Rating?",
          "How the CMS overall hospital quality star rating is calculated, what the five groups "
          "measure, and why some hospitals are not rated.",
          """<h1>What is the CMS hospital star rating?</h1>
<p class="lede">The overall rating is a single 1–5 score built from five groups of quality measures.</p>
<h2>The five groups</h2>
<p>CMS groups dozens of measures into mortality (deaths among patients treated for serious
conditions), safety of care (infections and complications), readmission (patients returning soon
after discharge), patient experience (survey responses about communication and the stay), and
timely &amp; effective care (how quickly and appropriately care is delivered). Each group is
summarised as better than, no different from, or worse than the national average.</p>
<h2>How the star rating is derived</h2>
<p>Groups are weighted and combined into a summary score, then compared with other hospitals. A
hospital rated 5 stars performs better than most on most groups; 1 star means worse. The rating
reflects reported measures, not the size of the building or the reputation of the doctors.</p>
<h2>Why many hospitals are unrated</h2>
<p>A hospital needs enough measures in at least three groups to be rated. Small rural hospitals,
specialty hospitals (children's, psychiatric, rehabilitation) and facilities with low case volumes
often fall below the threshold, so "not rated" does not mean poor quality.</p>
""",
          crumbs=[("Guides", "/guides/"), ("CMS star rating", None)])

    s.add("/guides/hospital-types-explained/", "Hospital Types and Ownership Explained",
          "Acute care, critical access, psychiatric, children's and specialty hospitals, and what the "
          "ownership categories mean for patients.",
          """<h1>Hospital types and ownership explained</h1>
<p class="lede">The type and ownership of a hospital tells you what it is set up to treat and who runs it.</p>
<h2>Types</h2>
<p><strong>Acute care hospitals</strong> provide short-term inpatient and emergency care — the
general hospital most people picture. <strong>Critical access hospitals</strong> are small rural
facilities with limited beds and longer stays, kept open with special federal payments.
<strong>Psychiatric</strong>, <strong>rehabilitation</strong> and <strong>children's</strong>
hospitals specialise by patient group, and <strong>long-term care hospitals</strong> treat patients
who need extended stays.</p>
<h2>Ownership</h2>
<p>Ownership categories describe who operates the facility: government (federal, state, county or
hospital district), voluntary non-profit (religious or community), proprietary (for-profit
corporation), and physician-owned. Ownership affects governance and charity-care policies but is not
by itself a quality indicator — the quality measures on each hospital page are the better guide.</p>
""",
          crumbs=[("Guides", "/guides/"), ("Hospital types", None)])

    s.add("/guides/", "Guides — US Hospitals",
          "Explainers on CMS hospital ratings and hospital types.",
          "<h1>Guides</h1><p class=\"lede\">Short explainers to help you read the data on each hospital page.</p>"
          + cards([("/guides/what-is-the-cms-hospital-rating/", "What is the CMS hospital star rating?",
                    "How the 1–5 rating is built and why some hospitals are unrated."),
                   ("/guides/hospital-types-explained/", "Hospital types and ownership explained",
                    "Acute care, critical access, specialty hospitals and ownership categories.")]),
          crumbs=[("Guides", None)])

    # ---- rating pages
    for n in (5, 4, 3, 2, 1):
        group = sorted(by_rating[n], key=lambda h: h["name"])
        body = f"""
<h1>{stars(str(n))} hospitals</h1>
<p class="lede">{human(len(group))} hospitals have a CMS overall rating of {n} out of 5. The rating
compares performance across mortality, safety, readmission, patient experience and timely care.</p>
{cards([(h["url"], esc(h["name"]), f'{esc(h["city"])}, {esc(h["state"])}') for h in group[:200]])}
<p class="mut">Showing the first 200; use search to find a specific hospital.</p>
{related([("/#ratings", "All ratings"), ("/search/", "Search hospitals")])}
"""
        s.add(f"/rating/{n}/", f"{n}-Star Hospitals — CMS Overall Rating",
              f"{human(len(group))} US hospitals with a CMS overall quality rating of {n} of 5 stars, "
              f"with city, state and services.", body, crumbs=[("Ratings", "/#ratings"), (f"{n} stars", None)])

    # ---- state pages
    for st, group in sorted(by_state.items(), key=lambda kv: -len(kv[1])):
        sname = STATE_NAMES.get(st, st)
        rated = [h for h in group if h["rating"].isdigit()]
        avg = round(sum(int(h["rating"]) for h in rated) / len(rated), 2) if rated else None
        body = f"""
<h1>Hospitals in {esc(sname)}</h1>
<p class="lede">{human(len(group))} hospitals in {esc(sname)}{f', {human(len(rated))} of them rated by CMS (average {avg} stars)' if avg else ''}.</p>
{cards([(h["url"], esc(h["name"]), f'{esc(h["city"])} · {stars(h["rating"])}') for h in group[:200]])}
<h2>About hospital care in {esc(sname)}</h2>
<p>Hospital ratings in {esc(sname)} vary by facility type and case mix. Critical access hospitals
in rural counties are often unrated, while large acute-care hospitals report enough measures to
receive a star rating. Use the individual pages for address, phone, emergency services and measure
results.</p>
{related([("/#ratings", "Browse by rating"), ("/search/", "Search hospitals")])}
"""
        s.add(state_url[st], f"Hospitals in {sname} — Ratings & Locations",
              f"{human(len(group))} hospitals in {sname}: CMS ratings, city, type, emergency services "
              f"and contact details.", body, crumbs=[("States", "/#states"), (sname, None)])

    # ---- city pages
    for (st, city), group in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]:
        sname = STATE_NAMES.get(st, st)
        body = f"""
<h1>Hospitals in {esc(city)}, {esc(st)}</h1>
<p class="lede">{human(len(group))} hospitals in {esc(city)}. Each entry links to its CMS rating,
services and contact details.</p>
{cards([(h["url"], esc(h["name"]), stars(h["rating"])) for h in group[:60]])}
{related([(state_url[st], f"All hospitals in {sname}"), ("/search/", "Search hospitals")])}
"""
        s.add(city_url[(st, city)], f"Hospitals in {city}, {st}",
              f"Hospitals in {city}, {st}: CMS ratings, emergency services, addresses and phone numbers.",
              body, crumbs=[("States", "/#states"), (sname, state_url[st]), (city, None)])

    # ---- hospital pages
    for h in hospitals:
        sname = STATE_NAMES.get(h["state"], h["state"])
        near = nearby(h)
        tlabel = re.sub(r"Hospitals$", "Hospital", h["type"]).lower()
        tarticle = "an" if tlabel[:1] in "aeiou" else "a"
        rows = [["Address", esc(h["address"])],
                ["City", f'{esc(h["city"])}, {esc(h["state"])} {esc(h["zip"])}'],
                ["County", esc(h["county"] or "—")],
                ["Phone", f'<a href="tel:{esc(re.sub(r"[^0-9+]", "", h["phone"]))}">{esc(h["phone"])}</a>' if h["phone"] else "—"],
                ["Hospital type", esc(h["type"])],
                ["Ownership", esc(h["owner"])],
                ["Emergency services", "Yes" if h["emergency"] else "No"],
                ["CMS overall rating", f'<strong>{stars(h["rating"])}</strong>'],
                ]
        if h["birthing"]:
            rows.append(["Birthing friendly", "Yes — meets CMS criteria"])
        group_rows = []
        for label, _key, desc in GROUPS:
            if label in h["groups"]:
                better, same, worse = h["groups"][label]
                group_rows.append([esc(label), esc(better), esc(same), esc(worse)])
        group_html = ""
        if group_rows:
            group_html = ("<h2>Quality measures by group</h2>"
                          + table(["Measure group", "Better than national", "No different", "Worse than national"], group_rows)
                          + "<p>Counts show how many individual measures in each group performed better "
                            "than, no differently from, or worse than the national average. A hospital "
                            "with more 'better' results and fewer 'worse' results generally earns a "
                            "higher star rating.</p>")
        body = f"""
<h1>{esc(h["label"])}</h1>
<p class="lede">{esc(h["name"])} is {esc(tarticle)} {esc(tlabel)} in {esc(h["city"])}, {esc(sname)},
operated by {esc(h["owner"].lower())}. Its CMS overall rating is <strong>{stars(h["rating"])}</strong>.</p>
{table(["Field", "Value"], rows)}
{group_html}
<h2>Location and contact</h2>
<p>{esc(h["name"])} is at {esc(h["address"])}, {esc(h["city"])}, {esc(h["state"])} {esc(h["zip"])}
{('in ' + esc(h["county"])) if h["county"] else ''}. Call <strong>{esc(h["phone"])}</strong> for
appointments and general enquiries{'; emergency services are available' if h['emergency'] else ''}.</p>
<h2>Nearby hospitals</h2>
{cards([(b["url"], esc(b["name"]), f'{d:,.0f} km · {esc(b["city"])}') for d, b in near]) or "<p>—</p>"}
{related([(state_url[h["state"]], f"All hospitals in {sname}"),
          (city_url.get((h["state"], h["city"])), f"Hospitals in {h['city']}") if (h["state"], h["city"]) in city_pages else ("/search/", "Search hospitals"),
          ("/guides/what-is-the-cms-hospital-rating/", "How the CMS rating works")])}
{faq([
    (f'What is the CMS rating of {h["name"]}?',
     (f'{esc(h["name"])} has an overall CMS rating of {stars(h["rating"])}. The rating summarises '
      f'mortality, safety, readmission, patient experience and timely care measures.'
      if h["rating"].isdigit() else
      f'{esc(h["name"])} is not rated by CMS, which usually means it reports too few measures — common '
      f'for small, rural or specialty hospitals.')),
    (f'Does {h["name"]} have an emergency room?',
     ('Yes — this hospital reports emergency services.' if h["emergency"]
      else 'No — this facility does not report emergency services; check nearby hospitals in an emergency.')),
    (f'What type of hospital is {h["name"]}?',
     f'It is {esc(tarticle)} {esc(tlabel)} with {esc(h["owner"].lower())} ownership.'),
])}
"""
        s.add(h["url"], seo_title(h["label"], " — CMS Rating & Services"),
              f'{h["name"]} in {h["city"]}, {h["state"]}: CMS rating {stars(h["rating"])}, '
              f'{h["type"].lower()}, emergency services, address and phone.',
              body, crumbs=[("States", "/#states"), (sname, state_url[h["state"]]), (h["name"], None)])

    s.add_file("/data/hospitals.json", json.dumps(
        [[h["name"], h["city"], h["state"], h["rating"], h["url"]] for h in hospitals],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(hospitals))} hospitals from the CMS Provider Data "
                    f"Catalog (Hospital General Information, public domain), with coordinates from "
                    f"GeoNames. Ratings and measure counts are reproduced as published by CMS; a "
                    f"facility that reports too few measures is unrated. This site is informational and "
                    f"is not medical advice.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/hospitals.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' hospitals indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(h){return (h[0]+' '+h[1]+' '+h[2]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML=out.length?'<div class="grid">'+out.slice(0,40).map(function(h){
      return '<a href="'+h[4]+'">'+esc(h[0])+' <span class="mut">'+esc(h[1])+', '+esc(h[2])+'</span></a>';
    }).join('')+'</div>':'<p class="mut">No hospital found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
