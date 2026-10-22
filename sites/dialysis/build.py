#!/usr/bin/env python3
"""Build dialysis.tekify.xyz — a US dialysis-facility directory from CMS data.

Answers what patients and families search: which dialysis centres are nearby, what services they
offer, how many stations they have, and what CMS's five-star rating and quality measures say.

Input : .cache/dialysis.csv (CMS Provider Data, public domain) + GeoNames ZIP coordinates
Output: site/ (~7.8k pages)

Pages
  /facility/<slug>/   one per facility (7,490)
  /state/<ST>/        facilities in a state (52)
  /city/<city>-<ST>/  facilities in a city (top 250)
  /rating/<n>/        facilities by CMS five-star rating (1-5)
  /guides/            two explainers
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

from engine.sitegen import Site, table, cards, related, faq, esc, slug, human, notice, seo_title, health_cross_links  # noqa: E402

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
MEASURES = [
    ("Patient survival", "Patient Survival Category Text", "Mortality Rate (Facility)",
     "Number of Patients included in survival summary", "patients"),
    ("Hospitalisation", "Patient hospitalization category text", "Hospitalization Rate (Facility)",
     "Number of patients included in hospitalization summary", "patients"),
    ("Hospital readmission", "Patient Hospital Readmission Category", "Readmission Rate (Facility)",
     "Number of hospitalizations included in hospital readmission summary", "hospitalisations"),
    ("Transfusion", "Patient Transfusion category text", "Transfusion Rate (Facility)",
     "Number of patients included in the transfusion summary", "patients"),
    ("Emergency-department visits", "SEDR category text", "Standardized ED visits ratio (Facility)",
     "Number of patients included in SEDR summary", "patients"),
]


def clean(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def titlecase(s: str) -> str:
    s = clean(s).lower()
    small = {"of", "the", "and", "at", "in", "for", "on", "a", "an", "de", "la", "&"}
    return " ".join(w if (w in small and i) else (w[:1].upper() + w[1:]) for i, w in enumerate(s.split()))


def stars(rating) -> str:
    try:
        n = int(str(rating).strip())
    except (TypeError, ValueError):
        return "Not rated"
    if not 1 <= n <= 5:
        return "Not rated"
    return "★" * n + "☆" * (5 - n) + f" ({n} of 5)"


def load():
    rows = list(csv.DictReader((CACHE / "dialysis.csv").open(encoding="utf-8-sig")))
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
        name = re.sub(r"^\d{6}\s+", "", clean(r.get("Facility Name")))  # some rows prefix the CCN
        ccn = clean(r.get("CMS Certification Number (CCN)"))
        if not name or not ccn:
            continue
        zc = clean(r.get("ZIP Code"))[:5]
        lat, lon = coords.get(zc, (None, None))
        measures = []
        for label, cat_col, rate_col, n_col, unit in MEASURES:
            cat = clean(r.get(cat_col))
            rate = clean(r.get(rate_col))
            n = clean(r.get(n_col))
            if cat and cat.lower() not in ("not available", ""):
                measures.append((label, cat, rate, n, unit))
        waitlisted = clean(r.get("Percentage of Prevalent Patients Waitlisted for Kidney Transplant"))
        out.append({
            "ccn": ccn, "name": titlecase(name),
            "address": titlecase(clean(r.get("Address Line 1")) + (" " + clean(r.get("Address Line 2")) if clean(r.get("Address Line 2")) else "")),
            "city": titlecase(r.get("City/Town")), "state": clean(r.get("State")),
            "zip": zc, "county": titlecase(r.get("County/Parish")),
            "phone": clean(r.get("Telephone Number")),
            "profit": clean(r.get("Profit or Non-Profit")),
            "chain": clean(r.get("Chain Organization")),
            "chain_owned": clean(r.get("Chain Owned")).lower() == "yes",
            "stations": clean(r.get("# of Dialysis Stations")),
            "late_shift": clean(r.get("Late Shift")).lower() == "yes",
            "in_center": clean(r.get("Offers in-center hemodialysis")).lower() == "yes",
            "peritoneal": clean(r.get("Offers peritoneal dialysis")).lower() == "yes",
            "home_hd": clean(r.get("Offers home hemodialysis training")).lower() == "yes",
            "cert_date": clean(r.get("Certification Date")),
            "rating": clean(r.get("Five Star")),
            "measures": measures,
            "waitlisted": waitlisted if waitlisted not in ("", "0.0") else "",
            "lat": lat, "lon": lon,
        })
    return out


def distance_km(a, b) -> float:
    if None in (a["lat"], a["lon"], b["lat"], b["lon"]):
        return 1e9
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def build() -> Site:
    facilities = load()
    facilities.sort(key=lambda f: (-(int(f["rating"]) if f["rating"].isdigit() else 0), f["name"]))
    used = collections.Counter()
    for f in facilities:
        base = slug(f["name"])
        used[base] += 1
        f["url"] = (f"/facility/{base}/" if used[base] == 1
                    else f"/facility/{base}-{slug(f['city'])}/" if used[base] == 2
                    else f"/facility/{base}-{f['ccn']}/")
    name_city = collections.Counter((f["name"], f["city"]) for f in facilities)
    for f in facilities:
        f["label"] = (f["name"] if name_city[(f["name"], f["city"])] == 1
                      else f'{f["name"]} (CCN {f["ccn"]})')
    by_state = collections.defaultdict(list)
    by_city = collections.defaultdict(list)
    by_rating = collections.defaultdict(list)
    for f in facilities:
        by_state[f["state"]].append(f)
        by_city[(f["state"], f["city"])].append(f)
        if f["rating"].isdigit():
            by_rating[int(f["rating"])].append(f)
    city_rank = {k: i for i, (k, v) in enumerate(sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0])))}
    city_limit = 250
    city_pages = {k for k, _ in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]}
    state_url = {st: f"/state/{st.lower()}/" for st in by_state}
    city_url = {k: f"/city/{slug(k[1])}-{k[0].lower()}/" for k in city_pages}
    grid = collections.defaultdict(list)
    for f in facilities:
        if f["lat"] is not None:
            grid[(int(f["lat"]), int(f["lon"]))].append(f)

    def nearby(f, limit=6):
        if f["lat"] is None:
            return []
        res = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for b in grid.get((int(f["lat"]) + dlat, int(f["lon"]) + dlon), ()):
                    if b["ccn"] == f["ccn"]:
                        continue
                    d = distance_km(f, b)
                    if d <= 60:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    s = Site("dialysis", "US Dialysis Centers", "dialysis.tekify.xyz",
             "US dialysis facilities: CMS five-star ratings, services, stations and location.",
             "Look up any US dialysis facility: CMS five-star rating, patient survival, "
             "hospitalisation and readmission measures, services offered, number of stations, "
             "address and nearby centres.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("Ratings", "/#ratings"), ("Guides", "/guides/")],
             source_note="Data: Centers for Medicare & Medicaid Services (CMS) Provider Data Catalog, "
                         "Dialysis Facility listing (public domain). The five-star rating summarises "
                         "patient survival, hospitalisation, readmission and other measures.")

    home = f"""
