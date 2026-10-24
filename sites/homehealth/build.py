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

    # ---- national aggregates from the CMS file (used by the guides + /stats/ page)
    def pct(x, y):
        return f"{100 * x / y:.0f}%" if y else "—"

    rated = [a for a in agencies if a["rating"].isdigit()]
    n_high = sum(1 for a in rated if int(a["rating"]) >= 4)
    own = collections.Counter((a["owner"] or "Unreported").title() for a in agencies)
    svc = collections.Counter(s for a in agencies for s in a["services"])
    cert_years = collections.Counter(
        a["cert_date"].split("/")[-1] for a in agencies if "/" in a["cert_date"]
    )
    st_rating = collections.defaultdict(list)
    for a in rated:
        st_rating[a["state"]].append(int(a["rating"]))
    st_avg = {st: sum(v) / len(v) for st, v in st_rating.items() if len(v) >= 20}
    top_rating = sorted(st_avg.items(), key=lambda kv: -kv[1])[:5]
    low_rating = sorted(st_avg.items(), key=lambda kv: kv[1])[:5]
    n_since2020 = sum(c for y, c in cert_years.items() if y.isdigit() and int(y) >= 2020)
    n_1990s = sum(c for y, c in cert_years.items() if y.isdigit() and 1990 <= int(y) <= 1999)
    n_pre1990 = sum(c for y, c in cert_years.items() if y.isdigit() and int(y) < 1990)

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

    # ---- high-intent guide cluster: Medicare coverage / comparison / choosing / statistics
    s.add("/guides/medicare-home-health-coverage/", "Does Medicare Cover Home Health Care?",
          "Medicare home-health eligibility in plain English: the homebound rule, skilled intermittent "
          "need, the face-to-face requirement, what you pay (and do not pay), and what Medicare will "
          "not cover.",
          """<h1>Does Medicare cover home health care?</h1>
<p class="lede">Usually yes — if you are homebound and need skilled care intermittently. It is one
of the most misunderstood benefits because "home care" and "home health" sound the same and are
paid for very differently.</p>
<h2>The five conditions</h2>
<p>Original Medicare pays for home health when <strong>all</strong> of these are true:</p>
<ul>
<li>A doctor certifies you need <strong>skilled care intermittently</strong> — nursing or therapy
that only licensed professionals can provide.</li>
<li>You are <strong>homebound</strong>: leaving home takes considerable effort or the help of
another person or equipment.</li>
<li>A doctor has a <strong>face-to-face</strong> encounter with you (in person or by telehealth in
some cases) within the required window before the plan of care starts.</li>
<li>A <strong>plan of care</strong> is established and reviewed regularly.</li>
<li>The agency is <strong>Medicare-certified</strong> — every agency in this directory is.</li>
</ul>
<h2>What you pay</h2>
<p>Original Medicare pays <strong>100% of covered home-health services</strong> — there is no
coinsurance and no deductible for the visits. Equipment such as a hospital bed or walker, if
covered, carries the usual 20% coinsurance for durable medical equipment. You may owe for services
that are not medically necessary or not covered.</p>
<h2>What is not covered</h2>
<p>Medicare does not pay for <strong>24-hour care</strong>, <strong>custodial care</strong> (help
with bathing, dressing, meals when that is the main need), or homemaker services. Those are
private-pay, long-term-care-insurance or, in some cases, Medicaid waiver services. If the need is
mostly companionship or supervision, Medicare home health is not the right benefit.</p>
<h2>Medicare Advantage</h2>
<p>If you have a Medicare Advantage plan, home health is a covered benefit, but the plan may have
its own network of agencies and prior-authorisation rules. Ask the plan which agencies are
in-network before choosing one.</p>
<h2>How to start</h2>
<p>You do not have to be discharged from a hospital to use home health, although it is common
then. Ask your doctor for a home-health referral and an order, choose a Medicare-certified agency
(check its CMS rating and services in this directory), and ask the agency to confirm in writing
what Medicare will cover before care starts.</p>
{faq([
    ("Is home health care covered by Medicare?",
     "Yes, when you are homebound and a doctor certifies you need skilled, intermittent care, and "
     "the agency is Medicare-certified. Original Medicare pays 100% of covered visits."),
    ("What does homebound mean for Medicare?",
     "Leaving home requires considerable effort or the help of another person or equipment. Short, "
     "occasional absences (medical appointments, religious services) can still qualify."),
    ("Does Medicare pay for 24-hour home care?",
     "No. Medicare home health is intermittent skilled care. Around-the-clock or custodial care is "
     "not covered."),
])}""",
          crumbs=[("Guides", "/guides/"), ("Medicare coverage", None)])

    s.add("/guides/home-health-vs-home-care/", "Home Health vs Home Care: What's the Difference?",
          "Skilled Medicare-paid home health versus private-pay home care — what each provides, who "
          "qualifies, what you pay, and how to know which one you need.",
          """<h1>Home health vs home care</h1>
<p class="lede">One is medical and often paid by Medicare; the other is help with daily living and
paid privately. Families mix them up constantly, and the mistake is expensive.</p>
<h2>Home health</h2>
<p><strong>Skilled, intermittent care ordered by a doctor</strong>: nursing (wound care,
injections, medication management, education), physical, occupational and speech therapy, medical
social services. Delivered by a Medicare-certified agency, usually for weeks or months after a
hospital stay or a change in condition. Original Medicare pays 100% of covered services when the
homebound and skilled-need rules are met; the visits stop when skilled need ends.</p>
<h2>Home care</h2>
<p><strong>Non-medical help with daily living</strong>: bathing, dressing, meals, medication
reminders, companionship, supervision, help around the house. Delivered by home-care aides or
companions, billed hourly by a private agency or directly. Medicare does not pay for it when
that is the main need. It is paid privately, by long-term care insurance, or through Medicaid
waiver programs in some states.</p>
<h2>What it costs</h2>
<p>CareScout's 2025 Cost of Care Survey puts the national median for a home health aide at about
<strong>$35 an hour</strong>. Forty hours a week of that is roughly <strong>$6,000 a month</strong> —
which is why the amount of care needed matters as much as the hourly rate. Skilled home-health
visits covered by Medicare carry no coinsurance.</p>
<h2>Which do you need?</h2>
<p>If there is a medical need a nurse or therapist must handle — a wound, an infusion, therapy
after an injury — it is home health; ask the doctor for an order and a Medicare-certified agency.
If the need is safety, supervision and help with daily activities, it is home care; budget hours
and plan the money (private pay, LTC insurance, VA benefits, or a state Medicaid programme).</p>
{related([("/guides/medicare-home-health-coverage/", "Medicare home health eligibility"),
          ("/guides/choosing-a-home-health-agency/", "How to choose an agency"),
          ("/stats/", "US home health statistics")])}""",
          crumbs=[("Guides", "/guides/"), ("Home health vs home care", None)])

    s.add("/guides/choosing-a-home-health-agency/", "How to Choose a Home Health Agency",
          "A practical checklist: CMS star rating and measures, services offered, ownership, "
          f"certification age, after-hours coverage and the questions that reveal good care — using "
          f"data from {human(len(agencies))} agencies.",
          f"""<h1>How to choose a home health agency</h1>
<p class="lede">The stars narrow the list; the questions decide. Use the CMS data on agency pages,
then ask these questions before you sign a plan of care.</p>
<h2>1. Check the star rating and the individual measures</h2>
<p>CMS rates agencies 1–5 on quality-of-patient-care measures. Do not stop at the star: read the
measures beside it. Most informative are <strong>improvement in walking</strong>, <strong>improvement
in bathing</strong>, <strong>timely initiation of care</strong> and <strong>discharge to the
community</strong>. For hospitalisation and emergency-department rates, lower is better.</p>
<h2>2. Check the services you will need</h2>
<p>Not every agency offers every service. Filter agency pages by nursing, physical therapy,
occupational therapy, speech pathology, medical social services and home-health aide services.
If the family needs a specialist service, confirm it is offered before starting.</p>
<h2>3. Check ownership and experience</h2>
<p>Agency pages show ownership (proprietary, non-profit, government) and the date the agency was
first certified. Neither decides quality by itself — but a long certification history and a stable
local organisation are useful context. CMS flags ownership changes separately where reported.</p>
<h2>4. Ask these questions</h2>
<ul>
<li>Which nurse or therapist will usually come, and can that stay consistent?</li>
<li>Who answers the phone after hours and at weekends?</li>
<li>What happens if I need a visit urgently — how fast is the response?</li>
<li>How do you coordinate with my doctor, and how will I know the plan is changing?</li>
<li>What will Medicare cover, and what will I be billed for?</li>
<li>How do you handle hospital admissions or emergencies?</li>
</ul>
<h2>5. Confirm the paperwork</h2>
<p>The agency must provide you written information about your care plan, rights and billing. Keep
the Medicare "Advance Beneficiary Notice" every time it is offered — it tells you what might not
be covered before you receive it.</p>
{related([("/guides/medicare-home-health-coverage/", "Medicare coverage rules"),
          ("/guides/home-health-star-rating-explained/", "What the star rating measures"),
          ("/search/", "Search agencies near you")])}""",
          crumbs=[("Guides", "/guides/"), ("Choosing an agency", None)])

    # ---- national statistics page
    svc_rows = "".join(f"<tr><td>{esc(name)}</td><td>{human(n)}</td><td>{pct(n, len(agencies))}</td></tr>"
                       for name, n in svc.most_common())
    own_rows = "".join(f"<tr><td>{esc(k)}</td><td>{human(v)}</td><td>{pct(v, len(agencies))}</td></tr>"
                       for k, v in own.most_common())
    st_rows = "".join(
        f'<tr><td><a href="{state_url[st]}">{esc(STATE_NAMES.get(st, st))}</a></td><td>{v:.2f}</td></tr>'
        for st, v in top_rating)
    st_rows_low = "".join(
        f'<tr><td><a href="{state_url[st]}">{esc(STATE_NAMES.get(st, st))}</a></td><td>{v:.2f}</td></tr>'
        for st, v in low_rating)
    s.add("/stats/", "US Home Health Statistics — Agencies, Ratings, Services, Ownership",
          f"National statistics from the CMS home-health file: {human(len(agencies))} agencies, "
          f"ratings, services offered, ownership, certification history and state comparison tables.",
          f"""<h1>US home health statistics</h1>
<p class="lede">Original summary statistics computed from the CMS Provider Information file for the
<strong>{human(len(agencies))}</strong> Medicare-certified home-health agencies in this directory.</p>
<h2>National overview</h2>
<table>
<tr><td>Home-health agencies</td><td>{human(len(agencies))}</td></tr>
<tr><td>States and territories</td><td>{human(len(by_state))}</td></tr>
<tr><td>Agencies with a star rating</td><td>{human(len(rated))} ({pct(len(rated), len(agencies))})</td></tr>
<tr><td>Rated 4 or 5 stars</td><td>{pct(n_high, len(rated))}</td></tr>
<tr><td>Certified in 2020 or later</td><td>{pct(n_since2020, len(agencies))}</td></tr>
<tr><td>Certified before 1990</td><td>{pct(n_pre1990, len(agencies))}</td></tr>
</table>
<h2>Services offered (share of agencies reporting "yes")</h2>
<table><tr><th>Service</th><th>Agencies</th><th>Share</th></tr>{svc_rows}</table>
<h2>Ownership</h2>
<table><tr><th>Ownership type</th><th>Agencies</th><th>Share</th></tr>{own_rows}</table>
<h2>States with the highest average star rating (≥20 rated agencies)</h2>
<table><tr><th>State</th><th>Average rating</th></tr>{st_rows}</table>
<h2>States with the lowest average star rating (≥20 rated agencies)</h2>
<table><tr><th>State</th><th>Average rating</th></tr>{st_rows_low}</table>
<p class="mut">Averages are computed from the CMS published file and are not risk-adjusted; use them
as context, not as agency verdicts.</p>
{notice("Data: CMS Provider Data Catalog, Home Health Care Agencies (public domain), reproduced as "
        "published. Not medical advice.")}""",
          crumbs=[("Statistics", None)])

    s.add("/guides/", "Guides — US Home Health",
          "Explainers on home health care, Medicare coverage and choosing an agency — plus "
          "statistics computed from the CMS data behind this directory.",
          "<h1>Guides</h1><p class=\"lede\">Plain explainers for the questions families actually ask.</p>"
          + cards([("/guides/how-home-health-works/", "How home health works",
                    "Services, Medicare eligibility and what to ask an agency."),
                   ("/guides/home-health-star-rating-explained/", "The CMS star rating explained",
                    "What the rating measures and how to read the individual quality measures."),
                   ("/guides/medicare-home-health-coverage/", "Does Medicare cover home health?",
                    "Homebound rule, skilled need, what you pay and what is not covered."),
                   ("/guides/home-health-vs-home-care/", "Home health vs home care",
                    "Skilled Medicare-paid care versus private-pay help at home."),
                   ("/guides/choosing-a-home-health-agency/", "How to choose an agency",
                    "The checklist: ratings, measures, services and the questions to ask."),
                   ("/stats/", "US home health statistics",
                    "Agencies, services, ownership and state comparisons from CMS data.")]),
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
    titles_used = set()
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
{health_cross_links(a["state"], "homehealth")}
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
        title = seo_title(a["label"], f' — {a["city"]}, {a["state"]}')
        if title in titles_used:
            title = seo_title(f'{a["label"]} ({a["ccn"]})', f' — {a["city"]}')
        if title in titles_used:
            title = f'{a["label"][:40].rstrip()} — {a["ccn"]}'
        titles_used.add(title)
        s.add(a["url"], title,
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
