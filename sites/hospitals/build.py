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

    # ---- national aggregates from the CMS file (guides + /stats/)
    def pct(x, y):
        return f"{100 * x / y:.0f}%" if y else "—"

    rated = [h for h in hospitals if h["rating"].isdigit()]
    n_high = sum(1 for h in rated if int(h["rating"]) >= 4)
    types = collections.Counter(h["type"] or "Unreported" for h in hospitals)
    owns = collections.Counter((h["owner"] or "Unreported").title() for h in hospitals)
    n_er = sum(1 for h in hospitals if h["emergency"])
    n_birth = sum(1 for h in hospitals if h["birthing"])
    st_rating = collections.defaultdict(list)
    for h in rated:
        st_rating[h["state"]].append(int(h["rating"]))
    st_avg = {st: sum(v) / len(v) for st, v in st_rating.items() if len(v) >= 10}
    top_rating = sorted(st_avg.items(), key=lambda kv: -kv[1])[:5]
    low_rating = sorted(st_avg.items(), key=lambda kv: kv[1])[:5]

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

    # ---- high-intent guide cluster: financial assistance / ER vs urgent care / choosing + stats
    s.add("/guides/hospital-financial-assistance/", "Hospital Financial Assistance and Charity Care",
          "How hospital financial aid works: the 501(r) charity-care rules for non-profit hospitals, "
          "how to apply, what documents you need, and how to negotiate a hospital bill.",
          """<h1>Hospital financial assistance and charity care</h1>
<p class="lede">Most non-profit hospitals are legally required to have a financial assistance
policy — and many patients never ask. If a hospital bill is unaffordable, apply in writing before
paying, not after collections start.</p>
<h2>The 501(r) rules (non-profit hospitals)</h2>
<p>Non-profit hospitals must maintain a written <strong>financial assistance policy</strong>, publish
a plain-language summary, and limit what they charge patients who qualify — often to no more than
the amount paid by insured patients (the "amounts generally billed" limit). They must also tell you
about the policy before and during collection efforts, and they generally cannot take extraordinary
collection actions without first checking whether you qualify.</p>
<h2>Who qualifies</h2>
<p>Policies set income limits as a percentage of the Federal Poverty Level; many cover households up
to 200–400% FPL, and some states and hospital systems go higher. Eligibility is usually based on
household income and size, sometimes with an asset test. Each hospital's policy is different —
read the policy document, not a verbal summary.</p>
<h2>How to apply</h2>
<ol>
<li>Ask the hospital's financial counselling or patient financial services department for the
<strong>financial assistance policy (FAP)</strong>, the plain-language summary and the application
form.</li>
<li>Request an <strong>itemised bill</strong> — not just the summary — and review it for errors.</li>
<li>Submit the application with proof of income (pay stubs, tax return, benefits letters) and any
other documents the policy requires. Keep copies and get a receipt or confirmation.</li>
<li>Ask for a hold on the account while the application is reviewed.</li>
<li>If denied, ask for the reason in writing and appeal; many denials are fixable
(missing documents, wrong income period).</li>
</ol>
<h2>If you do not qualify — or the hospital is for-profit</h2>
<p>Ask about interest-free payment plans, prompt-pay discounts (often 10–30% if paid quickly), a
reduced self-pay rate, and whether the bill qualifies for state charity-care or Medicaid assistance.
Compare the self-pay price with the amount insurers pay — the "gross charge" on the bill is rarely
what anyone pays. Medical debt-collection rules vary by state; get advice before signing anything
that admits liability.</p>
<h2>Get help</h2>
<p>State consumer-assistance offices, patient advocates, and non-profit medical-debt groups help with
appeals, often for free. Apply for Medicaid and hospital charity care <em>in parallel</em> — help
from one does not disqualify the other.</p>
{faq([
    ("Do hospitals have to offer financial assistance?",
     "Non-profit hospitals generally must have a written financial assistance policy with income-based "
     "discounts under IRS 501(r) rules. For-profit hospitals are not bound by those rules, but many still "
     "offer payment plans or discounts."),
    ("Can I apply for charity care after the bill is sent to collections?",
     "Often yes. The hospital must tell you about its policy during collections, and many allow "
     "applications later. Ask in writing and check the policy's deadline."),
    ("What is a prompt-pay discount?",
     "A reduction — often 10-30% — offered if a self-pay patient pays quickly or in full. It is separate "
     "from charity care and can sometimes be combined with a payment plan."),
])}""",
          crumbs=[("Guides", "/guides/"), ("Financial assistance", None)])

    s.add("/guides/emergency-room-vs-urgent-care/", "Emergency Room vs Urgent Care: Where to Go",
          "When to call 911, when to go to an emergency room, and what urgent care can handle — with "
          "the cost and coverage consequences of choosing wrong.",
          """<h1>Emergency room vs urgent care</h1>
<p class="lede">The emergency department is for conditions that could kill or permanently injure
you. Urgent care is for problems that need prompt attention but are not life-threatening. Choosing
wrong can mean hours of waiting or a bill many times larger.</p>
<h2>Call 911 or go to the emergency room for</h2>
<ul>
<li>Chest pain, pressure or squeezing; pain spreading to the arm, jaw or back</li>
<li>Signs of stroke — face drooping, arm weakness, trouble speaking, sudden confusion</li>
<li>Severe trouble breathing, choking, or blue lips</li>
<li>Severe bleeding that will not stop, or a serious head injury / loss of consciousness</li>
<li>Sudden severe abdominal pain, or vomiting blood</li>
<li>A severe allergic reaction with swelling or difficulty breathing</li>
<li>Serious burns, broken bones that pierce the skin, or a seizure that does not stop</li>
</ul>
<p>If you are unsure in a potentially life-threatening situation, call 911. Emergency departments
are required by federal law (EMTALA) to screen and stabilise emergency conditions regardless of
insurance or ability to pay — do not delay care over money.</p>
<h2>Urgent care usually handles</h2>
<ul>
<li>Sprains, strains and minor broken bones</li>
<li>Cuts needing stitches, minor burns and rashes</li>
<li>Ear pain, sore throat, sinus infections, urinary symptoms</li>
<li>Fever or flu symptoms without severe breathing trouble</li>
<li>Minor eye irritation, and some vaccinations and physicals</li>
</ul>
<p>Urgent care centres are usually faster and far cheaper than an ER for these problems, and many
accept insurance or offer self-pay rates. Call ahead to check hours, X-ray availability and network
status.</p>
<h2>The cost difference</h2>
<p>An emergency-department visit is coded at a much higher level than an urgent-care visit; the
same sprain can cost several times more at an ER. If you have insurance, check the copay for each
and use in-network facilities. If you are uninsured, ask each facility for its self-pay price before
you go where you have a choice.</p>
<h2>When in doubt</h2>
<p>Call your doctor or a nurse line. If the choice is between an ER and waiting at home with a
potentially serious symptom, go to the ER. Urgent care staff will send you to the ER if they find
something they cannot handle.</p>
{related([("/guides/hospital-financial-assistance/", "Help paying a hospital bill"),
          ("/guides/how-to-choose-a-hospital/", "How to choose a hospital"),
          ("/search/", "Find hospitals near you")])}""",
          crumbs=[("Guides", "/guides/"), ("ER vs urgent care", None)])

    s.add("/guides/how-to-choose-a-hospital/", "How to Choose a Hospital",
          "A practical guide to comparing hospitals with CMS data — rating and measure groups, "
          "emergency services, hospital type, network coverage and location — plus questions to ask.",
          f"""<h1>How to choose a hospital</h1>
<p class="lede">For planned care you often have a choice; for emergencies you do not. Use the data
here to plan, and use the nearest emergency department when it is urgent.</p>
<h2>1. Check the CMS rating and the five measure groups</h2>
<p>The overall star rating summarises mortality, safety, readmission, patient experience and
timeliness. Read the groups, not just the star: a hospital may be strong on outcomes and weak on
patient experience, or vice versa. Each hospital page shows whether each group is better than, no
different from, or worse than the national average.</p>
<h2>2. Match the hospital type to the care</h2>
<p>{human(len(hospitals))} hospitals are in this directory. Acute-care hospitals handle most
inpatient and emergency care; critical access hospitals serve rural areas with limited beds;
children's, psychiatric, rehabilitation and long-term care hospitals specialise. Confirm the
hospital offers the service you need before travelling.</p>
<h2>3. Check emergency and specialty services</h2>
<p>Not every hospital has an emergency department ({pct(n_er, len(hospitals))} here do) or meets the
CMS birthing-friendly criteria ({pct(n_birth, len(hospitals))}). If emergency care or maternity care
matters, filter for it on the hospital page.</p>
<h2>4. Check network and cost</h2>
<p>Insurance networks matter as much as quality: an out-of-network hospital can cost far more.
Confirm the hospital is in your plan's network before booking elective care, and ask for an
estimate of your share. If you are uninsured, ask about financial assistance before care — see
<a href="/guides/hospital-financial-assistance/">hospital financial assistance</a>.</p>
<h2>5. Ask these questions</h2>
<ul>
<li>How many of these procedures does the hospital do each year?</li>
<li>Who will be my surgeon or attending, and what is their experience?</li>
<li>What are the hospital's infection and readmission rates for my condition?</li>
<li>What is the plan for discharge and follow-up?</li>
</ul>
{related([("/guides/what-is-the-cms-hospital-rating/", "What the CMS rating measures"),
          ("/guides/hospital-types-explained/", "Hospital types explained"),
          ("/stats/", "US hospital statistics")])}""",
          crumbs=[("Guides", "/guides/"), ("Choosing a hospital", None)])

    # ---- national statistics page
    type_rows = "".join(f"<tr><td>{esc(k)}</td><td>{human(v)}</td><td>{pct(v, len(hospitals))}</td></tr>"
                        for k, v in types.most_common())
    own_rows = "".join(f"<tr><td>{esc(k)}</td><td>{human(v)}</td><td>{pct(v, len(hospitals))}</td></tr>"
                       for k, v in owns.most_common())
    st_rows = "".join(
        f'<tr><td><a href="{state_url[st]}">{esc(STATE_NAMES.get(st, st))}</a></td><td>{v:.2f}</td></tr>'
        for st, v in top_rating)
    st_rows_low = "".join(
        f'<tr><td><a href="{state_url[st]}">{esc(STATE_NAMES.get(st, st))}</a></td><td>{v:.2f}</td></tr>'
        for st, v in low_rating)
    s.add("/stats/", "US Hospital Statistics — Ratings, Types, Ownership, Emergency Services",
          f"National statistics from the CMS hospital file: {human(len(hospitals))} hospitals, "
          f"ratings, hospital types, ownership, emergency and birthing services, and state tables.",
          f"""<h1>US hospital statistics</h1>
<p class="lede">Original summary statistics computed from the CMS Provider Information file for the
<strong>{human(len(hospitals))}</strong> hospitals in this directory.</p>
<h2>National overview</h2>
<table>
<tr><td>Hospitals</td><td>{human(len(hospitals))}</td></tr>
<tr><td>States and territories</td><td>{human(len(by_state))}</td></tr>
<tr><td>Rated by CMS</td><td>{human(len(rated))} ({pct(len(rated), len(hospitals))})</td></tr>
<tr><td>Rated 4 or 5 stars</td><td>{pct(n_high, len(rated))}</td></tr>
<tr><td>With emergency services</td><td>{pct(n_er, len(hospitals))}</td></tr>
<tr><td>Meeting CMS birthing-friendly criteria</td><td>{pct(n_birth, len(hospitals))}</td></tr>
</table>
<h2>Hospital types</h2>
<table><tr><th>Type</th><th>Hospitals</th><th>Share</th></tr>{type_rows}</table>
<h2>Ownership</h2>
<table><tr><th>Ownership</th><th>Hospitals</th><th>Share</th></tr>{own_rows}</table>
<h2>States with the highest average CMS rating (≥10 rated hospitals)</h2>
<table><tr><th>State</th><th>Average rating</th></tr>{st_rows}</table>
<h2>States with the lowest average CMS rating (≥10 rated hospitals)</h2>
<table><tr><th>State</th><th>Average rating</th></tr>{st_rows_low}</table>
<p class="mut">Averages are computed from the CMS published file and are not risk-adjusted; use them
as context, not as hospital verdicts.</p>
{notice("Data: CMS Provider Data Catalog, Hospital General Information (public domain), reproduced "
        "as published. Not medical advice.")}""",
          crumbs=[("Statistics", None)])

    s.add("/guides/", "Guides — US Hospitals",
          "Explainers on CMS hospital ratings, hospital types, financial assistance, choosing a "
          "hospital and ER versus urgent care — plus national statistics.",
          "<h1>Guides</h1><p class=\"lede\">Plain explainers for the questions patients actually ask.</p>"
          + cards([("/guides/what-is-the-cms-hospital-rating/", "What is the CMS hospital star rating?",
                    "How the 1–5 rating is built and why some hospitals are unrated."),
                   ("/guides/hospital-types-explained/", "Hospital types and ownership explained",
                    "Acute care, critical access, specialty hospitals and ownership categories."),
                   ("/guides/hospital-financial-assistance/", "Financial assistance and charity care",
                    "How non-profit hospitals must help, and how to apply."),
                   ("/guides/emergency-room-vs-urgent-care/", "ER vs urgent care",
                    "When to call 911, when urgent care is enough, and the cost difference."),
                   ("/guides/how-to-choose-a-hospital/", "How to choose a hospital",
                    "Ratings, measure groups, services, network and the questions to ask."),
                   ("/stats/", "US hospital statistics",
                    "Types, ownership, ratings and services computed from CMS data.")]),
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
    titles_used = set()
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
{health_cross_links(h["state"], "hospitals")}
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
        title = seo_title(h["label"], f' — {h["city"]}, {h["state"]}')
        if title in titles_used:
            title = seo_title(f'{h["label"]} ({h["id"]})', f' — {h["city"]}')
        if title in titles_used:
            title = f'{h["label"][:40].rstrip()} — {h["id"]}'
        titles_used.add(title)
        s.add(h["url"], title,
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
