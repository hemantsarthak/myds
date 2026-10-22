#!/usr/bin/env python3
"""Build homehealth.tekify.xyz — a US home-health agency directory from CMS data.

Answers what families search for: which agencies serve my city, what services they offer, how they
are rated, and how they perform on CMS quality measures.

Input : .cache/home_health.csv (CMS Provider Data, public domain) + GeoNames ZIP coordinates
Output: site/ (~12.8k pages)

Pages
  /agency/<slug>/   one per agency (12,409)
  /state/<ST>/      agencies in a state (52)
  /city/<city>-<ST>/ agencies in a city (top 300)
  /rating/<n>/      agencies by CMS quality-of-patient-care star rating (1-5)
  /guides/          two explainers (inline)
  /search/  /       search + home
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
SERVICE_COLS = [
    ("Nursing care", "Offers Nursing Care Services"),
    ("Physical therapy", "Offers Physical Therapy Services"),
    ("Occupational therapy", "Offers Occupational Therapy Services"),
    ("Speech pathology", "Offers Speech Pathology Services"),
    ("Medical social services", "Offers Medical Social Services"),
    ("Home health aide", "Offers Home Health Aide Services"),
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
    path = CACHE / "home_health.csv"
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = [c for c in reader.fieldnames if c]
        rows = list(reader)
    measure_cols = [c for c in fields if c.startswith("How often ")]
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
        name = clean(r.get("Provider Name"))
        ccn = clean(r.get("CMS Certification Number (CCN)"))
        if not name or not ccn:
            continue
        zc = clean(r.get("ZIP Code"))[:5]
        lat, lon = coords.get(zc, (None, None))
        measures = []
        for col in measure_cols:
            v = clean(r.get(col))
            if not v or v in ("-", "N/A"):
                continue
            label = col[len("How often "):].strip()
            label = re.sub(r"^the home health team ", "", label)
            measures.append((label[:1].upper() + label[1:], v))
        services = [label for label, col in SERVICE_COLS if clean(r.get(col)).lower() == "yes"]
        out.append({
            "ccn": ccn, "name": titlecase(name), "address": titlecase(r.get("Address")),
            "city": titlecase(r.get("City/Town")), "state": clean(r.get("State")),
            "zip": zc, "phone": clean(r.get("Telephone Number")),
            "owner": clean(r.get("Type of Ownership")),
            "cert_date": clean(r.get("Certification Date")),
            "rating": clean(r.get("Quality of patient care star rating")),
            "services": services, "measures": measures,
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
    agencies = load()
    agencies.sort(key=lambda a: (-(int(a["rating"]) if a["rating"].isdigit() else 0), a["name"]))
    used = collections.Counter()
    for a in agencies:
        base = slug(a["name"])
        used[base] += 1
        a["url"] = (f"/agency/{base}/" if used[base] == 1
                    else f"/agency/{base}-{slug(a['city'])}/" if used[base] == 2
                    else f"/agency/{base}-{a['ccn']}/")
    name_city = collections.Counter((a["name"], a["city"]) for a in agencies)
    for a in agencies:
        a["label"] = (a["name"] if name_city[(a["name"], a["city"])] == 1
                      else f'{a["name"]} (CCN {a["ccn"]})')
    by_state = collections.defaultdict(list)
    by_city = collections.defaultdict(list)
    by_rating = collections.defaultdict(list)
    for a in agencies:
        by_state[a["state"]].append(a)
        by_city[(a["state"], a["city"])].append(a)
        if a["rating"].isdigit():
            by_rating[int(a["rating"])].append(a)
    city_rank = {k: i for i, (k, v) in enumerate(sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0])))}
    city_limit = 300
    city_pages = {k for k, _ in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]}
    state_url = {st: f"/state/{st.lower()}/" for st in by_state}
    city_url = {k: f"/city/{slug(k[1])}-{k[0].lower()}/" for k in city_pages}
    grid = collections.defaultdict(list)
    for a in agencies:
        if a["lat"] is not None:
            grid[(int(a["lat"]), int(a["lon"]))].append(a)

    def nearby(a, limit=6):
        if a["lat"] is None:
            return []
        res = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for b in grid.get((int(a["lat"]) + dlat, int(a["lon"]) + dlon), ()):
                    if b["ccn"] == a["ccn"]:
                        continue
                    d = distance_km(a, b)
                    if d <= 60:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    s = Site("homehealth", "US Home Health", "homehealth.tekify.xyz",
             "US home-health agencies: CMS star ratings, services, quality measures and location.",
             "Look up any Medicare-certified home-health agency: services offered, CMS quality-of-"
             "patient-care star rating, individual quality measures, address, phone and nearby agencies.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("Ratings", "/#ratings"), ("Guides", "/guides/")],
             source_note="Data: Centers for Medicare & Medicaid Services (CMS) Provider Data Catalog, "
                         "Home Health Care Agencies (public domain). The star rating summarises CMS "
                         "quality-of-patient-care measures.")

    home = f"""