<h1>US dialysis centres: CMS ratings, services and locations</h1>
<p class="lede">Find any Medicare-certified dialysis facility — its CMS five-star rating, quality
measures, services, number of stations and contact details.
<span class="stat">{human(len(facilities))} facilities</span>
<span class="stat">{human(len(by_state))} states &amp; territories</span>
<span class="stat">{human(sum(len(v) for v in by_rating.values()))} rated</span></p>
<input type="search" id="q" placeholder="Fresenius, DaVita, dialysis, Miami…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2 id="ratings">Browse by CMS five-star rating</h2>
{cards([(f"/rating/{n}/", stars(str(n)), human(len(by_rating[n]))) for n in (5, 4, 3, 2, 1)])}
<h2>States with the most dialysis facilities</h2>
{cards([(state_url[st], esc(STATE_NAMES.get(st, st)), human(len(v))) for st, v in sorted(by_state.items(), key=lambda kv: -len(kv[1]))[:24]])}
<h2>How the CMS dialysis star rating works</h2>
<p>CMS rates dialysis facilities from 1 to 5 stars using measures of <strong>patient survival</strong>,
<strong>hospitalisation</strong>, <strong>hospital readmission</strong>, transfusion, emergency-department
visits and transplant waitlisting. Each measure is compared with what CMS expects for the facility's
patients, so a small rural centre and a large urban one are judged on their own case mix. The rating
is a comparison tool — visit the facility, ask about staffing, shift times and home-dialysis training.</p>
{notice("This directory reproduces official CMS data for information only. Treatment decisions belong "
        "with your nephrologist and care team.")}
