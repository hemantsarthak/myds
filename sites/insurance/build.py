#!/usr/bin/env python3
"""Build insurance.tekify.xyz — US health insurance marketplace plans by county (2026 plan year).

Input : .cache/insurance/{plans.json,counties.json,meta.json}  (from sites/insurance/fetch_data.py,
        CMS Exchange Public Use Files, public domain)
Output: site/ (~2.1k pages)

Pages
  /county/<state>-<county>/   one per county: plans, cheapest premium by metal, age table (2,055)
  /state/<ST>/                counties in a state + state summary (30)
  /guides/                    explainers: choosing a plan, subsidies, metal tiers, enrollment
  /search/  /                 search + home
  /data/counties.json         compact search index
"""
import collections
import json
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.sitegen import Site, table, cards, related, faq, esc, slug, human, notice  # noqa: E402

CACHE = ROOT / ".cache" / "insurance"
YEAR = 2026
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
    "PR": "Puerto Rico", "VI": "U.S. Virgin Islands", "GU": "Guam",
}
METALS = ["Bronze", "Silver", "Gold", "Platinum", "Catastrophic"]
METAL_NORM = {"Expanded Bronze": "Bronze"}


def money(v):
    return f"${v:,.0f}" if v is not None else "—"


def load():
    plans = json.loads((CACHE / "plans.json").read_text(encoding="utf-8"))
    counties = json.loads((CACHE / "counties.json").read_text(encoding="utf-8"))
    meta = json.loads((CACHE / "meta.json").read_text(encoding="utf-8"))
    for pid, p in plans.items():
        p["metal"] = METAL_NORM.get(p["metal"], p["metal"])
        p["p40"] = p.get("p40") or p.get("p21")
    return plans, counties, meta


def county_stats(plans, counties):
    out = {}
    for fips, c in counties.items():
        dps = [plans[pid] for pid in c["plans"] if pid in plans]
        if not dps:
            continue
        best = {}
        for p in dps:
            m = p["metal"]
            if p["p40"] is None:
                continue
            if m not in best or p["p40"] < best[m]:
                best[m] = p["p40"]
        silver = [p["p40"] for p in dps if p["metal"] == "Silver" and p["p40"] is not None]
        if not best:
            continue  # no listed rates for the county in this file — no useful page
        out[fips] = {
            "state": c["state"],
            "name": c["name"],
            "url": f"/county/{c['state'].lower()}-{slug(c['name'])}/",
            "plans": dps,
            "best": best,
            "benchmark": min(silver) if silver else None,
            "issuers": len({p["issuer"] for p in dps}),
        }
    return out


