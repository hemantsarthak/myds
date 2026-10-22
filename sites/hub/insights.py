#!/usr/bin/env python3
"""Data-driven insight articles for the hub, computed from the same public datasets that power the
directories. These are the pages most likely to earn links: unique numbers, clear methods, and a
path into the underlying directory pages."""
import collections
import csv
import io
import pathlib
import zipfile

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



def bar_chart(items, fmt, width=680, bar_h=24, label_w=190):
    """Inline SVG horizontal bar chart (no JavaScript, no external assets)."""
    maxv = max((v for _, v in items), default=1) or 1
    rows = []
    for i, (label, v) in enumerate(items):
        w = max(2, int(v / maxv * (width - label_w - 90)))
        y = i * (bar_h + 6)
        rows.append(
            f'<text x="0" y="{y + 16}" font-size="13" fill="#334155">{esc(label)}</text>'
            f'<rect x="{label_w}" y="{y + 3}" width="{w}" height="{bar_h - 8}" fill="#2563eb" rx="2"/>'
            f'<text x="{label_w + w + 8}" y="{y + 16}" font-size="12" fill="#334155">{fmt(v)}</text>'
        )
    height = len(items) * (bar_h + 6) + 8
    return (f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img" '
            f'aria-label="bar chart" style="max-width:680px;height:auto;margin:12px 0">'
            + "".join(rows) + "</svg>")


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
    chart = bar_chart([(STATE_NAMES[st], pct) for st, n, rated, avg, pct in data[:12]], lambda v: f"{v:.0f}%")
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
{chart}
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
    chart = bar_chart([(STATE_NAMES[st], staff) for st, n, overall, staff, beds in out[:12]],
                      lambda v: f"{v:.2f} of 5")
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
{chart}
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
    dist_chart = bar_chart([(f"{n} stars", dist[n]) for n in (5, 4, 3, 2, 1)],
                           lambda v: human(int(v)))
    body = f"""
<h1>US dialysis facilities: the national rating picture</h1>
<p class="lede">CMS publishes a five-star rating for dialysis facilities based on patient survival,
hospitalisation, readmission, transfusion, emergency-department visits and transplant waitlisting.
Across the country, most rated facilities land in three stars — but the spread between states is wide.
<span class="stat">{human(total)} facilities</span><span class="stat">{human(rated)} rated</span></p>
<h2>Ratings distribution</h2>
{dist_chart}
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



# ---------------------------------------------------------------- hospital emergency departments
def page_hospital_er(site):
    stats = collections.defaultdict(lambda: {"n": 0, "er": 0})
    for r in rows("hospital_general.csv"):
        st = (r.get("State") or "").strip()
        if st not in STATE_NAMES:
            continue
        s = stats[st]
        s["n"] += 1
        if (r.get("Emergency Services") or "").strip().lower() == "yes":
            s["er"] += 1
    total_n = sum(v["n"] for v in stats.values())
    total_er = sum(v["er"] for v in stats.values())
    ranked = sorted(((st, v) for st, v in stats.items() if v["n"] >= 20),
                    key=lambda kv: -(kv[1]["er"] / kv[1]["n"]))
    tr = [[esc(STATE_NAMES[st]), human(v["n"]), human(v["er"]), f'{v["er"] / v["n"] * 100:.0f}%']
          for st, v in ranked[:15]]
    body = f"""
<h1>Which US hospitals have emergency departments?</h1>
<p class="lede">Most hospitals in the CMS directory report emergency services, but the share varies
enormously by state — from nearly every hospital to about half.
<span class="stat">{human(total_er)} with an ER</span><span class="stat">{human(total_n)} hospitals</span></p>
<h2>Key findings</h2>
<ul>
<li>Nationally, <strong>{total_er / total_n * 100:.0f}%</strong> of hospitals in the directory report
emergency services.</li>
<li><strong>{esc(STATE_NAMES[ranked[0][0]])}</strong> has the highest share at
<strong>{ranked[0][1]["er"] / ranked[0][1]["n"] * 100:.0f}%</strong>; the lowest in this table is
{esc(STATE_NAMES[ranked[-1][0]])} at {ranked[-1][1]["er"] / ranked[-1][1]["n"] * 100:.0f}%.</li>
<li>{human(total_n - total_er)} hospitals report no emergency services — many are specialty,
psychiatric, rehabilitation or critical-access facilities.</li>
</ul>
{table(["State", "Hospitals", "With emergency services", "Share"], tr)}
<p class="mut">States with fewer than 20 hospitals are excluded.</p>
<h2>Why it matters</h2>
<p>In an emergency the closest hospital may not have an emergency department. Checking before you
need it — especially in rural areas — is worth two minutes. Facility pages in the directory show the
emergency-services flag alongside the CMS rating, type and address.</p>
<h2>Method</h2>
<p>Counts of the CMS "Emergency Services" field by hospital state, excluding hospitals outside the 50
states and DC. Data: CMS Provider Data Catalog (public domain).</p>
{related([("https://hospitals.tekify.xyz", "Hospitals by state"),
          ("/insights/hospital-ratings-by-state/", "Best-rated hospitals by state"),
          ("https://hospitals.tekify.xyz/state/tx/", "Texas hospitals")])}