"""
    s.add("/", "US Dialysis Centers — CMS Ratings, Services and Locations",
          "Search 7,400 Medicare-certified dialysis facilities: CMS five-star ratings, quality "
          "measures, services offered, stations and contact details.", home)

    s.add("/search/", "Search US Dialysis Facilities",
          "Search dialysis centres by name, city, county or state.",
          """<h1>Search US dialysis facilities</h1>
<p class="lede">Type a facility name, city, county or state. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Fresenius, DaVita, Houston…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- guides
    s.add("/guides/dialysis-five-star-rating/", "The CMS Dialysis Five-Star Rating Explained",
          "What the five-star rating measures, how each quality measure is compared with expected "
          "results, and why some facilities are unrated.",
          """<h1>The CMS dialysis five-star rating explained</h1>
<p class="lede">Five stars summarise several outcome measures, each compared with what CMS expects.</p>
<h2>What goes into it</h2>
<p>CMS uses standardised ratios for patient survival (deaths compared with expected), hospitalisation,
hospital readmission, transfusion, emergency-department visits, and the percentage of patients
waitlisted for a kidney transplant. Each facility is compared with national expectations adjusted
for its patients' age, race, and whether they have diabetes, among other factors.</p>
<h2>Reading a single measure</h2>
<p>A measure is reported as "better than expected", "as expected" or "worse than expected". A
facility can be better than expected on survival while worse than expected on hospitalisation — the
star rating weighs the measures together, but the individual results on each facility page are worth
reading separately.</p>
<h2>Why some facilities are unrated</h2>
<p>Facilities with too few patients in the reporting period, or too little data on individual
measures, do not receive a star rating. "Not rated" is not a quality signal.</p>
""",
          crumbs=[("Guides", "/guides/"), ("Star rating", None)])

    s.add("/guides/in-center-vs-home-dialysis/", "In-Center vs Home Dialysis: What the Data Shows",
          "The difference between in-centre haemodialysis, peritoneal dialysis and home haemodialysis "
          "training — and how to tell which facilities offer what.",
          """<h1>In-centre vs home dialysis</h1>
<p class="lede">Facilities differ in which treatments they offer; the CMS listing records three.</p>
<h2>In-centre haemodialysis</h2>
<p>The classic option: three sessions a week at the facility, each lasting around four hours. It
requires travel and fixed shift times, but all clinical support is on site. Facilities offering a
"late shift" run evening sessions for people who work during the day.</p>
<h2>Peritoneal dialysis</h2>
<p>Done at home, usually daily, using the lining of the abdomen as the filter. It needs training,
storage space and a clean routine, but offers more flexibility and often preserves residual kidney
function longer.</p>
<h2>Home haemodialysis</h2>
<p>More frequent sessions at home, usually with a machine installed in the house and a care partner
trained to help. Outcomes can be good, but it is demanding and not suitable for everyone.</p>
<h2>Using this directory</h2>
<p>Each facility page lists which of the three it offers, whether it runs a late shift, and how many
stations it has — a useful filter when choosing where to receive treatment.</p>
""",
          crumbs=[("Guides", "/guides/"), ("Treatment types", None)])

    s.add("/guides/", "Guides — US Dialysis Centers",
          "Explainers on the CMS dialysis star rating and on treatment options.",
          "<h1>Guides</h1><p class=\"lede\">Short explainers to help you read the data on each facility page.</p>"
          + cards([("/guides/dialysis-five-star-rating/", "The CMS five-star rating explained",
                    "What the rating measures and how to read a single measure."),
                   ("/guides/in-center-vs-home-dialysis/", "In-centre vs home dialysis",
                    "The three treatment types and how facilities report them.")]),
          crumbs=[("Guides", None)])

    # ---- rating pages
    for n in (5, 4, 3, 2, 1):
        group = sorted(by_rating[n], key=lambda f: (f["state"], f["name"]))
        body = f"""
<h1>{stars(str(n))} dialysis facilities</h1>
<p class="lede">{human(len(group))} facilities have a CMS five-star rating of {n} out of 5.</p>
{cards([(f["url"], esc(f["name"]), f'{esc(f["city"])}, {esc(f["state"])}') for f in group[:200]])}
<p class="mut">Showing the first 200; use search to find a specific facility.</p>
{related([("/#ratings", "All ratings"), ("/search/", "Search facilities")])}
"""
        s.add(f"/rating/{n}/", f"{n}-Star Dialysis Facilities — CMS Rating",
              f"{human(len(group))} US dialysis facilities with a CMS five-star rating of {n} of 5.",
              body, crumbs=[("Ratings", "/#ratings"), (f"{n} stars", None)])

    # ---- state pages
    for st, group in sorted(by_state.items(), key=lambda kv: -len(kv[1])):
        sname = STATE_NAMES.get(st, st)
        rated = [f for f in group if f["rating"].isdigit()]
        avg = round(sum(int(f["rating"]) for f in rated) / len(rated), 2) if rated else None
        body = f"""
<h1>Dialysis facilities in {esc(sname)}</h1>
<p class="lede">{human(len(group))} Medicare-certified dialysis facilities in {esc(sname)}{f', {human(len(rated))} rated (average {avg} stars)' if avg else ''}.</p>
{cards([(f["url"], esc(f["name"]), f'{esc(f["city"])} · {stars(f["rating"])}') for f in group[:200]])}
<h2>About dialysis care in {esc(sname)}</h2>
<p>{esc(sname)} has {human(len(group))} dialysis facilities in this directory, run by a mix of
non-profit and for-profit operators and chains. Compare the five-star rating, the individual quality
measures, and whether the facility offers home dialysis training or a late shift.</p>
{related([("/#ratings", "Browse by rating"), ("/search/", "Search facilities")])}
"""
        s.add(state_url[st], f"Dialysis Facilities in {sname} — Ratings & Services",
              f"{human(len(group))} dialysis facilities in {sname}: CMS five-star ratings, services, "
              f"stations and contact details.", body, crumbs=[("States", "/#states"), (sname, None)])

    # ---- city pages
    for (st, city), group in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]:
        sname = STATE_NAMES.get(st, st)
        body = f"""
<h1>Dialysis facilities in {esc(city)}, {esc(st)}</h1>
<p class="lede">{human(len(group))} dialysis centres in {esc(city)}, ordered by CMS rating.</p>
{cards([(f["url"], esc(f["name"]), stars(f["rating"])) for f in group[:60]])}
{related([(state_url[st], f"All facilities in {sname}"), ("/search/", "Search facilities")])}
"""
        s.add(city_url[(st, city)], f"Dialysis Centers in {city}, {st}",
              f"Dialysis facilities in {city}, {st}: CMS ratings, services and contact details.",
              body, crumbs=[("States", "/#states"), (sname, state_url[st]), (city, None)])

    # ---- facility pages
    titles_used = set()
    for f in facilities:
        sname = STATE_NAMES.get(f["state"], f["state"])
        near = nearby(f)
        services = []
        if f["in_center"]:
            services.append("in-centre haemodialysis")
        if f["peritoneal"]:
            services.append("peritoneal dialysis")
        if f["home_hd"]:
            services.append("home haemodialysis training")
        rows = [["Address", esc(f["address"])],
                ["City", f'{esc(f["city"])}, {esc(f["state"])} {esc(f["zip"])}'],
                ["County", esc(f["county"] or "—")],
                ["Phone", f'<a href="tel:{esc(re.sub(r"[^0-9+]", "", f["phone"]))}">{esc(f["phone"])}</a>' if f["phone"] else "—"],
                ["Operator", esc(f["profit"] or "—")],
                ["Chain", esc(f["chain"] or "Independent")],
                ["Dialysis stations", esc(f["stations"] or "—")],
                ["Late shift", "Yes" if f["late_shift"] else "No"],
                ["Services", esc(", ".join(services) or "not reported")],
                ["CMS five-star rating", f'<strong>{stars(f["rating"])}</strong>'],
                ["Medicare certification", esc(f["cert_date"] or "—")],
                ]
        measure_rows = [[esc(label), esc(cat), esc(rate or "—"), esc(n or "—")]
                        for label, cat, rate, n, _unit in f["measures"]]
        measure_html = ""
        if measure_rows:
            measure_html = ("<h2>Quality measures</h2>"
                            + table(["Measure", "Result", "Rate / ratio", "Patients"], measure_rows)
                            + "<p>Each result compares the facility with what CMS expects for its "
                              "patients: better than expected, as expected, or worse than expected. "
                              "Lower rates are better for mortality, hospitalisation and readmission.</p>")
        body = f"""
<h1>{esc(f["label"])}</h1>
<p class="lede">{esc(f["label"])} is a dialysis facility in {esc(f["city"])}, {esc(sname)},
operated by {esc((f["profit"] or "an unreported operator").lower())}. Its CMS five-star rating is
<strong>{stars(f["rating"])}</strong>.</p>
{table(["Field", "Value"], rows)}
{measure_html}
{('<p>About ' + esc(f["waitlisted"]) + '% of prevalent patients at this facility were waitlisted for a kidney transplant.</p>') if f["waitlisted"] else ''}
<h2>Location and contact</h2>
<p>{esc(f["label"])} is at {esc(f["address"])}, {esc(f["city"])}, {esc(f["state"])} {esc(f["zip"])}
{('in ' + esc(f["county"])) if f["county"] else ''}. Call <strong>{esc(f["phone"])}</strong> for
referrals, shift times and home-dialysis training.</p>
<h2>Nearby dialysis facilities</h2>
{cards([(b["url"], esc(b["name"]), f'{d:,.1f} km · {esc(b["city"])} · {stars(b["rating"])}') for d, b in near]) or "<p>—</p>"}
{related([(state_url[f["state"]], f"All facilities in {sname}"),
          (city_url.get((f["state"], f["city"])), f"Facilities in {f['city']}") if (f["state"], f["city"]) in city_pages else ("/search/", "Search facilities"),
          ("/guides/dialysis-five-star-rating/", "How the rating works")])}
{health_cross_links(f["state"], "dialysis")}
{faq([
    (f'What is the CMS rating of {f["label"]}?',
     (f'{esc(f["label"])} has a CMS five-star rating of {stars(f["rating"])}, based on patient survival, '
      f'hospitalisation, readmission and other measures compared with national expectations.'
      if f["rating"].isdigit() else
      f'{esc(f["label"])} is not currently rated by CMS, usually because it has too few patients in the reporting period.')),
    (f'What services does {f["label"]} offer?',
     (f'It reports offering {esc(", ".join(services))}.' if services
      else 'The CMS listing does not report which dialysis modalities this facility offers; call to confirm.')),
    (f'How many dialysis stations does {f["label"]} have?',
     (f'It has {esc(f["stations"])} dialysis stations' + (', and runs a late shift.' if f["late_shift"] else '.')
      if f["stations"] else 'Station count is not reported for this facility.')),
])}
"""
        title = seo_title(f["label"], " — Dialysis Center, CMS Rating")
        if title in titles_used:
            title = seo_title(f'{f["label"]} ({f["ccn"]})', " — Dialysis Center")
        if title in titles_used:
            title = f'{f["label"][:38].rstrip()} — Dialysis {f["ccn"]}'
        titles_used.add(title)
        s.add(f["url"], title,
              f'{f["label"]} in {f["city"]}, {f["state"]}: CMS five-star rating '
              f'{stars(f["rating"])}, services, stations and phone number.',
              body, crumbs=[("States", "/#states"), (sname, state_url[f["state"]]), (f["label"], None)])

    s.add_file("/data/dialysis.json", json.dumps(
        [[f["name"], f["city"], f["state"], f["rating"], f["url"]] for f in facilities],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(facilities))} Medicare-certified dialysis facilities "
                    f"from the CMS Provider Data Catalog (Dialysis Facility listing, public domain). "
                    f"Ratings and quality measures are reproduced as published by CMS. This site is "
                    f"informational; treatment decisions belong with your care team.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/dialysis.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' facilities indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(f){return (f[0]+' '+f[1]+' '+f[2]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML = out.length ? '<div class="grid">'+out.slice(0,40).map(function(f){
      return '<a href="'+f[4]+'">'+esc(f[0])+' <span class="mut">'+esc(f[1])+', '+esc(f[2])+'</span></a>';
    }).join('')+'</div>' : '<p class="mut">No facility found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
