#!/usr/bin/env python3
"""Build nursinghomes.tekify.xyz — a US nursing-home directory from CMS data.

Answers what families actually search for: where the facility is, who runs it, how many beds and
residents, its CMS star ratings, staffing hours, turnover, inspection recency and nearby options.

Input : .cache/nursing_homes.csv (CMS Provider Data, public domain)
Output: site/ (~15k pages)

Pages
  /nursing-home/<slug>/  one per facility (14,690)
  /state/<ST>/           facilities in a state (52)
  /city/<city>-<ST>/     facilities in a city (top 300)
  /rating/<n>/           facilities by CMS overall rating (1-5)
  /guides/               two explainers (inline)
  /search/  /            search + home
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
RATING_FIELDS = [
    ("Overall rating", "Overall Rating"),
    ("Health inspection rating", "Health Inspection Rating"),
    ("Quality measure (QM) rating", "QM Rating"),
    ("Staffing rating", "Staffing Rating"),
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


def fnum(v, suffix="", d=1):
    try:
        x = float(str(v).strip())
    except (TypeError, ValueError):
        return "—"
    return f"{x:,.{d}f}{suffix}"


def load():
    rows = list(csv.DictReader((CACHE / "nursing_homes.csv").open(encoding="utf-8-sig")))
    out = []
    for r in rows:
        name = clean(r.get("Provider Name"))
        ccn = clean(r.get("CMS Certification Number (CCN)"))
        if not name or not ccn:
            continue
        try:
            lat = float(r.get("Latitude") or "")
            lon = float(r.get("Longitude") or "")
        except ValueError:
            lat = lon = None
        out.append({
            "ccn": ccn, "name": titlecase(name), "address": titlecase(r.get("Provider Address")),
            "city": titlecase(r.get("City/Town")), "state": clean(r.get("State")),
            "zip": clean(r.get("ZIP Code"))[:5], "county": titlecase(r.get("County/Parish")),
            "phone": clean(r.get("Telephone Number")),
            "owner": clean(r.get("Ownership Type")),
            "beds": clean(r.get("Number of Certified Beds")),
            "residents": clean(r.get("Average Number of Residents per Day")),
            "ptype": clean(r.get("Provider Type")),
            "in_hospital": clean(r.get("Provider Resides in Hospital")).upper() == "Y",
            "ccrc": clean(r.get("Continuing Care Retirement Community")).upper() == "Y",
            "special_focus": clean(r.get("Special Focus Status")),
            "abuse": clean(r.get("Abuse Icon")).upper() == "Y",
            "high_performing": clean(r.get("High Performing Icon")).upper() == "Y",
            "sprinklers": clean(r.get("Automatic Sprinkler Systems in All Required Areas")).upper() == "Y",
            "council": clean(r.get("With a Resident and Family Council")).upper() == "Y",
            "first_approved": clean(r.get("Date First Approved to Provide Medicare and Medicaid Services")),
            "ownership_change": clean(r.get("Provider Changed Ownership in Last 12 Months")).upper() == "Y",
            "inspection_old": clean(r.get("Most Recent Health Inspection More Than 2 Years Ago")).upper() == "Y",
            "chain": clean(r.get("Chain Name")),
            "chain_facilities": clean(r.get("Number of Facilities in Chain")),
            "chain_rating": clean(r.get("Chain Average Overall 5-star Rating")),
            "legal": clean(r.get("Legal Business Name")),
            "lat": lat, "lon": lon,
            "ratings": {label: clean(r.get(col)) for label, col in RATING_FIELDS},
            "staff_aide": clean(r.get("Reported Nurse Aide Staffing Hours per Resident per Day")),
            "staff_lpn": clean(r.get("Reported LPN Staffing Hours per Resident per Day")),
            "staff_rn": clean(r.get("Reported RN Staffing Hours per Resident per Day")),
            "staff_total": clean(r.get("Reported Total Nurse Staffing Hours per Resident per Day")),
            "staff_weekend": clean(r.get("Total number of nurse staff hours per resident per day on the weekend")),
            "turnover_total": clean(r.get("Total nursing staff turnover")),
            "turnover_rn": clean(r.get("Registered Nurse turnover")),
            "admin_left": clean(r.get("Number of administrators who have left the nursing home")),
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
    homes = load()
    homes.sort(key=lambda h: (-(int(h["ratings"]["Overall rating"]) if h["ratings"]["Overall rating"].isdigit() else 0), h["name"]))
    used = collections.Counter()
    for h in homes:
        base = slug(h["name"])
        used[base] += 1
        h["url"] = (f"/nursing-home/{base}/" if used[base] == 1
                    else f"/nursing-home/{base}-{slug(h['city'])}/" if used[base] == 2
                    else f"/nursing-home/{base}-{h['ccn']}/")
    name_city = collections.Counter((h["name"], h["city"]) for h in homes)
    for h in homes:
        h["label"] = (h["name"] if name_city[(h["name"], h["city"])] == 1
                      else f'{h["name"]} (CCN {h["ccn"]})')
    by_state = collections.defaultdict(list)
    by_city = collections.defaultdict(list)
    by_rating = collections.defaultdict(list)
    for h in homes:
        by_state[h["state"]].append(h)
        by_city[(h["state"], h["city"])].append(h)
        if h["ratings"]["Overall rating"].isdigit():
            by_rating[int(h["ratings"]["Overall rating"])].append(h)
    city_rank = {k: i for i, (k, v) in enumerate(sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0])))}
    city_limit = 300
    city_pages = {k for k, _ in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]}
    state_url = {st: f"/state/{st.lower()}/" for st in by_state}
    city_url = {k: f"/city/{slug(k[1])}-{k[0].lower()}/" for k in city_pages}
    grid = collections.defaultdict(list)
    for h in homes:
        if h["lat"] is not None:
            grid[(int(h["lat"]), int(h["lon"]))].append(h)

    def nearby(h, limit=6):
        if h["lat"] is None:
            return []
        res = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for b in grid.get((int(h["lat"]) + dlat, int(h["lon"]) + dlon), ()):
                    if b["ccn"] == h["ccn"]:
                        continue
                    d = distance_km(h, b)
                    if d <= 60:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    s = Site("nursinghomes", "US Nursing Homes", "nursinghomes.tekify.xyz",
             "US nursing homes: CMS star ratings, staffing, ownership, beds and location.",
             "Look up any US nursing home: CMS overall, inspection, quality and staffing ratings, "
             "staffing hours, turnover, ownership, certified beds, address and nearby facilities.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("Ratings", "/#ratings"), ("Guides", "/guides/")],
             source_note="Data: Centers for Medicare & Medicaid Services (CMS) Provider Data Catalog, "
                         "nursing home Provider Information (public domain). Ratings are CMS five-star "
                         "quality ratings based on health inspections, staffing and quality measures.")

    home = f"""