<h1>US home health agencies: ratings, services and locations</h1>
<p class="lede">Find any Medicare-certified home-health agency — services offered, CMS star rating,
individual quality measures, address and phone.
<span class="stat">{human(len(agencies))} agencies</span>
<span class="stat">{human(len(by_state))} states &amp; territories</span>
<span class="stat">{human(sum(len(v) for v in by_rating.values()))} rated</span></p>
<input type="search" id="q" placeholder="Providence, home health, Miami…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2 id="ratings">Browse by quality-of-patient-care rating</h2>
{cards([(f"/rating/{n}/", stars(str(n)), human(len(by_rating[n]))) for n in (5, 4, 3, 2, 1)])}
<h2>States with the most agencies</h2>
{cards([(state_url[st], esc(STATE_NAMES.get(st, st)), human(len(v))) for st, v in sorted(by_state.items(), key=lambda kv: -len(kv[1]))[:24]])}
<h2>How home health works</h2>
<p>Home health agencies send nurses, therapists and aides into a patient's home for skilled care
after a hospital stay, for chronic conditions or for rehabilitation. Medicare covers home health
when a doctor certifies that you are homebound and need skilled nursing or therapy; the agency must
be Medicare-certified. CMS publishes a <strong>quality-of-patient-care star rating</strong> for each
agency based on measures such as timely care, improvement in walking and bathing, medication
management, flu vaccination and discharge to the community.</p>
{notice("This directory reproduces official CMS data for information only. Coverage, eligibility and "
        "referral decisions depend on a doctor's order and your Medicare plan.")}
"""
    s.add("/", "US Home Health Agencies — CMS Ratings, Services and Locations",
          "Search 12,400 Medicare-certified home health agencies: CMS star ratings, services offered, "
          "quality measures, address and phone.", home)

    s.add("/search/", "Search US Home Health Agencies",
          "Search home-health agencies by name, city or state.",
          """<h1>Search home health agencies</h1>