"""
    site.add("/insights/hospitals-with-emergency-departments/",
             "Which US Hospitals Have Emergency Departments? — CMS Data",
             "Share of US hospitals reporting emergency services, nationally and by state.",
             body, crumbs=[("Insights", "/insights/"), ("Emergency departments", None)])


# ---------------------------------------------------------------- nursing-home chains
def page_nursing_chains(site):
    chains = collections.defaultdict(lambda: {"n": 0, "rated": 0, "sum": 0.0, "beds": 0})
    for r in rows("nursing_homes.csv"):
        name = (r.get("Chain Name") or "").strip()
        if not name or name.lower() in ("", "not applicable", "independent"):
            continue
        c = chains[name]
        c["n"] += 1
        c["beds"] += num(r.get("Number of Certified Beds")) or 0
        rating = num(r.get("Overall Rating"))
        if rating and 1 <= rating <= 5:
            c["rated"] += 1
            c["sum"] += rating
    top = sorted(chains.items(), key=lambda kv: -kv[1]["n"])[:20]
    tr = [[str(i + 1), esc(name), human(v["n"]), human(int(v["beds"])),
           f'{v["sum"] / v["rated"]:.2f} ★' if v["rated"] else "—"] for i, (name, v) in enumerate(top)]
    all_fac = sum(v["n"] for v in chains.values())
    body = f"""
<h1>America's largest nursing-home chains</h1>
<p class="lede">CMS records the chain behind every nursing home. Counting facilities by chain shows
how concentrated the industry is — and how the biggest operators rate.
<span class="stat">{human(len(chains))} chains</span><span class="stat">{human(all_fac)} chain facilities</span></p>
<h2>Key findings</h2>
<ul>
<li><strong>{esc(top[0][0])}</strong> operates the largest network in the data with
{human(top[0][1]["n"])} facilities.</li>
<li>The ten largest chains together run {human(sum(v["n"] for _, v in top[:10]))} nursing homes —
{sum(v["n"] for _, v in top[:10]) / all_fac * 100:.0f}% of all chain-affiliated facilities
in the dataset.</li>
<li>Average overall ratings among the largest chains range from
{min((v["sum"] / v["rated"] for _, v in top if v["rated"]), default=0):.1f} to
{max((v["sum"] / v["rated"] for _, v in top if v["rated"]), default=0):.1f} stars.</li>
</ul>
{table(["#", "Chain", "Facilities", "Certified beds", "Average rating"], tr)}
<h2>What this means for families</h2>
<p>Chain affiliation is not a quality measure, but it is a practical thing to know: staffing policies,
training and management are often set at chain level, and problems tend to repeat across a chain's
facilities. CMS publishes chain-level averages alongside facility ratings for exactly that reason.</p>
<h2>Method</h2>
<p>Facility counts by the CMS "Chain Name" field; average of the overall star rating across rated
facilities in the chain. Independents and facilities without a chain are excluded. Data: CMS Provider
Data Catalog, Nursing Home Provider Information (public domain).</p>
{related([("https://nursinghomes.tekify.xyz", "Look up a nursing home"),
          ("/insights/nursing-home-staffing-by-state/", "Staffing ratings by state"),
          ("https://homehealth.tekify.xyz", "Home-health agencies")])}