<h1>US nursing homes: CMS ratings, staffing and locations</h1>
<p class="lede">Find any Medicare/Medicaid-certified nursing home — its CMS star ratings, staffing
hours, turnover, ownership, beds and address.
<span class="stat">{human(len(homes))} facilities</span>
<span class="stat">{human(len(by_state))} states &amp; territories</span>
<span class="stat">{human(sum(len(v) for v in by_rating.values()))} rated</span></p>
<input type="search" id="q" placeholder="Sunrise, Manor, Boston…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2 id="ratings">Browse by CMS overall rating</h2>
{cards([(f"/rating/{n}/", stars(str(n)), human(len(by_rating[n]))) for n in (5, 4, 3, 2, 1)])}
<h2>States with the most nursing homes</h2>
{cards([(state_url[st], esc(STATE_NAMES.get(st, st)), human(len(v))) for st, v in sorted(by_state.items(), key=lambda kv: -len(kv[1]))[:24]])}
<h2>How the CMS five-star system works</h2>
<p>CMS rates each nursing home from 1 to 5 stars on three components: <strong>health inspections</strong>
(the most recent three years of survey results), <strong>staffing</strong> (nurse hours per resident
per day, adjusted for case mix) and <strong>quality measures</strong> (clinical outcomes such as
falls, pressure ulcers and antipsychotic use). The overall rating is derived from those three.
A separate icon flags facilities with abuse citations or special-focus status. The ratings are a
starting point for a visit and a conversation — not a substitute for seeing the facility.</p>
{notice("This directory reproduces official CMS data for information only. For placement decisions, "
        "contact your state's long-term care ombudsman or the facility directly.")}