<p class="lede">Type an agency name, city or state. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Providence, home health, Houston…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- guides
    s.add("/guides/how-home-health-works/", "How Home Health Works (And Who Pays)",
          "What home-health agencies do, Medicare eligibility (homebound + skilled need), what a "
          "visit covers, and what to check before choosing an agency.",
          """<h1>How home health works</h1>
<p class="lede">Home health is skilled care delivered at home — nursing or therapy, not housekeeping.</p>
<h2>What agencies provide</h2>
<p>Medicare-certified agencies provide skilled nursing (wound care, injections, medication
management, education), physical, occupational and speech therapy, medical social services and
home-health aide support for personal care. The plan of care is written by a doctor and reviewed
regularly.</p>
<h2>Medicare eligibility</h2>
<p>Medicare covers home health when a doctor certifies that you need skilled care intermittently, you
are <strong>homebound</strong> (leaving home requires considerable effort or assistance), and the
agency is Medicare-certified. Original Medicare pays 100% of covered home-health services; it does
not cover 24-hour care or mostly custodial care.</p>
<h2>Choosing an agency</h2>
<p>Compare CMS star ratings and individual measures — especially improvement in walking and bathing,
timely initiation of care, and discharge to the community — then ask about staffing continuity,
after-hours availability and how the agency communicates with family.</p>
""",
          crumbs=[("Guides", "/guides/"), ("How it works", None)])

    s.add("/guides/home-health-star-rating-explained/", "The CMS Home Health Star Rating Explained",
          "What the quality-of-patient-care star rating measures, how to read the individual quality "
          "measures, and why small agencies may be unrated.",
          """<h1>The CMS home health star rating explained</h1>
<p class="lede">The star rating summarises a set of process and outcome measures into 1–5 stars.</p>
<h2>What goes into it</h2>
<p>CMS combines measures such as how often care began promptly, whether patients improved at walking,
moving around and bathing, whether breathing improved, how often patients took drugs correctly,
flu and pneumonia vaccination rates, and how often patients were discharged to the community.
Each measure has a national rate; the star rating summarises how the agency performs across them.</p>
<h2>Reading the measures</h2>
<p>Higher is not always better in the same direction: for "discharged to community" a higher rate
means more patients went home; for "hospitalisation" or "ED visits" a lower rate is better. Each
agency page lists the measures CMS publishes with the agency's rate, so read them next to the star.</p>
<h2>Why some agencies are unrated</h2>
<p>Agencies with too few patients in the reporting period do not get a star rating. "Not rated" is
not a quality signal — check the measures and talk to the agency.</p>
""",
          crumbs=[("Guides", "/guides/"), ("Star rating", None)])

    s.add("/guides/", "Guides — US Home Health",
          "Explainers on home health care and CMS quality ratings.",
          "<h1>Guides</h1><p class=\"lede\">Short explainers to help you read the data on each agency page.</p>"
          + cards([("/guides/how-home-health-works/", "How home health works",
                    "Services, Medicare eligibility and what to ask an agency."),
                   ("/guides/home-health-star-rating-explained/", "The CMS star rating explained",
                    "What the rating measures and how to read the individual quality measures.")]),
          crumbs=[("Guides", None)])

    # ---- rating pages
    for n in (5, 4, 3, 2, 1):
        group = sorted(by_rating[n], key=lambda a: (a["state"], a["name"]))
        body = f"""
<h1>{stars(str(n))} home health agencies</h1>
<p class="lede">{human(len(group))} agencies have a CMS quality-of-patient-care rating of {n} of 5 stars.</p>
{cards([(a["url"], esc(a["name"]), f'{esc(a["city"])}, {esc(a["state"])}') for a in group[:200]])}
<p class="mut">Showing the first 200; use search to find a specific agency.</p>
{related([("/#ratings", "All ratings"), ("/search/", "Search agencies")])}
"""
        s.add(f"/rating/{n}/", f"{n}-Star Home Health Agencies — CMS Rating",
              f"{human(len(group))} US home health agencies with a CMS quality-of-patient-care rating "
              f"of {n} of 5 stars.", body, crumbs=[("Ratings", "/#ratings"), (f"{n} stars", None)])

    # ---- state pages
    for st, group in sorted(by_state.items(), key=lambda kv: -len(kv[1])):
        sname = STATE_NAMES.get(st, st)
        rated = [a for a in group if a["rating"].isdigit()]
        avg = round(sum(int(a["rating"]) for a in rated) / len(rated), 2) if rated else None
        body = f"""
<h1>Home health agencies in {esc(sname)}</h1>
<p class="lede">{human(len(group))} Medicare-certified agencies in {esc(sname)}{f', {human(len(rated))} rated (average {avg} stars)' if avg else ''}.</p>
{cards([(a["url"], esc(a["name"]), f'{esc(a["city"])} · {stars(a["rating"])}') for a in group[:200]])}
<h2>About home health in {esc(sname)}</h2>
<p>{esc(sname)} has {human(len(group))} home-health agencies in this directory. Agency quality varies
widely: compare the star rating, the individual measures and the services offered (nursing, therapy,
aide) before choosing.</p>
{related([("/#ratings", "Browse by rating"), ("/search/", "Search agencies")])}
"""
        s.add(state_url[st], f"Home Health Agencies in {sname} — Ratings & Services",
              f"{human(len(group))} home health agencies in {sname}: CMS star ratings, services, "
              f"quality measures and contact details.", body, crumbs=[("States", "/#states"), (sname, None)])

    # ---- city pages
    for (st, city), group in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]:
        sname = STATE_NAMES.get(st, st)
        body = f"""
<h1>Home health agencies in {esc(city)}, {esc(st)}</h1>
<p class="lede">{human(len(group))} agencies serving {esc(city)}, ordered by CMS rating.</p>
{cards([(a["url"], esc(a["name"]), stars(a["rating"])) for a in group[:60]])}
{related([(state_url[st], f"All agencies in {sname}"), ("/search/", "Search agencies")])}
"""
        s.add(city_url[(st, city)], f"Home Health Agencies in {city}, {st}",
              f"Home health agencies in {city}, {st}: CMS ratings, services and contact details.",
              body, crumbs=[("States", "/#states"), (sname, state_url[st]), (city, None)])

    # ---- agency pages
    for a in agencies:
        sname = STATE_NAMES.get(a["state"], a["state"])
        near = nearby(a)
        rows = [["Address", esc(a["address"])],
                ["City", f'{esc(a["city"])}, {esc(a["state"])} {esc(a["zip"])}'],
                ["Phone", f'<a href="tel:{esc(re.sub(r"[^0-9+]", "", a["phone"]))}">{esc(a["phone"])}</a>' if a["phone"] else "—"],
                ["Ownership", esc(a["owner"] or "—")],
                ["Medicare certification date", esc(a["cert_date"] or "—")],
                ["CMS quality-of-patient-care rating", f'<strong>{stars(a["rating"])}</strong>'],
                ["Services offered", esc(", ".join(a["services"]) or "not reported")],
                ]
        measure_html = ""
        if a["measures"]:
            mrows = [[esc(label), esc(value)] for label, value in a["measures"][:14]]
            measure_html = ("<h2>Quality measures</h2>"
                            + table(["Measure", "Agency rate"], mrows)
                            + "<p>Rates are the percentages CMS reports for this agency. Read them "
                              "next to the national comparison on the CMS Care Compare site: for some "
                              "measures higher is better (improvement, vaccination), for others lower "
                              "is better (hospitalisation, emergency visits).</p>")
        body = f"""
<h1>{esc(a["label"])}</h1>
<p class="lede">{esc(a["label"])} is a Medicare-certified home health agency in {esc(a["city"])},
{esc(sname)}. Its CMS quality-of-patient-care rating is <strong>{stars(a["rating"])}</strong>.</p>
{table(["Field", "Value"], rows)}
{measure_html}
<h2>Services</h2>
<p>{('This agency reports offering: ' + esc(', '.join(a["services"])) + '.') if a["services"] else 'Service mix is not reported in the CMS file for this agency.'}
Home health services are ordered by a doctor and delivered in the patient's home; Medicare covers
skilled nursing and therapy for eligible homebound patients.</p>
<h2>Location and contact</h2>
<p>{esc(a["label"])} is at {esc(a["address"])}, {esc(a["city"])}, {esc(a["state"])} {esc(a["zip"])}.
Call <strong>{esc(a["phone"])}</strong> for referrals and eligibility questions.</p>
<h2>Nearby agencies</h2>
{cards([(b["url"], esc(b["name"]), f'{d:,.1f} km · {esc(b["city"])} · {stars(b["rating"])}') for d, b in near]) or "<p>—</p>"}
{related([(state_url[a["state"]], f"All agencies in {sname}"),
          (city_url.get((a["state"], a["city"])), f"Agencies in {a['city']}") if (a["state"], a["city"]) in city_pages else ("/search/", "Search agencies"),
          ("/guides/how-home-health-works/", "How home health works")])}
{faq([
    (f'What is the CMS rating of {a["label"]}?',
     (f'{esc(a["label"])} has a quality-of-patient-care star rating of {stars(a["rating"])}, based on '
      f'CMS measures such as timely care, improvement in walking and bathing, and discharge to the community.'
      if a["rating"].isdigit() else
      f'{esc(a["label"])} does not have a CMS star rating, usually because it had too few patients in the reporting period.')),
    (f'What services does {a["label"]} offer?',
     (f'It reports offering {esc(", ".join(a["services"]))}.' if a["services"]
      else 'The CMS file does not list its service mix; call the agency to confirm.')),
    (f'Does Medicare cover {a["label"]}?',
     'Medicare covers home health from Medicare-certified agencies when a doctor certifies a skilled '
     'need and the patient is homebound. Confirm coverage with the agency and your plan.'),
])}
"""
        s.add(a["url"], seo_title(a["label"], " — CMS Rating & Services"),
              f'{a["label"]} in {a["city"]}, {a["state"]}: CMS star rating '
              f'{stars(a["rating"])}, services, quality measures and phone number.',
              body, crumbs=[("States", "/#states"), (sname, state_url[a["state"]]), (a["label"], None)])

    s.add_file("/data/homehealth.json", json.dumps(
        [[a["name"], a["city"], a["state"], a["rating"], a["url"]] for a in agencies],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(agencies))} Medicare-certified home health agencies "
                    f"from the CMS Provider Data Catalog (Home Health Care Agencies, public domain). "
                    f"Star ratings and quality measures are reproduced as published by CMS. This site "
                    f"is informational; coverage and referrals depend on a doctor's order and your plan.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/homehealth.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' agencies indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(a){return (a[0]+' '+a[1]+' '+a[2]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML = out.length ? '<div class="grid">'+out.slice(0,40).map(function(a){
      return '<a href="'+a[4]+'">'+esc(a[0])+' <span class="mut">'+esc(a[1])+', '+esc(a[2])+'</span></a>';
    }).join('')+'</div>' : '<p class="mut">No agency found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