def build() -> Site:
    plans, counties, meta = load()
    stats = county_stats(plans, counties)
    by_state = collections.defaultdict(list)
    for fips, s in stats.items():
        by_state[s["state"]].append(s)
    for lst in by_state.values():
        lst.sort(key=lambda s: s["name"])

    s = Site(
        "insurance", "US Health Insurance Marketplace", "healthinsurance.tekify.xyz",
        "Find ACA marketplace health insurance plans by county: premiums by age, metal tiers, "
        "issuers, deductibles and out-of-pocket limits (2026 plan year, CMS data).",
        "Compare individual-market health insurance plans by county: monthly premiums for ages "
        "21, 40 and 60, metal levels, deductibles, out-of-pocket maximums and the insurers "
        "offering coverage. Data from the CMS Exchange public use files.",
        nav=[("Search", "/search/"), ("States", "/#states"), ("Guides", "/guides/")],
        source_note="Data: Centers for Medicare & Medicaid Services (CMS) Exchange Public Use Files "
                    f"(plan attributes, rates, service areas) for the {YEAR} plan year, public domain. "
                    "Premiums are listed rates for a single non-smoking adult before any premium tax "
                    "credit. This site is informational, not insurance advice.",
    )

    # ---------- home
    west = sorted(by_state.items(), key=lambda kv: -len(kv[1]))
    n_counties = len(stats)
    all_bench = [s["benchmark"] for s in stats.values() if s["benchmark"]]
    med_bench = statistics.median(all_bench) if all_bench else None
    home = f"""
<h1>Health insurance marketplace plans by US county</h1>
<p class="lede">Compare ACA marketplace plans in your county: monthly premiums for ages 21, 40 and
60, metal levels, deductibles, out-of-pocket maximums and the insurers offering coverage
({YEAR} plan year — the latest CMS public file).
<span class="stat">{human(meta['plans'])} plans</span>
<span class="stat">{human(meta['issuers'])} issuer filings</span>
<span class="stat">{human(n_counties)} counties</span></p>
<input type="search" id="q" placeholder="County or state, e.g. Travis, Texas…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2 id="states">Browse by state</h2>
{cards([(f"/state/{st.lower()}/", STATE_NAMES.get(st, st), f"{len(v)} counties") for st, v in west])}
<h2>What this data shows</h2>
<p>The public use files behind this site list every certified plan offered on the federally
facilitated marketplace, the counties each plan's service area covers, and the monthly rate for
every age. The figures here are <strong>listed premiums before tax credits</strong> for one
non-smoking adult — most buyers qualify for a premium tax credit that lowers the cost, based on
household income. Use the county pages to see what is actually sold where you live, then get an
official subsidy estimate and enrol at HealthCare.gov.</p>
<h2>Typical cost</h2>
<p>Across the counties in this file the <strong>median cheapest silver plan</strong> for a
40-year-old is <strong>{money(med_bench)} a month</strong>; the cheapest bronze plans are lower,
gold and platinum higher. Rural counties often have fewer insurers and higher premiums than metro
counties.</p>
{notice("This site reproduces CMS public data for information only. Rates shown are for a single "
        "non-smoking adult and change with age, tobacco use, plan and location. Enrol or get an "
        "official price at HealthCare.gov or your state marketplace.")}
"""
    s.add("/", f"Health Insurance Marketplace Plans by County ({YEAR}) — Tekify",
          f"Compare ACA marketplace health insurance plans by county: {YEAR} premiums by age, metal "
          f"levels, deductibles, out-of-pocket limits and insurers. {human(n_counties)} counties, "
          f"{human(meta['plans'])} plans.", home)

    s.add("/search/", "Search Marketplace Plans by County",
          "Search ACA marketplace counties and states.",
          """<h1>Search health insurance plans by county</h1>
<p class="lede">Type a county or state name. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Travis, Miami-Dade, Ohio…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---------- state pages
    state_url = {st: f"/state/{st.lower()}/" for st in by_state}
    for st, lst in sorted(by_state.items(), key=lambda kv: STATE_NAMES.get(kv[0], kv[0])):
        sname = STATE_NAMES.get(st, st)
        benches = [x["benchmark"] for x in lst if x["benchmark"]]
        med = statistics.median(benches) if benches else None
        issuers = len({p["issuer"] for x in lst for p in x["plans"]})
        plans_n = len({p["id"] for x in lst for p in x["plans"]})
        rows = "".join(
            f'<tr><td><a href="{x["url"]}">{esc(x["name"])}</a></td>'
            f'<td>{money(x["benchmark"])}</td><td>{len(x["plans"])}</td><td>{x["issuers"]}</td></tr>'
            for x in lst)
        body = f"""
<h1>Health insurance plans in {esc(sname)} ({YEAR})</h1>
<p class="lede">{human(len(lst))} counties, {human(plans_n)} marketplace plans and {human(issuers)}
insurer filings in this CMS file. Median cheapest silver plan for a 40-year-old:
<strong>{money(med)} a month</strong> before tax credits.</p>
<table>
<tr><th>County</th><th>Cheapest silver (age 40)</th><th>Plans</th><th>Insurers</th></tr>{rows}
</table>
<h2>How to use this</h2>
<p>Premiums vary by county within a state because insurers file rates by rating area and plan
service areas. Pick your county for the full plan list with metal levels, deductibles and
out-of-pocket maximums, then check your subsidy estimate and enrol at HealthCare.gov.</p>
{related([("/guides/how-to-choose-a-health-insurance-plan/", "How to choose a plan"),
          ("/guides/aca-premium-tax-credits/", "How premium tax credits work"),
          ("/guides/metal-tiers-explained/", "Bronze vs Silver vs Gold")])}
"""
        s.add(state_url[st], f"Health Insurance Plans in {sname} ({YEAR}) — Premiums by County",
              f"ACA marketplace plans in {sname} for {YEAR}: cheapest silver and bronze premiums by "
              f"county for ages 21-60, plan counts and insurers.", body,
              crumbs=[("States", "/#states"), (sname, None)])

    # ---------- county pages
    for fips, x in sorted(stats.items(), key=lambda kv: (kv[1]["state"], kv[1]["name"])):
        st, sname = x["state"], STATE_NAMES.get(x["state"], x["state"])
        dps = sorted(x["plans"], key=lambda p: (p["p40"] is None, p["p40"] or 0))
        best_rows = "".join(
            f'<tr><td>{m}</td><td>{money(x["best"].get(m))}</td>'
            f'<td>{sum(1 for p in dps if p["metal"] == m)}</td></tr>'
            for m in METALS if x["best"].get(m) is not None)
        plan_rows = "".join(
            f'<tr><td>{esc(p["issuer_name"] or p["issuer"])}</td><td>{esc(p["name"])}'
            f'{(" · " + esc(p["variant"])) if p.get("variant") and p["variant"] not in p["name"] else ""}</td>'
            f'<td>{esc(p["metal"])}</td><td>{esc(p["type"])}</td>'
            f'<td>{money(p["ded"])}</td><td>{money(p["moop"])}</td><td>{money(p["p40"])}</td></tr>'
            for p in dps[:40])
        more = f"<p class=\"mut\">Showing 40 of {len(dps)} plans, cheapest first.</p>" if len(dps) > 40 else ""
        silver = [p for p in dps if p["metal"] == "Silver" and p["p40"]]
        age_rows = ""
        if silver:
            ap = min(silver, key=lambda p: p["p40"])
            age_rows = "".join(
                f'<tr><td>{age}</td><td>{money(ap.get("p" + age))}</td></tr>' for age in ("21", "40", "60"))
        body = f"""
<h1>Health insurance plans in {esc(x["name"])}, {esc(st)} ({YEAR})</h1>
<p class="lede">{human(len(dps))} marketplace plans from {human(x["issuers"])} insurers are offered in
{esc(x["name"])}. The cheapest silver plan is <strong>{money(x["benchmark"])} a month</strong> for a
40-year-old non-smoker before tax credits.</p>
<h2>Cheapest monthly premium by metal level (age 40)</h2>
<table><tr><th>Metal level</th><th>Cheapest premium</th><th>Plans</th></tr>{best_rows}</table>
<h2>All plans in {esc(x["name"])}</h2>
<table>
<tr><th>Insurer</th><th>Plan</th><th>Metal</th><th>Type</th><th>Deductible</th><th>Out-of-pocket max</th><th>Premium (age 40)</th></tr>
{plan_rows}
</table>
{more}
{f'<h2>How the premium changes with age</h2><p>Cheapest silver plan by age (the same plan):</p><table><tr><th>Age</th><th>Monthly premium</th></tr>{age_rows}</table>' if age_rows else ''}
<h2>About these numbers</h2>
<p>Premiums are the CMS-listed rate for a single non-smoking adult, before any premium tax credit.
Most marketplace buyers qualify for a credit based on household income — the actual price can be
far lower than the list rate, especially for silver plans. Deductibles and out-of-pocket maximums
are for in-network care and vary by plan design. Check doctor and hospital networks before
enrolling: a cheaper plan that excludes your doctors is not cheaper.</p>
{related([(state_url[st], f"All counties in {sname}"),
          ("/guides/how-to-choose-a-health-insurance-plan/", "How to choose a plan"),
          ("/guides/aca-premium-tax-credits/", "Premium tax credits explained"),
          ("/guides/metal-tiers-explained/", "Metal tiers explained")])}
{faq([
    (f"What is the cheapest health insurance plan in {x['name']} County?",
     f"The cheapest plan for a 40-year-old non-smoker is {money(min(x['best'].values()))} a month "
     f"({min(x['best'], key=x['best'].get)} metal level) before tax credits, based on {YEAR} CMS rate "
     f"filings. The cheapest silver plan, the benchmark for subsidies, is {money(x['benchmark'])}."),
    (f"How much does health insurance cost in {x['name']} County?",
     f"For a 40-year-old non-smoker the cheapest plans in {x['name']} start around "
     f"{money(min(x['best'].values()))} a month before subsidies. Silver plans cost from "
     f"{money(x['benchmark'])}; premiums rise with age and tobacco use."),
    (f"How many insurers offer marketplace plans in {x['name']} County?",
     f"{human(x['issuers'])} insurers filed {human(len(dps))} plan options for this county in the "
     f"{YEAR} CMS file."),
])}
"""
        s.add(x["url"], f"Health Insurance Plans in {x['name']}, {st} ({YEAR}) — Premiums & Plans",
              f"{YEAR} marketplace plans in {x['name']} County, {st}: cheapest silver "
              f"{money(x['benchmark'])}/mo for age 40, {len(dps)} plans, {x['issuers']} insurers, "
              f"deductibles and out-of-pocket limits.",
              body, crumbs=[("States", "/#states"), (sname, state_url[st]), (x["name"], None)])

    # ---------- guides
    s.add("/guides/metal-tiers-explained/", "Bronze, Silver, Gold and Platinum Plans Explained",
          "What the ACA metal levels mean: actuarial value, deductibles, out-of-pocket maximums, "
          "and why silver plans are the benchmark for premium tax credits.",
          f"""<h1>Bronze, Silver, Gold and Platinum plans explained</h1>
<p class="lede">The metal level tells you how much of an average person's medical costs the plan
pays — not how good the plan is for you.</p>
<h2>Actuarial value</h2>
<p>Metal levels correspond to <strong>actuarial value</strong>: the share of covered benefits the
plan pays for a standard population. Bronze ≈ 60%, Silver ≈ 70%, Gold ≈ 80%, Platinum ≈ 90%.
Catastrophic plans pay less and are only available to people under 30 or with a hardship
exemption.</p>
<h2>What that means in practice</h2>
<p><strong>Bronze</strong> has the lowest premium and the highest deductible — good if you rarely
need care but want protection from a catastrophe. <strong>Silver</strong> costs more per month but
has a lower deductible, and it is the only level where people with income up to 250% of the federal
poverty level can get <strong>cost-sharing reductions</strong>, which can make a silver plan
cheaper overall than bronze. <strong>Gold</strong> and <strong>Platinum</strong> have higher
premiums and lower costs when you use care — better for people who expect regular treatment.</p>
<h2>Why silver is the benchmark</h2>
<p>Premium tax credits are calculated against the second-lowest-cost silver plan in your area (the
"benchmark plan"). That is why the silver price on each county page matters even if you intend to
buy bronze or gold.</p>
<h2>The real decision</h2>
<p>Compare total expected cost, not just the premium: premium × 12 + deductible you expect to use +
copays + the drugs you take, all within the network. Check that your doctors and hospitals are
in-network, and check prescription formularies.</p>
{related([("/guides/how-to-choose-a-health-insurance-plan/", "How to choose a plan"),
          ("/guides/aca-premium-tax-credits/", "Premium tax credits")])}""",
          crumbs=[("Guides", "/guides/"), ("Metal tiers", None)])

    s.add("/guides/aca-premium-tax-credits/", "How ACA Premium Tax Credits Work",
          "How marketplace premium tax credits are calculated (benchmark silver, income and family "
          "size), advance payments versus claiming at tax time, and where to get an official "
          "estimate.",
          """<h1>How ACA premium tax credits work</h1>
<p class="lede">The listed premium is not what most people pay. A premium tax credit can cover most
or all of the cost, depending on household income and family size.</p>
<h2>The idea</h2>
<p>The marketplace caps what you pay for the <strong>benchmark silver plan</strong> (the second-
lowest-cost silver plan in your area) at a percentage of your household income. If the benchmark
costs more than that percentage, the difference is paid as a tax credit. You can apply it to any
metal level, though the credit is always calculated from the benchmark silver price.</p>
<h2>What counts as income</h2>
<p>Credits use <strong>modified adjusted gross income</strong> (MAGI) of everyone on the tax return,
plus certain tax-exempt income, and the number of people in your household. Reporting income
changes during the year matters: if your actual income differs from the estimate, you settle up on
your tax return.</p>
<h2>Advance vs. tax time</h2>
<p>You can take the credit in advance as a reduction in the monthly premium, or claim it when you
file. Advance is usual, but overestimating income means repaying some credit later — estimate
carefully and update the marketplace if your income changes.</p>
<h2>Cost-sharing reductions</h2>
<p>People with income up to 250% of the federal poverty level who buy a <strong>silver</strong>
plan may also get cost-sharing reductions: lower deductibles, copays and out-of-pocket maximums.
This is another reason silver can be the best value at lower incomes.</p>
<h2>Policy changes</h2>
<p>Subsidy rules have changed several times, and temporary enhancements have been extended by
Congress at various points. Always get the current rules and an official estimate from
<a href="https://www.healthcare.gov/lower-costs/">HealthCare.gov</a> or your state marketplace
before enrolling.</p>
{related([("/guides/metal-tiers-explained/", "Metal tiers"),
          ("/guides/how-to-choose-a-health-insurance-plan/", "Choosing a plan"),
          ("/guides/open-enrollment-and-special-enrollment/", "Enrollment periods")])}""",
          crumbs=[("Guides", "/guides/"), ("Premium tax credits", None)])

    s.add("/guides/how-to-choose-a-health-insurance-plan/", "How to Choose a Health Insurance Plan",
          "A practical checklist: estimate subsidies first, compare total cost not just premiums, "
          "check networks and drugs, understand deductibles and out-of-pocket maximums, and avoid "
          "coverage gaps.",
          """<h1>How to choose a health insurance plan</h1>
<p class="lede">Start with the subsidy estimate, then compare total expected cost — premium,
deductible, copays and drugs — inside the network.</p>
<h2>1. Get the subsidy estimate first</h2>
<p>The list premiums on this site are before tax credits. Enter income and household size at
HealthCare.gov (or your state marketplace) to see the real monthly price. Do this before comparing
plans: the credit changes the ranking, and silver plans can get cost-sharing reductions at lower
incomes.</p>
<h2>2. Compare total cost</h2>
<p>Premium × 12 + expected deductible use + copays + prescriptions. A bronze plan with a
$7,000 deductible can be the right choice for someone who rarely uses care; a silver plan with a
lower deductible often wins for anyone who will use care regularly.</p>
<h2>3. Check the network</h2>
<p>HMO, EPO, PPO and POS plans differ in whether you need referrals and whether out-of-network care
is covered. Verify your doctors, hospital and preferred pharmacy are in-network for the exact plan —
networks are plan-specific, not insurer-wide.</p>
<h2>4. Check prescriptions</h2>
<p>Look up each drug on the plan's formulary and check the tier and prior-authorisation rules. A
cheap premium is irrelevant if a needed drug costs hundreds a month.</p>
<h2>5. Check the out-of-pocket maximum</h2>
<p>This is your worst-case yearly exposure for in-network care. A lower premium with a much higher
out-of-pocket maximum may not be the safer choice if a hospital stay is likely.</p>
<h2>6. Enrol on time</h2>
<p>Open enrollment for the next plan year runs November 1 – January 15 on the federal marketplace
(with a December 15 deadline for January 1 coverage). Outside that window you need a qualifying
life event for a special enrollment period. Do not let coverage lapse — a gap can delay new
coverage.</p>
{related([("/guides/metal-tiers-explained/", "Metal tiers explained"),
          ("/guides/aca-premium-tax-credits/", "Premium tax credits"),
          ("/search/", "Find your county")])}""",
          crumbs=[("Guides", "/guides/"), ("Choosing a plan", None)])

    s.add("/guides/open-enrollment-and-special-enrollment/", "Open Enrollment and Special Enrollment Periods",
          "When you can enroll in marketplace coverage, the federal deadlines, and the qualifying "
          "life events that open a special enrollment period.",
          """<h1>Open enrollment and special enrollment periods</h1>
<p class="lede">Marketplace coverage is not sold year-round. There is one annual window — and a set
of life events that open a special window.</p>
<h2>Open enrollment</h2>
<p>On the federal marketplace, open enrollment for the next plan year runs <strong>November 1 to
January 15</strong>. To have coverage on January 1, enrol by <strong>December 15</strong>. States
that run their own marketplaces set their own dates, often similar but not identical. Outside these
dates you cannot newly enrol or change plans without a special enrollment period (Medicaid and CHIP
are open year-round).</p>
<h2>Special enrollment periods</h2>
<p>Qualifying life events include: losing other health coverage (including losing a job-based plan
or aging off a parent's plan), moving to a new area, marriage or divorce, having a baby or adopting,
death of someone on the plan, and changes in immigration status. You generally have <strong>60
days</strong> from the event to enrol; coverage typically starts the first of the month after you
enrol.</p>
<h2>What you will need</h2>
<p>Proof of the event (termination letter, marriage certificate, lease), Social Security numbers,
immigration documents if applicable, employer information and income estimates. Start the
application early — the marketplace can require documents and delays are common.</p>
<h2>Missed the window?</h2>
<p>Check whether you qualify for Medicaid or CHIP (year-round, income-based), a short-term plan
(limited benefit — read the exclusions), or your state's high-risk pool. Also check
HealthCare.gov for any extended enrollment periods announced for the current year.</p>
{related([("/guides/how-to-choose-a-health-insurance-plan/", "Choosing a plan"),
          ("/guides/aca-premium-tax-credits/", "Premium tax credits")])}""",
          crumbs=[("Guides", "/guides/"), ("Enrollment", None)])

    s.add("/guides/short-term-health-plans/", "Short-Term Health Plans vs ACA Plans: What You Give Up",
          "Why short-term plans look cheap, what they can exclude (pre-existing conditions, "
          "essential benefits), how long they last, and when buying one is a costly mistake.",
          """<h1>Short-term health plans vs ACA plans</h1>
<p class="lede">A short-term plan can cost a fraction of a marketplace premium — because it is
allowed to cover far less. Read what it excludes before you buy.</p>
<h2>Why they are cheaper</h2>
<p>Short-term limited-duration plans are not required to cover the ACA's essential health benefits,
can <strong>exclude or charge more for pre-existing conditions</strong> through medical
underwriting, can cap annual or lifetime benefits, may exclude prescription drugs, maternity care
and mental health, and can rescind coverage if the application was inaccurate. They also cannot be
bought with a premium tax credit, so the subsidy comparison is not apples-to-apples.</p>
<h2>How long they last</h2>
<p>Federal rules limit short-term plans to short durations (with renewals permitted under current
rules in many states), but states can be stricter — some effectively ban them. Check your state's
rules before relying on one.</p>
<h2>When a short-term plan can make sense</h2>
<p>Only as a bridge for someone healthy, with no pre-existing conditions, who needs temporary
coverage between jobs or while awaiting an ACA plan start date — and who can afford the risk that
a new condition will not be covered until the ACA plan begins. Never choose one knowing you need
care: the exclusions are exactly where you would need the coverage.</p>
<h2>The safer alternatives</h2>
<p>Check for a <strong>special enrollment period</strong> (job loss, moving, marriage), Medicaid/CHIP
eligibility (year-round), COBRA from a former employer, or a parent's plan if under 26. Compare the
full cost of a subsidised silver plan against the short-term premium plus the deductible you would
face if something happened.</p>
{related([("/guides/cobra-vs-marketplace/", "COBRA vs marketplace"),
          ("/guides/how-to-choose-a-health-insurance-plan/", "How to choose a plan"),
          ("/guides/open-enrollment-and-special-enrollment/", "Enrollment periods")])}""",
          crumbs=[("Guides", "/guides/"), ("Short-term plans", None)])

    s.add("/guides/cobra-vs-marketplace/", "COBRA vs Marketplace: Which Is Cheaper After a Job Loss?",
          "How to compare COBRA continuation coverage with a subsidised marketplace plan: premiums, "
          "networks, subsidies, deadlines and what to check before choosing.",
          """<h1>COBRA vs marketplace after a job loss</h1>
<p class="lede">COBRA keeps your current doctors and plan; the marketplace can be much cheaper
because of premium tax credits. The right answer depends on your income, your network and how
quickly you need coverage.</p>
<h2>What COBRA is</h2>
<p>COBRA lets you keep a former employer's group plan for a limited period (often 18 months),
but you pay the <strong>full premium</strong> the employer and employee together were paying, plus
up to a 2% administrative fee. The coverage itself does not change — same network, same deductible,
same prescriptions.</p>
<h2>What the marketplace offers</h2>
<p>Losing job-based coverage is a qualifying life event: you get a <strong>special enrollment
period</strong> (generally 60 days) to buy a marketplace plan. If your income qualifies, a premium
tax credit can make a silver plan far cheaper than the COBRA premium — and cost-sharing reductions
can lower the deductible further at lower incomes. The trade-off: a new network, new deductible,
and the plan must be chosen quickly.</p>
<h2>How to compare fairly</h2>
<p>Compare annual cost, not monthly premium: premium × 12 + deductible you expect to use + copays +
prescriptions, for the doctors and hospitals you actually see. A COBRA plan with a low premium but
out-of-network doctors after a move is not cheaper in practice.</p>
<h2>Practical steps</h2>
<ol>
<li>Get the COBRA election notice and premium in writing; note the deadline (often 60 days).</li>
<li>Start a marketplace application the same week — the SEP clock is short.</li>
<li>Estimate income for the year; the subsidy depends on annual modified adjusted gross income.</li>
<li>Check doctors, hospitals and drugs against both options before electing.</li>
<li>Keep proof of the coverage loss for the marketplace application.</li>
</ol>
<p>You can choose either — you cannot have both for the same coverage period, and dropping COBRA
later does not reopen a special enrollment period. Decide with the full-year numbers.</p>
{related([("/guides/short-term-health-plans/", "Short-term plans vs ACA"),
          ("/guides/aca-premium-tax-credits/", "How premium tax credits work"),
          ("/guides/open-enrollment-and-special-enrollment/", "Enrollment periods")])}""",
          crumbs=[("Guides", "/guides/"), ("COBRA vs marketplace", None)])

    s.add("/guides/", "Guides — US Health Insurance Marketplace",
          "Explainers on metal tiers, premium tax credits, choosing a plan, enrollment periods, "
          "short-term plans and COBRA.",
          "<h1>Guides</h1><p class=\"lede\">Plain explainers for choosing and paying for marketplace coverage.</p>"
          + cards([("/guides/metal-tiers-explained/", "Bronze, Silver, Gold, Platinum",
                    "What metal levels mean and why silver is the subsidy benchmark."),
                   ("/guides/aca-premium-tax-credits/", "How premium tax credits work",
                    "Benchmark silver, income and family size, advance vs. tax time."),
                   ("/guides/how-to-choose-a-health-insurance-plan/", "How to choose a plan",
                    "Total cost, networks, drugs, out-of-pocket maximum and deadlines."),
                   ("/guides/open-enrollment-and-special-enrollment/", "Enrollment periods",
                    "Open enrollment dates and the life events that open a special window."),
                   ("/guides/short-term-health-plans/", "Short-term plans vs ACA plans",
                    "What short-term plans can exclude - and when they are a mistake."),
                   ("/guides/cobra-vs-marketplace/", "COBRA vs marketplace",
                    "How to compare COBRA and a subsidised marketplace plan after a job loss.")]),
          crumbs=[("Guides", None)])

    # ---------- data index for search
    idx = [[x["name"], x["state"], x["url"]] for x in stats.values()]
    s.add_file("/data/counties.json", json.dumps(idx, separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(stats))} counties, {human(meta['plans'])} plan "
                    f"filings and {human(meta['issuers'])} issuer filings from the CMS Exchange Public "
                    f"Use Files for the {YEAR} plan year (public domain). Premiums are listed rates for "
                    f"a single non-smoking adult before premium tax credits. Plan and rate data covers "
                    f"the federally facilitated marketplace states; state-based marketplaces publish "
                    f"separate data.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/counties.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' counties indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(h){return (h[0]+' '+h[1]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML = out.length ? '<div class="grid">'+out.slice(0,40).map(function(h){
      return '<a href="'+h[2]+'">'+esc(h[0])+' <span class="mut">'+esc(h[1])+'</span></a>';
    }).join('')+'</div>' : '<p class="mut">No county found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