"""
    s.add("/", "US Nursing Homes — CMS Ratings, Staffing and Locations",
          "Search 14,700 US nursing homes: CMS overall, health inspection, quality and staffing "
          "ratings, staffing hours, turnover, ownership, beds and contact details.", home)

    s.add("/search/", "Search US Nursing Homes",
          "Search nursing homes by name, city, county or state.",
          """<h1>Search US nursing homes</h1>
<p class="lede">Type a facility name, city, county or state. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Sunrise, Manor, Chicago…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- guides
    s.add("/guides/how-nursing-home-ratings-work/", "How the CMS Nursing Home Star Ratings Work",
          "What the overall, health inspection, staffing and quality-measure ratings measure, how "
          "they combine, and what the abuse and special-focus flags mean.",
          """<h1>How the CMS nursing home star ratings work</h1>
<p class="lede">Five stars summarise inspections, staffing and clinical quality measures.</p>
<h2>The three components</h2>
<p><strong>Health inspections</strong> come from state surveyors' unannounced visits over the last
three years: deficiencies, their scope and severity. <strong>Staffing</strong> compares nurse hours
per resident per day — including registered nurses on weekends — against expected levels for the
facility's residents. <strong>Quality measures</strong> track outcomes such as falls with major
injury, pressure ulcers, antipsychotic medication use and successful return to the community.</p>
<h2>The overall rating</h2>
<p>The overall star rating is derived from the three component ratings, with health inspections
weighing most heavily. A facility can earn 4 or 5 stars overall while still having a weak staffing
component, so read the components separately rather than only the headline number.</p>
<h2>Flags to look for</h2>
<p>An <strong>abuse icon</strong> means the facility was cited for abuse during the last three survey
cycles. <strong>Special focus status</strong> identifies facilities with a history of serious quality
problems that CMS monitors more closely. <strong>High-performing</strong> flags facilities that
performed well on a broad set of measures.</p>
<h2>What the ratings do not capture</h2>
<p>Staff turnover, administrator changes, culture, food, activities and how a facility feels on a
visit are not in the star rating. The pages here show turnover and administrator changes alongside
the stars so the picture is fuller.</p>
""",
          crumbs=[("Guides", "/guides/"), ("Star ratings", None)])

    s.add("/guides/how-to-choose-a-nursing-home/", "How to Choose a Nursing Home: A Practical Checklist",
          "A short, concrete checklist for comparing nursing homes: ratings, staffing, inspections, "
          "cost, location and the questions to ask on a visit.",
          """<h1>How to choose a nursing home</h1>
<p class="lede">Use the data to shortlist, then visit. The visit decides.</p>
<h2>Before the visit</h2>
<p>Filter by location (closer means easier visits, which matter), check the CMS overall and
component ratings, look at staffing hours and turnover, and read the inspection history. Confirm
whether the facility is Medicare- and Medicaid-certified, and whether it has the specific care you
need — memory care, rehabilitation, ventilator care or bariatric services.</p>
<h2>Questions to ask</h2>
<p>What is the staff-to-resident ratio on nights and weekends? What is the registered-nurse
coverage after hours? How often do administrators change? What is the current occupancy and is there
a waiting list? How are care plans reviewed with families? What happens if the resident's needs
increase — is there a higher level of care on site?</p>
<h2>On the visit</h2>
<p>Smell the air, watch how staff speak to residents, look at the activity calendar, taste the food,
and ask residents and families what they think. Compare at least three facilities. Ratings narrow
the list; the visit and the care plan decide.</p>
""",
          crumbs=[("Guides", "/guides/"), ("Choosing a home", None)])

    s.add("/guides/", "Guides — US Nursing Homes",
          "Explainers on CMS nursing home ratings and how to choose a facility.",
          "<h1>Guides</h1><p class=\"lede\">Short explainers to help you read the data on each facility page.</p>"
          + cards([("/guides/how-nursing-home-ratings-work/", "How CMS star ratings work",
                    "Inspections, staffing and quality measures — and the abuse/special-focus flags."),
                   ("/guides/how-to-choose-a-nursing-home/", "How to choose a nursing home",
                    "A practical checklist for shortlisting and visiting facilities.")]),
          crumbs=[("Guides", None)])

    # ---- rating pages
    for n in (5, 4, 3, 2, 1):
        group = sorted(by_rating[n], key=lambda h: (h["state"], h["name"]))
        body = f"""
<h1>{stars(str(n))} nursing homes</h1>
<p class="lede">{human(len(group))} facilities have a CMS overall rating of {n} out of 5 stars.</p>
{cards([(h["url"], esc(h["name"]), f'{esc(h["city"])}, {esc(h["state"])}') for h in group[:200]])}
<p class="mut">Showing the first 200; use search to find a specific facility.</p>
{related([("/#ratings", "All ratings"), ("/search/", "Search facilities")])}
"""
        s.add(f"/rating/{n}/", f"{n}-Star Nursing Homes — CMS Overall Rating",
              f"{human(len(group))} US nursing homes with a CMS overall rating of {n} of 5 stars, "
              f"with city, state and staffing data.", body, crumbs=[("Ratings", "/#ratings"), (f"{n} stars", None)])

    # ---- state pages
    for st, group in sorted(by_state.items(), key=lambda kv: -len(kv[1])):
        sname = STATE_NAMES.get(st, st)
        rated = [h for h in group if h["ratings"]["Overall rating"].isdigit()]
        avg = round(sum(int(h["ratings"]["Overall rating"]) for h in rated) / len(rated), 2) if rated else None
        body = f"""
<h1>Nursing homes in {esc(sname)}</h1>
<p class="lede">{human(len(group))} certified nursing homes in {esc(sname)}{f', {human(len(rated))} rated by CMS (average {avg} stars)' if avg else ''}.</p>
{cards([(h["url"], esc(h["name"]), f'{esc(h["city"])} · {stars(h["ratings"]["Overall rating"])}') for h in group[:200]])}
<h2>About nursing home care in {esc(sname)}</h2>
<p>{esc(sname)} has {human(len(group))} Medicare/Medicaid-certified nursing homes in this directory.
Ratings vary by ownership and by region; compare the component ratings (inspections, staffing,
quality measures) rather than the overall star alone, and check staffing turnover for signs of
stability.</p>
{related([("/#ratings", "Browse by rating"), ("/search/", "Search facilities")])}
"""
        s.add(state_url[st], f"Nursing Homes in {sname} — Ratings & Locations",
              f"{human(len(group))} nursing homes in {sname}: CMS star ratings, staffing, ownership, "
              f"beds and contact details.", body, crumbs=[("States", "/#states"), (sname, None)])

    # ---- city pages
    for (st, city), group in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:city_limit]:
        sname = STATE_NAMES.get(st, st)
        body = f"""
<h1>Nursing homes in {esc(city)}, {esc(st)}</h1>
<p class="lede">{human(len(group))} nursing homes in {esc(city)}, ordered by CMS rating.</p>
{cards([(h["url"], esc(h["name"]), stars(h["ratings"]["Overall rating"])) for h in group[:60]])}
{related([(state_url[st], f"All nursing homes in {sname}"), ("/search/", "Search facilities")])}
"""
        s.add(city_url[(st, city)], f"Nursing Homes in {city}, {st}",
              f"Nursing homes in {city}, {st}: CMS ratings, staffing hours, ownership and contact details.",
              body, crumbs=[("States", "/#states"), (sname, state_url[st]), (city, None)])

    # ---- facility pages
    for h in homes:
        sname = STATE_NAMES.get(h["state"], h["state"])
        near = nearby(h)
        rating_rows = [[label, f'<strong>{stars(h["ratings"][label])}</strong>'] for label, _c in RATING_FIELDS]
        staff_rows = []
        for label, key, suffix in (("Nurse aide hours", "staff_aide", " h/resident/day"),
                                   ("LPN hours", "staff_lpn", " h/resident/day"),
                                   ("RN hours", "staff_rn", " h/resident/day"),
                                   ("Total nurse hours", "staff_total", " h/resident/day"),
                                   ("Weekend nurse hours", "staff_weekend", " h/resident/day"),
                                   ("Total nursing turnover", "turnover_total", "%"),
                                   ("RN turnover", "turnover_rn", "%")):
            if h[key]:
                staff_rows.append([label, fnum(h[key], suffix, 2 if suffix.endswith("day") else 1)])
        rows = [["Address", esc(h["address"])],
                ["City", f'{esc(h["city"])}, {esc(h["state"])} {esc(h["zip"])}'],
                ["County", esc(h["county"] or "—")],
                ["Phone", f'<a href="tel:{esc(re.sub(r"[^0-9+]", "", h["phone"]))}">{esc(h["phone"])}</a>' if h["phone"] else "—"],
                ["Ownership", esc(h["owner"] or "—")],
                ["Provider type", esc(h["ptype"] or "—")],
                ["Certified beds", esc(h["beds"] or "—")],
                ["Average residents/day", esc(h["residents"] or "—")],
                ["First approved (Medicare/Medicaid)", esc(h["first_approved"] or "—")],
                ]
        flags = []
        if h["abuse"]:
            flags.append("CMS abuse icon — cited for abuse in recent survey cycles")
        if h["special_focus"]:
            flags.append(f"Special focus status: {h['special_focus']}")
        if h["high_performing"]:
            flags.append("CMS high-performing facility")
        if h["in_hospital"]:
            flags.append("Located inside a hospital")
        if h["ccrc"]:
            flags.append("Continuing care retirement community (CCRC)")
        if h["ownership_change"]:
            flags.append("Changed ownership in the last 12 months")
        if h["inspection_old"]:
            flags.append("Most recent health inspection more than 2 years ago")
        if h["sprinklers"]:
            flags.append("Automatic sprinklers in all required areas")
        if h["council"]:
            flags.append("Has a resident and family council")
        chain_html = ""
        if h["chain"]:
            chain_html = (f'<p>Part of the <strong>{esc(h["chain"])}</strong> chain '
                          f'({esc(h["chain_facilities"] or "?")} facilities'
                          + (f', chain average overall rating {esc(h["chain_rating"])} stars' if h["chain_rating"] else '')
                          + ').</p>')
        body = f"""
<h1>{esc(h["label"])}</h1>
<p class="lede">{esc(h["label"])} is a {esc((h["owner"] or "nursing").lower())} nursing facility in
{esc(h["city"])}, {esc(sname)}. Its CMS overall rating is <strong>{stars(h["ratings"]["Overall rating"])}</strong>.</p>
{table(["Field", "Value"], rows)}
<h2>CMS star ratings</h2>
{table(["Rating", "Stars"], rating_rows)}
<p>CMS rates health inspections, staffing and quality measures separately and combines them into the
overall rating. Read the components together: a facility with strong inspections but weak staffing
is a different risk than one with the reverse.</p>
<h2>Staffing and turnover</h2>
{('<table>' + ''.join(f'<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>' for a, b in staff_rows) + '</table>') if staff_rows else '<p>Staffing hours are not reported for this facility.</p>'}
<p>Higher nurse hours per resident per day generally mean more hands-on care; low turnover suggests
a more stable workforce. Weekend hours and RN hours matter most for clinical coverage.</p>
{('<h2>Flags and notes</h2><ul>' + ''.join(f'<li>{esc(f)}</li>' for f in flags) + '</ul>') if flags else ''}
{chain_html}
<h2>Location and contact</h2>
<p>{esc(h["label"])} is at {esc(h["address"])}, {esc(h["city"])}, {esc(h["state"])} {esc(h["zip"])}
{('in ' + esc(h["county"])) if h["county"] else ''}. Call <strong>{esc(h["phone"])}</strong> for
admissions and visits.</p>
<h2>Nearby nursing homes</h2>
{cards([(b["url"], esc(b["name"]), f'{d:,.1f} km · {esc(b["city"])} · {stars(b["ratings"]["Overall rating"])}') for d, b in near]) or "<p>—</p>"}
{related([(state_url[h["state"]], f"All nursing homes in {sname}"),
          (city_url.get((h["state"], h["city"])), f"Nursing homes in {h['city']}") if (h["state"], h["city"]) in city_pages else ("/search/", "Search facilities"),
          ("/guides/how-nursing-home-ratings-work/", "How the ratings work")])}
{faq([
    (f'What is the CMS rating of {h["label"]}?',
     (f'{esc(h["label"])} has an overall CMS rating of {stars(h["ratings"]["Overall rating"])}, with a '
      f'health inspection rating of {stars(h["ratings"]["Health inspection rating"])} and a staffing '
      f'rating of {stars(h["ratings"]["Staffing rating"])}.'
      if h["ratings"]["Overall rating"].isdigit() else
      f'{esc(h["label"])} is not currently rated by CMS.')),
    (f'How many beds does {h["label"]} have?',
     (f'It is certified for {esc(h["beds"])} beds and averages {esc(h["residents"] or "an unreported number of")} residents per day.'
      if h["beds"] else 'Bed count is not reported in the CMS file for this facility.')),
    (f'Who owns {h["label"]}?',
     f'It is a {esc((h["owner"] or "unreported").lower())} facility'
     + (f', part of the {esc(h["chain"])} chain' if h["chain"] else '') + '.'),
])}
"""
        s.add(h["url"], f'{h["label"]} — {h["city"]}, {h["state"]} | Ratings, Staffing & Contact',
              f'{h["label"]} in {h["city"]}, {h["state"]}: CMS overall rating '
              f'{stars(h["ratings"]["Overall rating"])}, staffing hours, ownership, beds and phone.',
              body, crumbs=[("States", "/#states"), (sname, state_url[h["state"]]), (h["label"], None)])

    s.add_file("/data/nursinghomes.json", json.dumps(
        [[h["name"], h["city"], h["state"], h["ratings"]["Overall rating"], h["url"]] for h in homes],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(homes))} Medicare/Medicaid-certified nursing homes "
                    f"from the CMS Provider Data Catalog (nursing home Provider Information, public "
                    f"domain). Star ratings, staffing hours, turnover and flags are reproduced as "
                    f"published by CMS. This site is informational; for care decisions consult the "
                    f"facility, your state's long-term care ombudsman and medical professionals.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/nursinghomes.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' facilities indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(h){return (h[0]+' '+h[1]+' '+h[2]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML = out.length ? '<div class="grid">'+out.slice(0,40).map(function(h){
      return '<a href="'+h[4]+'">'+esc(h[0])+' <span class="mut">'+esc(h[1])+', '+esc(h[2])+'</span></a>';
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