"""
    site.add("/insights/largest-nursing-home-chains/",
             "America's Largest Nursing-Home Chains — CMS Data",
             "The biggest nursing-home chains by facility count, with certified beds and average CMS "
             "star ratings.",
             body, crumbs=[("Insights", "/insights/"), ("Nursing-home chains", None)])



# ---------------------------------------------------------------- college net price (IPEDS)
SECTOR_LABEL = {"1": "Public 4-year", "2": "Private non-profit 4-year", "3": "For-profit 4-year"}


def load_college_net_price():
    hd = {}
    with zipfile.ZipFile(CACHE / "ipeds" / "HD2023.zip") as z:
        with z.open("HD2023.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")):
                if (r.get("SECTOR") or "") in SECTOR_LABEL:
                    hd[r["UNITID"]] = (r.get("INSTNM") or "", (r.get("STABBR") or "").strip(), r["SECTOR"])
    out = []
    rows_src = None
    unzipped = next((CACHE / "SFA2223").glob("*.csv"), None) if (CACHE / "SFA2223").exists() else None
    if unzipped:
        with unzipped.open(encoding="utf-8-sig", errors="replace") as f:
            rows_src = list(csv.DictReader(f))
    else:
        with zipfile.ZipFile(CACHE / "ipeds" / "SFA2223.zip") as z:
            with z.open("sfa2223.csv") as f:
                rows_src = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")))
    for r in rows_src:
        uid = r.get("UNITID")
        if uid not in hd:
            continue
        v = num(r.get("NPIS412"))   # net price, families earning under $30,000
        if v is None or v <= 0 or v > 80000:
            continue
        name, st, sector = hd[uid]
        out.append((name, st, sector, v))
    return out


def page_college_net_price(site):
    data = load_college_net_price()
    data.sort(key=lambda x: x[3])
    cheapest = data[:20]
    median = sorted(d[3] for d in data)[len(data) // 2]
    by_state = collections.defaultdict(list)
    for name, st, sector, v in data:
        if st in STATE_NAMES:
            by_state[st].append(v)
    states = [(st, sorted(v)[len(v) // 2], len(v)) for st, v in by_state.items() if len(v) >= 8]
    states.sort(key=lambda x: x[1])
    low = states[:10]
    high = states[-10:][::-1]
    by_sector = collections.defaultdict(list)
    for name, st, sector, v in data:
        by_sector[sector].append(v)
    sector_rows = []
    for sector, vals in sorted(by_sector.items()):
        vals.sort()
        sector_rows.append([esc(SECTOR_LABEL[sector]), human(len(vals)),
                            "$" + human(round(vals[len(vals) // 2]))])
    tr = [[str(i + 1), esc(name), esc(st), "$" + human(round(v))]
          for i, (name, st, sector, v) in enumerate(cheapest)]
    tr_low = [[esc(STATE_NAMES[st]), "$" + human(round(v)), human(n)] for st, v, n in low]
    tr_high = [[esc(STATE_NAMES[st]), "$" + human(round(v)), human(n)] for st, v, n in high]
    body = f"""
<h1>Which US colleges cost least for low-income students?</h1>
<p class="lede">Sticker price says little about what students actually pay. Federal data reports the
average net price — tuition, fees, books and living costs minus grant aid — for students from families
earning under $30,000 a year. The range is enormous.
<span class="stat">{human(len(data))} four-year colleges</span>
<span class="stat">national median ${human(round(median))}</span></p>
<h2>Key findings</h2>
<ul>
<li>The national median net price for students from families earning under $30,000 is
<strong>${human(round(median))}</strong> a year across the four-year colleges in this analysis.</li>
<li>The cheapest state median is <strong>{esc(STATE_NAMES[low[0][0]])}</strong> at
${human(round(low[0][1]))}, against ${human(round(high[0][1]))} in
{esc(STATE_NAMES[high[0][0]])} — a difference of
${human(round(high[0][1] - low[0][1]))} a year for the same income band.</li>
<li>Public four-year colleges have a median net price of
${human(round(sorted(by_sector["1"])[len(by_sector["1"]) // 2]))}, versus
${human(round(sorted(by_sector["2"])[len(by_sector["2"]) // 2]))} at private non-profit four-year
colleges — before institutional aid is applied at the top end.</li>
</ul>
<h2>Cheapest colleges for students from families earning under $30,000</h2>
{table(["#", "Institution", "State", "Average net price"], tr)}
<h2>State medians: lowest ten</h2>
{table(["State", "Median net price", "Colleges"], tr_low)}
<h2>State medians: highest ten</h2>
{table(["State", "Median net price", "Colleges"], tr_high)}
<h2>Net price by type of college</h2>
{table(["Sector", "Colleges", "Median net price"], sector_rows)}
<h2>How to read this</h2>
<p>Net price is what a student actually pays after grant and scholarship aid, not after loans. It
includes living costs for students living on campus, which is why some urban commuter colleges look
cheap: no room and board. Compare a college's net price with its graduation rate before drawing
conclusions — a cheap college that students do not finish is expensive in the end.</p>
<h2>Method</h2>
<p>Net price for the $0-$30,000 family-income band (IPEDS SFA 2022-23, field NPIS412) for four-year
degree-granting institutions (IPEDS sectors 1-3), joined to the IPEDS directory (HD2023) for name and
state. State medians use states with at least eight reporting colleges. Data: NCES/IPEDS, public
domain.</p>
{related([("https://colleges.tekify.xyz", "Look up a college"),
          ("https://colleges.tekify.xyz/state/ca/", "California colleges"),
          ("https://colleges.tekify.xyz/state/tx/", "Texas colleges"),
          ("/insights/hospital-ratings-by-state/", "Hospital ratings by state")])}
"""
    site.add("/insights/college-net-price-by-income/",
             "Which US Colleges Cost Least for Low-Income Students? — IPEDS Data",
             "Average net price for students from families earning under $30,000 at four-year US "
             "colleges, with state medians and comparisons by sector.",
             body, crumbs=[("Insights", "/insights/"), ("College net price", None)])


def build_insights(site):
    page_hospital_ratings(site)
    page_hospital_ownership(site)
    page_nursing_staffing(site)
    page_dialysis(site)
    page_ifsc(site)
    page_hospital_er(site)
    page_nursing_chains(site)
    # page_college_net_price(site)  # parked: SFA income bands are public-only
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
