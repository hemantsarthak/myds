#!/usr/bin/env python3
"""Data-driven insight articles for the hub, computed from the same public datasets that power the
directories. These are the pages most likely to earn links: unique numbers, clear methods, and a
path into the underlying directory pages."""
import collections
import csv
import pathlib

from engine.sitegen import cards, esc, human, notice, related, table

ROOT = pathlib.Path(__file__).resolve().parents[2]
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
}


def rows(name):
    with (CACHE / name).open(encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(str(x).strip())
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def fmt_pct(part, whole):
    return f"{part / whole * 100:.1f}%" if whole else "—"


# ---------------------------------------------------------------- hospital ratings by state
def hospital_state_stats():
    stats = collections.defaultdict(lambda: {"n": 0, "rated": 0, "top": 0, "sum": 0.0})
    for r in rows("hospital_general.csv"):
        st = (r.get("State") or "").strip()
        if st not in STATE_NAMES:
            continue
        s = stats[st]
        s["n"] += 1
        rating = num(r.get("Hospital overall rating"))
        if rating and 1 <= rating <= 5:
            s["rated"] += 1
            s["sum"] += rating
            if rating >= 4:
                s["top"] += 1
    out = []
    for st, s in stats.items():
        if s["rated"] < 20:
            continue
        out.append((st, s["n"], s["rated"], s["sum"] / s["rated"], s["top"] / s["rated"] * 100))
    out.sort(key=lambda x: -x[4])
    return out


def page_hospital_ratings(site):
    data = hospital_state_stats()
    total_hosp = sum(r[1] for r in data)
    rated = sum(r[2] for r in data)
    top = [d for d in data if d[0] not in ("PR", "VI", "GU", "AS")]
    table_rows = [[esc(STATE_NAMES[st]), human(n), human(rated), f"{avg:.2f} ★", f"{pct:.0f}%"]
                  for st, n, rated, avg, pct in data[:15]]
    body = f"""
<h1>Which US states have the best-rated hospitals?</h1>
<p class="lede">CMS gives every hospital an overall star rating from one to five. Aggregating the
ratings by state shows where the share of four- and five-star hospitals is highest — and the
differences are larger than the state ranking by average rating suggests.
<span class="stat">{human(rated)} rated hospitals</span><span class="stat">{human(total_hosp)} hospitals</span></p>
<h2>Key findings</h2>
<ul>
<li><strong>{esc(STATE_NAMES[top[0][0]])}</strong> leads with {top[0][4]:.0f}% of its rated hospitals at
four stars or better, followed by {esc(STATE_NAMES[top[1][0]])} ({top[1][4]:.0f}%) and
{esc(STATE_NAMES[top[2][0]])} ({top[2][4]:.0f}%).</li>
<li>At the other end, <strong>{esc(STATE_NAMES[top[-1][0]])}</strong> has {top[-1][4]:.0f}% of rated
hospitals at four stars or better.</li>
<li>Across the country, {fmt_pct(sum(r[2] for r in data if r[4] >= 50), rated)} of rated hospitals are
in states where at least half the rated hospitals are four-star or better.</li>
</ul>
<h2>States ranked by share of four- and five-star hospitals</h2>
{table(["State", "Hospitals", "Rated", "Average rating", "Four stars or better"], table_rows)}
<p class="mut">States with fewer than 20 rated hospitals are excluded from the ranking.</p>
<h2>How to read this</h2>
<p>The share of top-rated hospitals and the average rating are different measures: a state where most
hospitals are unrated can post a flattering average from a small rated set. That is why the table
shows both the number of rated hospitals and the percentage at four stars or better.</p>
<h2>Method</h2>
<p>Ratings are the CMS overall hospital star ratings from Care Compare, aggregated by the hospital
state field. Unrated hospitals (including those with too few measures) are counted in the hospital
total but excluded from the averages. Data: CMS Provider Data Catalog, public domain.</p>
{related([("https://hospitals.tekify.xyz", "Look up any hospital here"),
          ("https://hospitals.tekify.xyz/state/ca/", "California hospitals"),
          ("https://hospitals.tekify.xyz/state/tx/", "Texas hospitals"),
          ("/insights/hospitals-by-ownership/", "Hospitals by ownership type")])}
"""
    site.add("/insights/hospital-ratings-by-state/",
             "Which US states have the best-rated hospitals? — CMS data",
             "CMS hospital star ratings aggregated by state: the share of four- and five-star hospitals, "
             "average ratings and how many hospitals each state reports.",
             body, crumbs=[("Insights", "/insights/"), ("Hospital ratings by state", None)])


# ---------------------------------------------------------------- hospitals by ownership
def page_hospital_ownership(site):
    groups = collections.defaultdict(lambda: {"n": 0, "rated": 0, "sum": 0.0, "top": 0})
    for r in rows("hospital_general.csv"):
        own = (r.get("Hospital Ownership") or "Unknown").strip()
        key = ("For-profit" if "profit" in own.lower() and "non" not in own.lower()
               else "Non-profit" if "non" in own.lower() or "voluntary" in own.lower()
               else "Government" if "government" in own.lower() or "federal" in own.lower()
               else own)
        g = groups[key]
        g["n"] += 1
        rating = num(r.get("Hospital overall rating"))
        if rating and 1 <= rating <= 5:
            g["rated"] += 1
            g["sum"] += rating
            if rating >= 4:
                g["top"] += 1
    rated_groups = [(k, v) for k, v in groups.items() if v["rated"] > 0]
    order = sorted(rated_groups, key=lambda kv: -(kv[1]["sum"] / kv[1]["rated"]))
    tr = [[esc(k), human(v["n"]), human(v["rated"]),
           f'{v["sum"] / v["rated"]:.2f} ★' if v["rated"] else "—",
           fmt_pct(v["top"], v["rated"])] for k, v in order]
    best = order[0]
    worst = order[-1]
    body = f"""
<h1>Hospital star ratings by ownership type</h1>
<p class="lede">CMS data records each hospital's ownership: non-profit, for-profit, or government
(local, state and federal). Aggregating the star ratings by ownership gives a clear picture of who
runs the best-rated hospitals nationally.</p>
<h2>Key findings</h2>
<ul>
<li><strong>{esc(best[0])}</strong> hospitals average {best[1]["sum"] / best[1]["rated"]:.2f} stars, with
{fmt_pct(best[1]["top"], best[1]["rated"])} rated four stars or better.</li>
<li><strong>{esc(worst[0])}</strong> hospitals average {worst[1]["sum"] / worst[1]["rated"]:.2f} stars,
with {fmt_pct(worst[1]["top"], worst[1]["rated"])} at four stars or better.</li>
<li>Taken together, these groups cover {human(sum(v["n"] for _, v in order))} hospitals, of which
{human(sum(v["rated"] for _, v in order))} carry an overall CMS rating.</li>
</ul>
{table(["Ownership", "Hospitals", "Rated", "Average rating", "Four stars or better"], tr)}
<h2>Why this matters</h2>
<p>Ownership does not decide quality, but the pattern is worth knowing when choosing a hospital:
large for-profit chains, non-profit systems and public hospitals tend to report different mixes of
services, and their patient populations differ. The rating adjusts for some of that, but not all.</p>
<h2>Method</h2>
<p>Ownership labels are grouped into non-profit, for-profit and government from the CMS
"Hospital Ownership" field; unrated hospitals are excluded from averages. Data: CMS Provider Data
Catalog (public domain).</p>
{related([("https://hospitals.tekify.xyz", "Browse hospitals by state"),
          ("/insights/hospital-ratings-by-state/", "Ratings by state"),
          ("https://nursinghomes.tekify.xyz", "Nursing-home ratings")])}
"""
    site.add("/insights/hospitals-by-ownership/", "Hospital Star Ratings by Ownership Type — CMS Data",
             "Average CMS hospital star rating for non-profit, for-profit and government hospitals, "
             "with the share rated four stars or better.",
             body, crumbs=[("Insights", "/insights/"), ("Hospitals by ownership", None)])


# ---------------------------------------------------------------- nursing home staffing by state
def page_nursing_staffing(site):
    stats = collections.defaultdict(lambda: {"n": 0, "rated": 0, "sum": 0.0, "staff": 0.0, "staff_n": 0, "beds": 0})
    for r in rows("nursing_homes.csv"):
        st = (r.get("State") or "").strip()
        if st not in STATE_NAMES:
            continue
        s = stats[st]
        s["n"] += 1
        s["beds"] += num(r.get("Number of Certified Beds")) or 0
        rating = num(r.get("Overall Rating"))
        if rating and 1 <= rating <= 5:
            s["rated"] += 1
            s["sum"] += rating
        sr = num(r.get("Staffing Rating"))
        if sr and 1 <= sr <= 5:
            s["staff"] += sr
            s["staff_n"] += 1
    out = []
    for st, s in stats.items():
        if s["rated"] < 30 or s["staff_n"] < 30:
            continue
        out.append((st, s["n"], s["sum"] / s["rated"], s["staff"] / s["staff_n"], int(s["beds"])))
    out.sort(key=lambda x: -x[3])
    tr = [[esc(STATE_NAMES[st]), human(n), f"{staff:.2f} ★", f"{overall:.2f} ★", human(beds)]
          for st, n, overall, staff, beds in out[:15]]
    body = f"""
<h1>Nursing-home staffing ratings by state</h1>
<p class="lede">CMS rates nursing homes on staffing as well as inspections and quality measures.
Sorting the country by average staffing rating shows where facilities are most consistently
well-staffed relative to their residents.
<span class="stat">{human(sum(r[1] for r in out))} facilities</span>
<span class="stat">{human(len(out))} states</span></p>
<h2>Key findings</h2>
<ul>
<li><strong>{esc(STATE_NAMES[out[0][0]])}</strong> has the highest average staffing rating
({out[0][3]:.2f} of 5), ahead of {esc(STATE_NAMES[out[1][0]])} ({out[1][3]:.2f}) and
{esc(STATE_NAMES[out[2][0]])} ({out[2][3]:.2f}).</li>
<li>The lowest average in the table is {esc(STATE_NAMES[out[-1][0]])} at {out[-1][3]:.2f}.</li>
<li>Overall ratings do not always follow staffing: in some states the average overall rating is lower
than the staffing rating, meaning inspection or quality results drag the overall score down.</li>
</ul>
{table(["State", "Facilities", "Staffing rating", "Overall rating", "Certified beds"], tr)}
<p class="mut">States with fewer than 30 rated facilities are excluded.</p>
<h2>What the staffing rating measures</h2>
<p>CMS compares nurse staffing hours per resident per day with what it expects for the residents a
facility actually has, and adjusts for case mix. Turnover is part of the picture too: facilities with
high staff churn score worse even when headline hours look adequate.</p>
<h2>Method</h2>
<p>Average of the CMS staffing rating and overall rating across facilities with a valid rating, by
state. Data: CMS Provider Data Catalog, Nursing Home Provider Information (public domain).</p>
{related([("https://nursinghomes.tekify.xyz", "Look up a nursing home"),
          ("/insights/hospital-ratings-by-state/", "Hospital ratings by state"),
          ("https://homehealth.tekify.xyz", "Home-health agencies")])}
"""
    site.add("/insights/nursing-home-staffing-by-state/",
             "Nursing-Home Staffing Ratings by State — CMS Data",
             "Average CMS staffing and overall ratings for nursing homes by state, with facility counts "
             "and certified beds.",
             body, crumbs=[("Insights", "/insights/"), ("Nursing-home staffing", None)])


# ---------------------------------------------------------------- dialysis ratings
def page_dialysis(site):
    dist = collections.Counter()
    total = 0
    states = collections.defaultdict(lambda: {"n": 0, "rated": 0, "top": 0})
    for r in rows("dialysis.csv"):
        total += 1
        rating = num(r.get("Five Star"))
        if rating and 1 <= rating <= 5:
            dist[int(rating)] += 1
        st = (r.get("State") or "").strip()
        if st in STATE_NAMES:
            s = states[st]
            s["n"] += 1
            if rating:
                s["rated"] += 1
                if rating >= 4:
                    s["top"] += 1
    rated = sum(dist.values())
    best = sorted(((st, v) for st, v in states.items() if v["rated"] >= 20),
                  key=lambda kv: -(kv[1]["top"] / kv[1]["rated"]))[:15]
    tr = [[esc(STATE_NAMES[st]), human(v["n"]), human(v["rated"]), f'{v["top"] / v["rated"] * 100:.0f}%']
          for st, v in best]
    dist_rows = [[f"{n} stars", human(dist[n]), fmt_pct(dist[n], rated)] for n in (5, 4, 3, 2, 1)]
    body = f"""
<h1>US dialysis facilities: the national rating picture</h1>
<p class="lede">CMS publishes a five-star rating for dialysis facilities based on patient survival,
hospitalisation, readmission, transfusion, emergency-department visits and transplant waitlisting.
Across the country, most rated facilities land in three stars — but the spread between states is wide.
<span class="stat">{human(total)} facilities</span><span class="stat">{human(rated)} rated</span></p>
<h2>Ratings distribution</h2>
{table(["Rating", "Facilities", "Share of rated"], dist_rows)}
<h2>States with the highest share of four- and five-star facilities</h2>
{table(["State", "Facilities", "Rated", "Four stars or better"], tr)}
<p class="mut">States with fewer than 20 rated facilities are excluded.</p>
<h2>What the rating does and does not capture</h2>
<p>The star rating summarises outcomes, not amenities or convenience. Two facilities with the same
stars can differ in whether they offer home haemodialysis training, how many stations they run, and
whether they have a late shift — details worth checking for anyone choosing a centre.</p>
<h2>Method</h2>
<p>Counts and averages come from the CMS Dialysis Facility listing; "Not Available" ratings are
excluded. Data: CMS Provider Data Catalog (public domain).</p>
{related([("https://dialysis.tekify.xyz", "Look up a dialysis facility"),
          ("https://dialysis.tekify.xyz/rating/5/", "Five-star facilities"),
          ("/insights/hospital-ratings-by-state/", "Hospital ratings by state")])}
"""
    site.add("/insights/dialysis-ratings-nationally/",
             "US Dialysis Facilities: National Rating Distribution — CMS Data",
             "How CMS five-star dialysis ratings are distributed nationally, and which states have the "
             "highest share of four- and five-star facilities.",
             body, crumbs=[("Insights", "/insights/"), ("Dialysis ratings", None)])


# ---------------------------------------------------------------- IFSC branch counts
def page_ifsc(site):
    counts = collections.Counter()
    total = 0
    for r in rows("ifsc.csv"):
        bank = (r.get("BANK") or "").strip()
        if not bank:
            continue
        counts[bank] += 1
        total += 1
    top = counts.most_common(15)
    tr = [[str(i + 1), esc(bank), human(n), f"{n / total * 100:.1f}%"] for i, (bank, n) in enumerate(top)]
    body = f"""
<h1>Which Indian banks have the most branches?</h1>
<p class="lede">Every bank branch in India has an IFSC code, so counting codes by bank gives a direct
measure of branch network size. The largest networks are not the ones most people would guess.
<span class="stat">{human(total)} IFSC codes</span><span class="stat">{human(len(counts))} banks</span></p>
<h2>Key findings</h2>
<ul>
<li><strong>{esc(top[0][0])}</strong> has the largest network with {human(top[0][1])} branches
({top[0][1] / total * 100:.1f}% of all codes).</li>
<li>The top five banks together account for {sum(n for _, n in top[:5]) / total * 100:.1f}% of every
IFSC code in the dataset.</li>
<li>The long tail is enormous: most banks in the directory have fewer than 100 branches.</li>
</ul>
{table(["#", "Bank", "Branches", "Share"], tr)}
<h2>Why IFSC codes matter</h2>
<p>An IFSC code identifies a specific bank branch for NEFT, RTGS and IMPS transfers. The first four
characters identify the bank, the fifth is a zero, and the last six identify the branch. Getting one
character wrong sends money to the wrong bank — which is why every transfer should be checked
against the branch record rather than a code copied from a message.</p>
<h2>Method</h2>
<p>Counts of IFSC codes by the bank field in the Razorpay IFSC dataset (MIT licence), which mirrors
the Reserve Bank of India's published branch list.</p>
{related([("https://ifsccodes.tekify.xyz", "Look up any IFSC code"),
          ("https://ifsccodes.tekify.xyz/search/", "Search by bank or city"),
          ("/insights/dialysis-ratings-nationally/", "US dialysis ratings")])}
"""
    site.add("/insights/indian-bank-branch-networks/",
             "Which Indian Banks Have the Most Branches? — IFSC Data",
             "Ranking Indian banks by branch network size using IFSC codes, with shares of the national "
             "total.",
             body, crumbs=[("Insights", "/insights/"), ("Bank branch networks", None)])


def build_insights(site):
    page_hospital_ratings(site)
    page_hospital_ownership(site)
    page_nursing_staffing(site)
    page_dialysis(site)
    page_ifsc(site)
    site.add("/insights/", "Insights — Tekify",
             "Data-driven articles computed from the same public datasets that power the Tekify "
             "directories: hospital ratings by state, nursing-home staffing, dialysis ratings and "
             "Indian bank branch networks.",
             """<h1>Insights</h1>
<p class="lede">Short, data-driven articles computed from the open datasets behind our directories.
Every number can be traced back to the source dataset, and every article links into the directory
where you can look up an individual record.</p>"""
             + cards([("/insights/hospital-ratings-by-state/", "Which states have the best-rated hospitals?",
                        "CMS star ratings aggregated by state."),
                      ("/insights/hospitals-by-ownership/", "Hospital ratings by ownership type",
                        "Non-profit vs for-profit vs government hospitals."),
                      ("/insights/nursing-home-staffing-by-state/", "Nursing-home staffing ratings by state",
                        "Where facilities are most consistently well staffed."),
                      ("/insights/dialysis-ratings-nationally/", "US dialysis: the national rating picture",
                        "Distribution of the CMS five-star ratings."),
                      ("/insights/indian-bank-branch-networks/", "Which Indian banks have the most branches?",
                        "The IFSC dataset, counted by bank.")]),
             crumbs=[("Insights", None)])
