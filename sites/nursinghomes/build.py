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

    # ---- national aggregates computed from the CMS file (used by the guides + /stats/ page)
    def numf(v):
        try:
            return float(str(v).replace(",", "").strip())
        except Exception:
            return None

    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else 0.0

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    def pct(a, b):
        return f"{100 * a / b:.0f}%" if b else "—"

    rated = [h for h in homes if h["ratings"]["Overall rating"].isdigit()]
    n_high = sum(1 for h in rated if int(h["ratings"]["Overall rating"]) >= 4)
    n_abuse = sum(1 for h in homes if h["abuse"])
    n_focus = sum(1 for h in homes if h["special_focus"])
    beds_v = [x for x in (numf(h["beds"]) for h in homes) if x]
    res_v = [x for x in (numf(h["residents"]) for h in homes) if x]
    staff_v = [x for x in (numf(h["staff_total"]) for h in homes) if x]
    rn_v = [x for x in (numf(h["staff_rn"]) for h in homes) if x]
    wk_v = [x for x in (numf(h["staff_weekend"]) for h in homes) if x]
    to_v = [x for x in (numf(h["turnover_total"]) for h in homes) if x]
    rtn_v = [x for x in (numf(h["turnover_rn"]) for h in homes) if x]
    own = collections.Counter((h["owner"] or "Unreported") for h in homes)
    chain_homes = [h for h in homes if h["chain"]]
    n_sprink = sum(1 for h in homes if h["sprinklers"])
    n_council = sum(1 for h in homes if h["council"])
    # state staffing/ratings extremes (>= 20 facilities so single facilities do not distort)
    st_staff = collections.defaultdict(list)
    st_rating = collections.defaultdict(list)
    for h in homes:
        v = numf(h["staff_total"])
        if v:
            st_staff[h["state"]].append(v)
        if h["ratings"]["Overall rating"].isdigit():
            st_rating[h["state"]].append(int(h["ratings"]["Overall rating"]))
    st_staff = {s: mean(v) for s, v in st_staff.items() if len(v) >= 20}
    st_rating = {s: mean(v) for s, v in st_rating.items() if len(v) >= 20}
    top_staff = sorted(st_staff.items(), key=lambda kv: -kv[1])[:5]
    low_staff = sorted(st_staff.items(), key=lambda kv: kv[1])[:5]
    top_rating = sorted(st_rating.items(), key=lambda kv: -kv[1])[:5]
    low_rating = sorted(st_rating.items(), key=lambda kv: kv[1])[:5]
    top_chains = collections.Counter(h["chain"] for h in chain_homes).most_common(10)

    # ---- CareScout 2025 cost-of-care medians by state (see sites/nursinghomes/fetch_costs.py)
    COSTS = json.loads((CACHE / "carescout-costs.json").read_text(encoding="utf-8"))
    cost_nat = COSTS["national"]
    cost_states = COSTS["states"]
    cost_url = {st: f"/costs/{slug(STATE_NAMES[st])}/" for st in by_state
                if STATE_NAMES.get(st) in cost_states}

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
             nav=[("Search", "/search/"), ("States", "/#states"), ("Ratings", "/#ratings"),
                  ("Costs", "/costs/"), ("Guides", "/guides/")],
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

    # ---- high-intent guide cluster (payment / coverage / comparison / staffing / stats)
    s.add("/guides/paying-for-nursing-home-care/", "How to Pay for Nursing Home Care",
          "What nursing home care costs nationally, the payment sources that cover it "
          "(Medicare, Medicaid, VA, long-term care insurance, private pay) and the order to "
          "use them in.",
          f"""<h1>How to pay for nursing home care</h1>
<p class="lede">Nursing home care is the most expensive form of long-term care. Most families
combine several payment sources over time — almost nobody pays the whole bill from one place.</p>
<h2>What it costs</h2>
<p>CareScout's 2025 Cost of Care Survey puts the <strong>national median</strong> at
<strong>$315 a day</strong> for a semi-private room — about <strong>$9,581 a month</strong> or
<strong>$114,975 a year</strong> — and <strong>$355 a day</strong> for a private room
(<strong>$10,798 a month</strong>, <strong>$129,575 a year</strong>). Costs vary widely by state
and city; the {human(len(homes))} facilities in this directory show the spread, and a facility's
own admissions office is the only authoritative quote.</p>
<h2>The payment sources, in the order families usually use them</h2>
<p><strong>1. Private pay.</strong> Savings, pension income, the proceeds of selling a home, and
family contributions. This is how most people start. A facility will ask for a financial
disclosure and may require a deposit.</p>
<p><strong>2. Medicare — short-term skilled care only.</strong> Part A can pay for up to
<strong>100 days per benefit period</strong> of <em>skilled</em> nursing facility care after a
qualifying hospital stay, with coinsurance after day 20. Medicare does <strong>not</strong> pay for
custodial long-term care. See <a href="/guides/medicare-and-nursing-homes/">does Medicare cover
nursing home care</a>.</p>
<p><strong>3. Medicaid — the long-term-care payer of last resort.</strong> For people who meet
their state's income and asset limits, Medicaid covers long-term custodial nursing home care in
certified facilities. It is means-tested and state-specific; see
<a href="/guides/medicaid-and-nursing-homes/">Medicaid and nursing homes</a>.</p>
<p><strong>4. Long-term care insurance.</strong> If a policy was bought years ago, it may pay a
daily or monthly benefit after an elimination period. Check the policy's benefit period,
inflation protection and whether it pays for nursing home care only or also home care.</p>
<p><strong>5. Veterans benefits.</strong> The VA has community living centres, state veterans
homes and the Aid &amp; Attendance allowance for eligible wartime veterans and surviving spouses.
Apply through the VA, not the facility.</p>
<p><strong>6. Other assets.</strong> Life insurance with a long-term care rider, hybrid
life/LTC policies, annuities with LTC benefits, a reverse mortgage, or the sale of a home. Get
independent financial advice before cashing in policies — the tax and benefit consequences
matter.</p>
<h2>How to choose the order</h2>
<p>Start with what the person needs clinically (skilled rehabilitation versus custodial care), then
check Medicare eligibility for the short term, then plan the long term with Medicaid/insurance/VA
in mind. Ask the facility's admissions director which payers they accept — most accept Medicaid,
but bed availability for Medicaid patients can differ. Apply for Medicaid <em>before</em> the
money runs out; retroactive coverage is limited.</p>
<h2>Watch out for</h2>
<p>Facilities are not allowed to require a "Medicaid bed" deposit in most states, but they can ask
for a private-pay commitment for a period. Get every commitment in writing. Keep records of every
payment, policy and application — appeals are common and documentation wins them.</p>
{faq([
    ("Does Medicare pay for long-term nursing home care?",
     "No. Medicare covers short-term skilled nursing facility care (up to 100 days per benefit "
     "period) after a qualifying hospital stay, not custodial long-term care."),
    ("What is the national median cost of a semi-private nursing home room?",
     "About $315 a day, or roughly $114,975 a year, according to CareScout's 2025 Cost of Care Survey."),
    ("Can I pay for a nursing home with Medicaid?",
     "Yes, if the person meets the state's income and asset limits and the facility is Medicaid-certified. "
     "Rules vary by state."),
])}""",
          crumbs=[("Guides", "/guides/"), ("Paying for care", None)])

    s.add("/guides/medicare-and-nursing-homes/", "Does Medicare Cover Nursing Home Care?",
          "Medicare's skilled nursing facility benefit explained: the 100-day limit, the 3-day "
          "hospital rule, 2026 coinsurance, skilled versus custodial care, and what happens when "
          "coverage ends.",
          """<h1>Does Medicare cover nursing home care?</h1>
<p class="lede">Usually only for a short, skilled stay — and never for long-term custodial care.
That distinction decides most of the money questions families bring to a nursing home.</p>
<h2>The short answer</h2>
<p>Medicare Part A pays for up to <strong>100 days of skilled nursing facility (SNF) care per
benefit period</strong> if you had a qualifying inpatient hospital stay, but it covers
<strong>custodial care — help with daily living — not at all</strong>. Long-term nursing home
residents are typically covered by Medicaid or private funds instead.</p>
<h2>What qualifies</h2>
<ul>
<li>An inpatient hospital stay of at least <strong>3 consecutive days</strong> (observation status
does not count).</li>
<li>Admission to a Medicare-certified SNF within <strong>30 days</strong> of discharge.</li>
<li>A doctor orders <strong>skilled care</strong> (nursing, rehabilitation) on a daily basis, and
the facility certifies it is medically necessary.</li>
</ul>
<h2>What Medicare pays</h2>
<p>In 2026, days <strong>1–20</strong> are covered in full after the Part A hospital deductible.
Days <strong>21–100</strong> carry coinsurance of about <strong>$217 a day</strong>. Coverage is
per benefit period — it resets after 60 days out of hospital care. Check the current figures at
Medicare.gov, and note that a Medicare Advantage plan can set its own SNF rules and network.</p>
<h2>Skilled care versus custodial care</h2>
<p><strong>Skilled care</strong> means services that only licensed nurses or therapists can
provide: wound care, intravenous medication, physical or speech therapy after a stroke or
fracture. <strong>Custodial care</strong> is help with eating, dressing, bathing, toileting and
supervision. Custodial care is what most long-stay nursing home residents need — and it is the
part Medicare does not pay for.</p>
<h2>When Medicare stops paying</h2>
<p>Coverage ends when the person's condition stops improving, when skilled services are no longer
needed, or at 100 days. Options then: Medicaid if eligible, long-term care insurance, VA benefits,
or private pay. Ask the facility's social worker to start the next application early.</p>
{faq([
    ("Does Medicare pay for nursing home care?",
     "Only for short-term skilled care — up to 100 days per benefit period after a qualifying "
     "hospital stay. Medicare does not pay for long-term custodial care."),
    ("How many days will Medicare pay for a skilled nursing facility?",
     "Up to 100 days per benefit period: days 1-20 are fully covered, days 21-100 have daily "
     "coinsurance (about $217 a day in 2026)."),
    ("What is the 3-day rule?",
     "Medicare requires at least a 3-consecutive-day inpatient hospital stay before it will pay "
     "for the SNF stay, and admission within 30 days of discharge."),
])}""",
          crumbs=[("Guides", "/guides/"), ("Medicare", None)])

    s.add("/guides/medicaid-and-nursing-homes/", "Medicaid and Nursing Homes: How Coverage Works",
          "How Medicaid pays for long-term nursing home care: eligibility limits, the look-back "
          "period, spend-down, spousal protections, and how to apply in your state.",
          """<h1>Medicaid and nursing homes: how coverage works</h1>
<p class="lede">Medicaid is the largest payer of long-term nursing home care in the United States.
It is available only to people who meet both a <em>medical eligibility</em> and a
<em>financial eligibility</em> test — but it pays for custodial care that Medicare does not.</p>
<h2>What Medicaid covers</h2>
<p>For eligible residents, Medicaid covers nursing facility services in participating facilities,
including custodial care (help with daily living), which is the part Medicare excludes. Most, but
not all, nursing homes in this directory are certified to accept Medicaid.</p>
<h2>Medical eligibility</h2>
<p>States generally require that the person needs a nursing-facility level of care — assessed by
the state's functional assessment, not by the facility. Contact your state Medicaid agency for the
assessment.</p>
<h2>Financial eligibility</h2>
<p>Limits on income and countable assets are set by each state, within federal rules. A home is
often not counted if a spouse still lives there, subject to an equity limit. Some income can be
diverted to a community spouse; 2026 federal rules set the minimum and maximum monthly
maintenance needs allowance for spouses. Because the numbers change yearly and vary by state,
always check with that state's Medicaid office before planning.</p>
<h2>The five-year look-back</h2>
<p>When you apply, states review <strong>five years</strong> of asset transfers. Gifts and
below-market sales made in that window can cause a period of ineligibility, calculated by
dividing the transferred value by the state's average daily nursing home rate. Keep records of
every large transaction. Some transfers are exempt (for example, to certain family members or for
fair-market value).</p>
<h2>Spend-down and planning</h2>
<p>If income or assets are slightly above the limit, a "spend-down" (medical expense deduction)
process may allow eligibility. An elder-law attorney can explain state options — but beware of
advisors who suggest hiding assets, which can itself trigger penalties.</p>
<h2>How to apply</h2>
<p>Apply through the state Medicaid agency or the county office, not the nursing home (the facility
can help with paperwork). Start before assets are exhausted; processing can take weeks. Once
approved, a redetermination is usually required annually.</p>
{faq([
    ("Does Medicaid pay for nursing home care?",
     "Yes, for people who meet their state's income and asset limits and need nursing-facility-level care. "
     "Medicaid covers custodial care that Medicare does not."),
    ("What is the 5-year look-back?",
     "Medicaid reviews five years of asset transfers before approval. Undisclosed gifts or below-market "
     "transfers can cause a period of ineligibility."),
    ("Can I keep my home if my spouse enters a nursing home?",
     "Often yes, when a spouse still lives there, subject to the state's equity limit and rules. Rules vary "
     "by state."),
])}""",
          crumbs=[("Guides", "/guides/"), ("Medicaid", None)])

    s.add("/guides/nursing-home-vs-home-care-vs-assisted-living/",
          "Nursing Home vs Home Care vs Assisted Living: What Is the Difference?",
          "A plain comparison of nursing homes, assisted living, memory care, home care and home "
          "health — what each provides, who pays, and how to know which is needed.",
          f"""<h1>Nursing home vs home care vs assisted living</h1>
<p class="lede">People use these words interchangeably, but they describe very different levels of
care and different payment rules. Getting the setting wrong is the most expensive mistake families
make.</p>
<h2>The settings, briefly</h2>
<table>
<tr><td><strong>Nursing home</strong></td><td>24/7 skilled nursing and custodial care; clinical
supervision, medication management, therapy. Medicare-certified facilities are in this directory.</td></tr>
<tr><td><strong>Assisted living</strong></td><td>Housing with help for daily activities — meals,
housekeeping, bathing, medication reminders. Not skilled nursing; most residents do not need
round-the-clock clinical care.</td></tr>
<tr><td><strong>Memory care</strong></td><td>Specialised assisted living for dementia, with secured
areas and dementia-trained staff. Often a unit inside a nursing home or assisted-living
community.</td></tr>
<tr><td><strong>Home care</strong></td><td>Non-medical help at home: companionship, bathing,
dressing, meals. Paid privately or through long-term care insurance; usually hourly.</td></tr>
<tr><td><strong>Home health</strong></td><td>Skilled services at home — nursing, physical therapy,
wound care — covered short-term by Medicare when homebound and medically necessary.</td></tr>
<tr><td><strong>CCRC / life plan</strong></td><td>Campus offering independent living through
nursing care; entry fees and contracts vary.</td></tr>
</table>
<h2>Cost comparison</h2>
<p>For national context, CareScout's 2025 Cost of Care Survey reports a median of about
<strong>$114,975 a year</strong> for a semi-private nursing home room and about
<strong>$6,200 a month</strong> for assisted living, with home care billed hourly and depending on
the hours needed. The {human(len(homes))} facilities in this directory can be filtered by state and
city to compare local options.</p>
<h2>Who pays</h2>
<p>Medicare pays only for <em>skilled</em> care — a short nursing home stay or home health — not
for custodial care. Medicaid pays long-term nursing home care for people who qualify financially.
Private pay, long-term care insurance and VA benefits fill the middle. Assisted living is almost
always private pay unless a state offers a Medicaid waiver.</p>
<h2>How to decide</h2>
<p>Match the setting to the <strong>clinical need and the hours of supervision required</strong>,
then to the money. If the person needs 24/7 nursing or can no longer be safely left alone, a
nursing home may be the only safe setting. If the need is help with daily living and safety, home
care or assisted living may be enough. Reassess regularly — needs change.</p>
{related([("/guides/medicare-and-nursing-homes/", "Medicare versus custodial care"),
          ("/guides/paying-for-nursing-home-care/", "How to pay for care"),
          ("/guides/how-to-choose-a-nursing-home/", "How to choose a nursing home")])}""",
          crumbs=[("Guides", "/guides/"), ("Care settings", None)])

    s.add("/guides/nursing-home-staffing-and-turnover/",
          "Nursing Home Staffing Hours and Turnover: How to Read Them",
          f"What CMS staffing hours per resident per day mean, the national medians computed from "
          f"{human(len(homes))} facilities, why RN hours and weekend hours matter, and how to read "
          f"turnover numbers.",
          f"""<h1>Nursing home staffing hours and turnover</h1>
<p class="lede">Staffing is the part of the CMS data most directly linked to daily experience — and
the easiest to misread. Here is what the numbers mean, with national medians computed from the
{human(len(homes))} facilities in this directory.</p>
<h2>Staffing hours per resident per day</h2>
<p>CMS reports how many hours of care each facility's residents receive per day, split into nurse
aides, licensed practical nurses (LPNs) and registered nurses (RNs). The <strong>total nurse
staffing</strong> figure is the sum. In this data the median facility reports about
<strong>{med(staff_v):.2f} total nurse hours per resident per day</strong>, including
<strong>{med(rn_v):.2f} RN hours</strong>; on weekends the median is about
<strong>{med(wk_v):.2f} total hours</strong>. Facilities below the median deserve extra questions
about nights and weekends.</p>
<h2>Why RN hours matter</h2>
<p>RNs assess changes in condition, manage medications and supervise aides. A facility can have a
high total hour count dominated by aide hours and still be thin on RN coverage. Compare the RN
figure separately, and ask specifically who covers nights and weekends.</p>
<h2>Turnover</h2>
<p>CMS reports total nursing-staff turnover and RN turnover over the year. In this data the median
total nursing-staff turnover is <strong>{med(to_v):.1f}%</strong> and median RN turnover is
<strong>{med(rtn_v):.1f}%</strong>. Very high turnover suggests unstable staffing — which affects
consistency of care, family communication and training. Low turnover is not automatically better
if the facility is understaffed, but it is a good sign when staffing hours are also solid.</p>
<h2>The abuse and special-focus flags</h2>
<p>CMS flags facilities with abuse citations in the last three survey cycles —
<strong>{pct(n_abuse, len(homes))}</strong> of facilities in this directory — and special-focus
status for persistent quality problems (<strong>{pct(n_focus, len(homes))}</strong>). These are
independent of star ratings and worth checking even for 4- and 5-star facilities.</p>
<h2>How to check</h2>
<p>Every facility page in this directory shows staffing hours, turnover, ownership and flags next
to the CMS star ratings. Compare at least three facilities at the same level of care, and ask each
one how the numbers translate into a typical day on the floor.</p>
{related([("/guides/how-nursing-home-ratings-work/", "How CMS ratings work"),
          ("/stats/", "National statistics from this CMS data")])}""",
          crumbs=[("Guides", "/guides/"), ("Staffing", None)])

    # ---- national statistics page (original data from the CMS file)
    own_rows = "".join(f"<tr><td>{esc(k)}</td><td>{human(v)}</td><td>{pct(v, len(homes))}</td></tr>"
                       for k, v in own.most_common())
    chain_rows = "".join(f"<tr><td>{esc(k)}</td><td>{human(v)}</td></tr>" for k, v in top_chains)
    h2 = lambda title, rows: f"<h2>{title}</h2><table><tr><th>State</th><th>Average</th></tr>{rows}</table>"
    rows_staff_top = "".join(f'<tr><td><a href="{state_url[s]}">{esc(STATE_NAMES.get(s, s))}</a></td><td>{v:.2f} hours</td></tr>' for s, v in top_staff)
    rows_staff_low = "".join(f'<tr><td><a href="{state_url[s]}">{esc(STATE_NAMES.get(s, s))}</a></td><td>{v:.2f} hours</td></tr>' for s, v in low_staff)
    rows_rating_top = "".join(f'<tr><td><a href="{state_url[s]}">{esc(STATE_NAMES.get(s, s))}</a></td><td>{v:.2f} / 5</td></tr>' for s, v in top_rating)
    rows_rating_low = "".join(f'<tr><td><a href="{state_url[s]}">{esc(STATE_NAMES.get(s, s))}</a></td><td>{v:.2f} / 5</td></tr>' for s, v in low_rating)
    s.add("/stats/", "US Nursing Home Statistics — Beds, Staffing, Ratings, Ownership",
          f"National statistics from the CMS nursing home file: {human(len(homes))} facilities, "
          f"{human(int(sum(beds_v)))} certified beds, staffing hours, turnover, ownership, chains "
          f"and state comparison tables.",
          f"""<h1>US nursing home statistics</h1>
<p class="lede">Original summary statistics computed from the CMS Provider Information file for the
<strong>{human(len(homes))}</strong> Medicare/Medicaid-certified nursing homes listed in this
directory.</p>
<h2>National overview</h2>
<table>
<tr><td>Facilities</td><td>{human(len(homes))}</td></tr>
<tr><td>States and territories</td><td>{human(len(by_state))}</td></tr>
<tr><td>Certified beds</td><td>{human(int(sum(beds_v)))}</td></tr>
<tr><td>Median beds per facility</td><td>{med(beds_v):.0f}</td></tr>
<tr><td>Average residents per day (median)</td><td>{med(res_v):.0f}</td></tr>
<tr><td>Facilities rated 4 or 5 stars (of rated)</td><td>{pct(n_high, len(rated))}</td></tr>
<tr><td>Facilities with an abuse flag</td><td>{pct(n_abuse, len(homes))}</td></tr>
<tr><td>Facilities with special-focus status</td><td>{pct(n_focus, len(homes))}</td></tr>
<tr><td>Facilities with sprinklers in all required areas</td><td>{pct(n_sprink, len(homes))}</td></tr>
<tr><td>Facilities with a resident and family council</td><td>{pct(n_council, len(homes))}</td></tr>
</table>
<h2>Staffing and turnover (national medians)</h2>
<table>
<tr><td>Total nurse staffing hours per resident per day</td><td>{med(staff_v):.2f}</td></tr>
<tr><td>RN staffing hours per resident per day</td><td>{med(rn_v):.2f}</td></tr>
<tr><td>Total nurse hours on weekends</td><td>{med(wk_v):.2f}</td></tr>
<tr><td>Total nursing-staff turnover</td><td>{med(to_v):.1f}%</td></tr>
<tr><td>RN turnover</td><td>{med(rtn_v):.1f}%</td></tr>
</table>
<h2>Ownership</h2>
<table><tr><th>Ownership type</th><th>Facilities</th><th>Share</th></tr>{own_rows}</table>
<h2>Chains with the most facilities</h2>
<table><tr><th>Chain</th><th>Facilities</th></tr>{chain_rows}</table>
<p>{pct(len(chain_homes), len(homes))} of facilities belong to a multi-facility chain.</p>
{h2("States with the most nurse staffing hours (≥20 facilities)", rows_staff_top)}
{h2("States with the fewest nurse staffing hours (≥20 facilities)", rows_staff_low)}
{h2("States with the highest average CMS overall rating (≥20 facilities)", rows_rating_top)}
{h2("States with the lowest average CMS overall rating (≥20 facilities)", rows_rating_low)}
<p class="mut">Averages are computed from the CMS published file and are not risk-adjusted; use
them as context, not as facility quality verdicts. Individual facility pages carry the CMS
ratings.</p>
{notice("Data: CMS Provider Data Catalog, nursing home Provider Information (public domain), "
        "reproduced as published. Not medical or legal advice.")}""",
          crumbs=[("Statistics", None)])

    # ---- cost-of-care pages (CareScout 2025 survey, state medians)
    def money(v):
        return f"${v:,.0f}" if v else "—"

    def monthly(v):
        return f"${v / 12:,.0f}" if v else "—"

    nat = cost_nat["annual"]
    s.add("/guides/how-much-does-nursing-home-care-cost/",
          "How Much Does Nursing Home Care Cost? (2025 Survey Data)",
          f"National median costs for nursing home care, assisted living, adult day care and "
          f"in-home help from the CareScout/Genworth 2025 survey — and how the numbers differ by "
          f"state and by level of care.",
          f"""<h1>How much does nursing home care cost?</h1>
<p class="lede">CareScout's 2025 Cost of Care Survey puts the national median at
<strong>{money(nat['nursing_semi'])} a year</strong> for a semi-private nursing home room and
<strong>{money(nat['nursing_private'])}</strong> for a private room. Costs vary widely by state —
use the <a href="/costs/">state cost tables</a> for local numbers.</p>
<h2>National medians, 2025</h2>
<table>
<tr><th>Setting</th><th>Annual median</th><th>Monthly</th></tr>
<tr><td>Nursing home — semi-private room</td><td>{money(nat['nursing_semi'])}</td><td>{monthly(nat['nursing_semi'])}</td></tr>
<tr><td>Nursing home — private room</td><td>{money(nat['nursing_private'])}</td><td>{monthly(nat['nursing_private'])}</td></tr>
<tr><td>Assisted living community</td><td>{money(nat['assisted_living'])}</td><td>{monthly(nat['assisted_living'])}</td></tr>
<tr><td>Adult day health care</td><td>{money(nat['adult_day'])}</td><td>{monthly(nat['adult_day'])}</td></tr>
<tr><td>Homemaker services (44 h/week)</td><td>{money(nat['homemaker'])}</td><td>{monthly(nat['homemaker'])}</td></tr>
<tr><td>In-home caregiver (hourly median)</td><td>{money(cost_nat['hourly']['caregiver'])}/hour</td><td>—</td></tr>
</table>
<h2>What these numbers include — and what they do not</h2>
<p>The survey reports <strong>median private-pay rates</strong> for the base service. Nursing home
rates cover room, board and routine nursing care; they generally <strong>do not include</strong>
medications, therapy add-ons, specialised care, transport or beauty/laundry services. Assisted
living rates often exclude a la carte care charges. The median is not your price: a facility's own
quote, the level of care, the room type and the state all move it.</p>
<h2>How the cost changes with level of care</h2>
<p>In-home help is billed hourly; nursing homes bill daily. The annual figures for homemaker
services assume <strong>44 hours of help per week</strong>, and adult day health care assumes
<strong>5 days a week</strong> — use the hourly rate to model the hours you actually need. Nursing
home care is the most expensive setting, and a private room costs roughly
<strong>{money(nat['nursing_private'] - nat['nursing_semi'])} a year more</strong> than a
semi-private room nationally.</p>
<h2>Who pays</h2>
<p>Medicare covers only short-term skilled care (up to 100 days after a qualifying hospital stay)
and does not pay for custodial care; Medicaid pays for long-term care for people who meet their
state's income and asset limits; VA benefits, long-term care insurance and private funds cover the
rest. See <a href="/guides/paying-for-nursing-home-care/">how to pay for nursing home care</a>.</p>
<h2>State variation</h2>
<p>State medians for a semi-private room range from well under $100,000 to more than $300,000 a
year in the most expensive states. The <a href="/costs/">cost tables by state</a> show the survey
medians next to each state's facility list, so you can compare local prices with the facilities
actually certified there.</p>
{notice("Source: CareScout (formerly Genworth) Cost of Care Survey 2025, median cost data tables, "
        "retrieved 2026-10-24. Figures are national/state medians for private pay, not quotes.")}""",
          crumbs=[("Guides", "/guides/"), ("Costs", None)])

    # cost index
    state_rows = "".join(
        f'<tr><td><a href="{cost_url[st]}">{esc(STATE_NAMES[st])}</a></td>'
        f'<td>{money(cost_states[STATE_NAMES[st]]["annual"]["nursing_semi"])}</td>'
        f'<td>{money(cost_states[STATE_NAMES[st]]["annual"]["nursing_private"])}</td>'
        f'<td>{money(cost_states[STATE_NAMES[st]]["annual"]["assisted_living"])}</td>'
        f'<td>{money((cost_states[STATE_NAMES[st]]["hourly"] or {}).get("caregiver"))}</td></tr>'
        for st in sorted(cost_url, key=lambda x: STATE_NAMES[x]))
    s.add("/costs/", "Nursing Home and Long-Term Care Costs by State (2025)",
          f"Median annual costs for nursing homes, assisted living and in-home care in every state "
          f"— CareScout 2025 survey data — with links to each state's certified facilities.",
          f"""<h1>Nursing home and long-term care costs by state</h1>
<p class="lede">CareScout's 2025 Cost of Care Survey medians for private-pay care, state by state.
National medians: <strong>{money(nat['nursing_semi'])}</strong> a year for a semi-private nursing
home room, <strong>{money(nat['nursing_private'])}</strong> for a private room,
<strong>{money(nat['assisted_living'])}</strong> for assisted living, and
<strong>{money(cost_nat['hourly']['caregiver'])}/hour</strong> for a non-medical caregiver.</p>
<table>
<tr><th>State</th><th>Nursing home semi-private</th><th>Private room</th><th>Assisted living</th><th>Caregiver hourly</th></tr>
{state_rows}
</table>
<h2>How to read this table</h2>
<p>All figures are <strong>annual medians</strong> except the caregiver rate, which is hourly.
Nursing home rates cover room, board and routine care but not medications, therapy add-ons or
specialised services; assisted living rates often exclude a la carte care charges. These are
survey medians, not quotes — the facility's own price depends on the room, level of care and
contract.</p>
<h2>What changes the bill</h2>
<p>Room type (private rooms cost more), the level of care (memory care and skilled nursing cost
more than basic assisted living), state wage levels (which drive staffing costs) and the contract
terms (entrance fees, add-ons, rate increases). Compare at least three facilities in the same
category and ask for the complete fee schedule, not just the base rate.</p>
{notice("Source: CareScout (formerly Genworth) Cost of Care Survey 2025, median cost data tables, "
        "retrieved 2026-10-24. Not a quote; not medical or legal advice.")}
{related([("/guides/paying-for-nursing-home-care/", "How to pay for care"),
          ("/guides/how-much-does-nursing-home-care-cost/", "What the national numbers mean"),
          ("/guides/medicaid-and-nursing-homes/", "Medicaid and nursing homes"),
          ("/search/", "Find facilities by state")])}""",
          crumbs=[("Costs", None)])

    # per-state cost pages
    for st, curl in cost_url.items():
        sname = STATE_NAMES[st]
        cs = cost_states[sname]["annual"]
        ch = cost_states[sname]["hourly"] or {}
        nat_semi = nat["nursing_semi"]
        diff = None
        if cs.get("nursing_semi") and nat_semi:
            diff = (cs["nursing_semi"] - nat_semi) / nat_semi * 100
        cmp_txt = (f"{abs(diff):.0f}% {'above' if diff >= 0 else 'below'} the national median"
                   if diff is not None else "not comparable")
        facilities_link = state_url.get(st)
        body = f"""
<h1>Nursing home and long-term care costs in {esc(sname)}</h1>
<p class="lede">CareScout's 2025 survey median for a semi-private nursing home room in
{esc(sname)} is <strong>{money(cs.get('nursing_semi'))} a year</strong>
({monthly(cs.get('nursing_semi'))} a month) — {cmp_txt} of {money(nat_semi)}.</p>
<h2>Median costs in {esc(sname)} (2025)</h2>
<table>
<tr><th>Setting</th><th>Annual median</th><th>Monthly</th></tr>
<tr><td>Nursing home — semi-private room</td><td>{money(cs.get('nursing_semi'))}</td><td>{monthly(cs.get('nursing_semi'))}</td></tr>
<tr><td>Nursing home — private room</td><td>{money(cs.get('nursing_private'))}</td><td>{monthly(cs.get('nursing_private'))}</td></tr>
<tr><td>Assisted living community</td><td>{money(cs.get('assisted_living'))}</td><td>{monthly(cs.get('assisted_living'))}</td></tr>
<tr><td>Adult day health care</td><td>{money(cs.get('adult_day'))}</td><td>{monthly(cs.get('adult_day'))}</td></tr>
<tr><td>Homemaker services (44 h/week)</td><td>{money(cs.get('homemaker'))}</td><td>{monthly(cs.get('homemaker'))}</td></tr>
<tr><td>In-home caregiver (hourly median)</td><td>{money(ch.get('caregiver'))}/hour</td><td>—</td></tr>
</table>
<h2>What drives cost in {esc(sname)}</h2>
<p>State medians reflect local wages, staffing requirements and demand. Within {esc(sname)}, urban
facilities usually cost more than rural ones, private rooms cost more than semi-private, and memory
care or skilled nursing costs more than basic assisted living. The median is a starting point: ask
each facility for its complete fee schedule, including medication management, therapy, laundry,
transport and any entrance or community fee.</p>
<h2>What the survey does not include</h2>
<p>The figures are private-pay medians for the base service. Nursing home rates generally exclude
medications, specialised therapies and transport; assisted living rates often exclude a la carte
care charges. Long-term insurance, Medicaid and VA benefits can change what a family actually pays
— see the payment guides below.</p>
{f'<h2>Nursing homes in {esc(sname)}</h2><p>Compare the local facilities and their CMS ratings: '
 f'<a href="{facilities_link}">all certified nursing homes in {esc(sname)}</a>.</p>' if facilities_link else ''}
{related([("/guides/paying-for-nursing-home-care/", "How to pay for care"),
          ("/guides/medicaid-and-nursing-homes/", "Medicaid eligibility"),
          ("/guides/how-much-does-nursing-home-care-cost/", "National cost explainer"),
          ("/costs/", "Costs by state")])}
{faq([
    (f"How much does a nursing home cost in {sname}?",
     f"The 2025 CareScout survey median for a semi-private room in {sname} is "
     f"{money(cs.get('nursing_semi'))} a year ({monthly(cs.get('nursing_semi'))} a month); a private "
     f"room is {money(cs.get('nursing_private'))}. Actual prices vary by facility and contract."),
    (f"How much is assisted living in {sname}?",
     f"The median assisted living rate in {sname} is {money(cs.get('assisted_living'))} a year "
     f"({monthly(cs.get('assisted_living'))} a month), excluding a la carte care charges."),
    (f"How much does in-home care cost in {sname}?",
     f"The median non-medical caregiver rate in {sname} is {money(ch.get('caregiver'))} per hour; "
     f"homemaker services at 44 hours a week cost {money(cs.get('homemaker'))} a year."),
])}"""
        s.add(curl, f"Nursing Home Costs in {sname} (2025) — Median Prices by Setting",
              f"Median 2025 costs in {sname}: nursing home semi-private {money(cs.get('nursing_semi'))}/yr, "
              f"private {money(cs.get('nursing_private'))}/yr, assisted living "
              f"{money(cs.get('assisted_living'))}/yr, caregiver {money(ch.get('caregiver'))}/hr.",
              body, crumbs=[("Costs", "/costs/"), (sname, None)])

    s.add("/guides/", "Guides — US Nursing Homes",
          "Explainers on CMS nursing home ratings, paying for care, Medicare and Medicaid "
          "coverage, care settings, staffing, costs and national statistics.",
          "<h1>Guides</h1><p class=\"lede\">Plain explainers for the questions families actually ask — plus statistics computed from the CMS data behind this directory.</p>"
          + cards([("/guides/how-nursing-home-ratings-work/", "How CMS star ratings work",
                    "Inspections, staffing and quality measures — and the abuse/special-focus flags."),
                   ("/guides/how-to-choose-a-nursing-home/", "How to choose a nursing home",
                    "A practical checklist for shortlisting and visiting facilities."),
                   ("/guides/how-much-does-nursing-home-care-cost/", "How much does care cost?",
                    "2025 national medians and what the survey does and does not include."),
                   ("/costs/", "Costs by state",
                    "Nursing home, assisted living and in-home medians for every state."),
                   ("/guides/paying-for-nursing-home-care/", "How to pay for nursing home care",
                    "Costs, and the payment sources in the order families use them."),
                   ("/guides/medicare-and-nursing-homes/", "Does Medicare cover nursing home care?",
                    "The 100-day SNF benefit, the 3-day rule and custodial care."),
                   ("/guides/medicaid-and-nursing-homes/", "Medicaid and nursing homes",
                    "Eligibility, the 5-year look-back and how to apply."),
                   ("/guides/nursing-home-vs-home-care-vs-assisted-living/", "Nursing home vs other care",
                    "What each setting provides and who pays for it."),
                   ("/guides/nursing-home-staffing-and-turnover/", "Staffing hours and turnover",
                    "What the staffing data means, with national medians."),
                   ("/stats/", "US nursing home statistics",
                    "Beds, staffing, ratings and ownership — computed from this CMS file.")]),
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
{related([("/#ratings", "Browse by rating"), ("/search/", "Search facilities")]
         + ([(cost_url[st], f"Nursing home costs in {sname}")] if st in cost_url else []))}
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
    titles_used = set()
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
          (cost_url[h["state"]], f"Nursing home costs in {sname}") if h["state"] in cost_url else ("/costs/", "Costs by state"),
          ("/guides/how-nursing-home-ratings-work/", "How the ratings work")])}
{health_cross_links(h["state"], "nursinghomes")}
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
        title = seo_title(h["label"], f' — {h["city"]}, {h["state"]}')
        if title in titles_used:
            title = seo_title(f'{h["label"]} ({h["ccn"]})', f' — {h["city"]}')
        if title in titles_used:
            title = f'{h["label"][:40].rstrip()} — {h["ccn"]}'
        titles_used.add(title)
        s.add(h["url"], title,
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
