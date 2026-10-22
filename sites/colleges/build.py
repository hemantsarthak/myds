#!/usr/bin/env python3
"""Build colleges.tekify.xyz — a US college / university directory from IPEDS.

Answers the questions people actually search for each institution: acceptance rate, tuition,
enrollment, graduation rate, location and website.

Input : .cache/ipeds/{HD2023,ADM2023,IC2023_AY,EF2023A,GR2023}
Output: site/ (~6.1k pages)

Pages
  /college/<slug>/   one page per active institution (degree-granting and non-degree)
  /state/<ST>/       colleges in a state (52)
  /guides/           explainers (engine/guides.py)
  /search/  /        search + browse
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
from engine.guides import add_guides  # noqa: E402

CACHE = ROOT / ".cache" / "ipeds"
PROJ = pathlib.Path(__file__).resolve().parent
LABELS = json.loads((PROJ / "labels.json").read_text(encoding="utf-8")) if (PROJ / "labels.json").exists() else {}

SECTOR = {
    "0": ("Administrative unit", "Other"),
    "1": ("Public 4-year", "public"), "2": ("Private nonprofit 4-year", "private nonprofit"),
    "3": ("Private for-profit 4-year", "private for-profit"),
    "4": ("Public 2-year", "public"), "5": ("Private nonprofit 2-year", "private nonprofit"),
    "6": ("Private for-profit 2-year", "private for-profit"),
    "7": ("Public less-than-2-year", "public"), "8": ("Private nonprofit less-than-2-year", "private nonprofit"),
    "9": ("Private for-profit less-than-2-year", "private for-profit"),
    "99": ("Unknown", "unknown"),
}
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
    "MP": "Northern Mariana Islands", "FM": "Micronesia", "MH": "Marshall Islands", "PW": "Palau",
}


def clean(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def num(v):
    """IPEDS numbers, or None when the field is suppressed/not applicable."""
    try:
        s = clean(str(v)).replace(",", "")
        return int(float(s))
    except (TypeError, ValueError):
        return None


def title_name(name: str) -> str:
    """IPEDS names are usually upper case; title-case the awkward ALL CAPS ones."""
    name = clean(name)
    if name.isupper() or (sum(1 for c in name if c.isupper()) > len(name) * 0.7):
        small = {"of", "the", "and", "at", "in", "for", "on", "a", "an", "de", "la"}
        out = []
        for i, w in enumerate(name.lower().split()):
            if w in small and i:
                out.append(w)
            elif w.startswith("("):
                out.append(w)
            else:
                out.append(w[:1].upper() + w[1:])
        name = " ".join(out)
        name = name.replace("'S ", "'s ").replace("'T ", "'t ")
    return name


def load():
    hd_path = next((CACHE / "HD2023").glob("*.csv"))
    admissions, charges, enrollment, grads = {}, {}, {}, {}
    with next((CACHE / "ADM2023").glob("*.csv")).open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            admissions[clean(r["UNITID"])] = r
    with next((CACHE / "IC2023_AY").glob("*.csv")).open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            charges[clean(r["UNITID"])] = r
    with next((CACHE / "EF2023A").glob("*.csv")).open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if clean(r["EFALEVEL"]) == "1":
                enrollment[clean(r["UNITID"])] = num(r["EFTOTLT"])
    with next((CACHE / "GR2023").glob("*.csv")).open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            uid, gtype = clean(r["UNITID"]), clean(r["GRTYPE"])
            if gtype in ("2", "3", "4"):
                grads.setdefault(uid, {})[gtype] = num(r["GRTOTLT"])

    # net price by income band (SFA2223, 2022-23) + retention/student-faculty ratio (EF2023D)
    netprice, retention = {}, {}
    sfa = next((CACHE / "SFA2223").glob("*.csv"), None)
    if sfa:
        with sfa.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                uid = clean(r["UNITID"])
                bands = []
                for col, label in (("NPIS412", "Under $30,000"), ("NPIS422", "$30,001–48,000"),
                                   ("NPIS432", "$48,001–75,000"), ("NPIS442", "$75,001–110,000"),
                                   ("NPIS452", "Over $110,000")):
                    v = num(r.get(col))
                    if v is not None:
                        bands.append((label, v))
                netprice[uid] = {"total": num(r.get("NPIST2")), "bands": bands}
    efd = next((CACHE / "EF2023D").glob("*.csv"), None)
    if efd:
        with efd.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                uid = clean(r["UNITID"])
                retention[uid] = {"ret_ft": num(r.get("RET_PCF")), "stufac": num(r.get("STUFACR"))}

    out = []
    with hd_path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            sector = clean(r["SECTOR"])
            if sector in ("0", "99") or clean(r["CYACTIVE"]) != "1":
                continue
            uid = clean(r["UNITID"])
            adm = admissions.get(uid, {})
            ch = charges.get(uid, {})
            apps, admd, enr = num(adm.get("APPLCN")), num(adm.get("ADMSSN")), num(adm.get("ENRLT"))
            instate = None
            if ch:
                t2, f2 = num(ch.get("TUITION2")), num(ch.get("FEE2"))
                if t2 is not None:
                    instate = t2 + (f2 or 0)
            outstate = None
            if ch:
                t3, f3 = num(ch.get("TUITION3")), num(ch.get("FEE3"))
                if t3 is not None:
                    outstate = t3 + (f3 or 0)
            g = grads.get(uid, {})
            cohort, completers = g.get("2"), g.get("3")
            grad_rate = round(100 * completers / cohort) if cohort and completers is not None and cohort >= 20 else None
            transfer_rate = round(100 * g["4"] / cohort) if cohort and g.get("4") is not None and cohort >= 20 else None
            try:
                lat, lon = float(r["LATITUDE"]), float(r["LONGITUD"])
            except (TypeError, ValueError):
                lat = lon = None
            out.append({
                "unitid": uid, "name": title_name(r["INSTNM"]),
                "city": title_name(r["CITY"]), "state": clean(r["STABBR"]), "zip": clean(r["ZIP"])[:5],
                "county": title_name(r["COUNTYNM"]), "sector": sector,
                "sector_label": SECTOR[sector][0], "control": SECTOR[sector][1],
                "level": {"1": "4-year", "2": "2-year"}.get(clean(r["ICLEVEL"]), "less-than-2-year"),
                "web": clean(r["WEBADDR"]), "phone": clean(r["GENTELE"]),
                "hbcu": clean(r["HBCU"]) == "1", "tribal": clean(r["TRIBAL"]) == "1",
                "lat": lat, "lon": lon,
                "enrollment": enrollment.get(uid), "apps": apps, "admitted": admd, "enrolled": enr,
                "accept": (round(100 * admd / apps) if apps and admd is not None else None),
                "sat_pct": num(adm.get("SATPCT")),
                "act_pct": num(adm.get("ACTPCT")),
                "sat_25": num(adm.get("SATVR25")), "sat_75": num(adm.get("SATVR75")),
                "act_25": num(adm.get("ACTCM25")), "act_75": num(adm.get("ACTCM75")),
                "tuition_in": instate, "tuition_out": outstate,
                "grad_rate": grad_rate, "transfer_rate": transfer_rate,
                "cohort": cohort,
                "net_price": netprice.get(uid, {}).get("total"),
                "np_bands": netprice.get(uid, {}).get("bands", []),
                "ret_ft": retention.get(uid, {}).get("ret_ft"),
                "stufac": retention.get(uid, {}).get("stufac"),
                "locale": (LABELS.get("LOCALE", {}).get(clean(r["LOCALE"])) or ""),
                "size_cat": (LABELS.get("INSTSIZE", {}).get(clean(r["INSTSIZE"])) or ""),
                "degree_top": (LABELS.get("HLOFFER", {}).get(clean(r["HLOFFER"])) or ""),
                "carnegie": (LABELS.get("C21BASIC", {}).get(clean(r["C21BASIC"])) or ""),
            })
    return out


def distance_km(a, b) -> float:
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def money(v) -> str:
    return f"${v:,}" if v else "—"


def pct(v) -> str:
    return f"{v}%" if v is not None else "—"


def build() -> Site:
    colleges = load()
    colleges.sort(key=lambda c: (-(c["enrollment"] or 0), c["name"]))
    used = collections.Counter()
    for c in colleges:
        base = slug(c["name"])
        used[base] += 1
        c["url"] = (f"/college/{base}/" if used[base] == 1 else f"/college/{base}-{c['unitid']}/")
    # Names are compared case-insensitively: "MotoRing Technical Training Institute" and
    # "Motoring Technical Training Institute" are different IPEDS records but produce the same
    # <title> once search engines lower-case it, which trips the site validator.
    name_counts = collections.Counter(c["name"].lower() for c in colleges)
    for c in colleges:
        c["label"] = (f'{c["name"]} ({c["city"]}, {c["state"]})'
                      if name_counts[c["name"].lower()] > 1 else c["name"])

    label_counts = collections.Counter(c["label"].lower() for c in colleges)
    for c in colleges:
        if label_counts[c["label"].lower()] > 1:
            c["label"] = f'{c["label"]} — campus {c["unitid"]}'

    by_state = collections.defaultdict(list)
    for c in colleges:
        by_state[c["state"]].append(c)
    grid = collections.defaultdict(list)
    for c in colleges:
        if c["lat"] is not None:
            grid[(int(c["lat"]), int(c["lon"]))].append(c)

    def nearby(c, limit=6):
        if c["lat"] is None:
            return []
        res = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for b in grid.get((int(c["lat"]) + dlat, int(c["lon"]) + dlon), ()):
                    if b["unitid"] == c["unitid"]:
                        continue
                    d = distance_km(c, b)
                    if d <= 150:
                        res.append((d, b))
        res.sort(key=lambda x: x[0])
        return res[:limit]

    big = [c for c in colleges if (c["enrollment"] or 0) >= 10000]
    states_sorted = sorted(by_state.items(), key=lambda kv: -sum((x["enrollment"] or 0) for x in kv[1]))
    state_url = {st: f"/state/{st.lower()}/" for st in by_state}

    s = Site("colleges", "US Colleges", "colleges.tekify.xyz",
             "US colleges and universities: acceptance rates, tuition, enrollment and graduation rates.",
             "Look up any US college or university: acceptance rate, tuition and fees, enrollment, "
             "graduation rate, location and official website — from federal IPEDS data.",
             nav=[("Search", "/search/"), ("States", "/#states"), ("Guides", "/guides/"), ("About", "/about/")],
             source_note="Data: US Department of Education, NCES IPEDS (2023 releases, public domain). "
                         "Tuition is the 2023-24 sticker price for full-time first-year students and "
                         "excludes room and board; graduation rates are the 150% cohort rate.")

    home = f"""
<h1>US colleges and universities</h1>
<p class="lede">Acceptance rates, tuition, enrollment and graduation rates for
{human(len(colleges))} US institutions, straight from federal IPEDS data.
<span class="stat">{human(len(colleges))} institutions</span>
<span class="stat">{len(by_state)} states &amp; territories</span>
<span class="stat">{human(len(big))} with 10,000+ students</span></p>
<input type="search" id="q" placeholder="Harvard, UCLA, community college…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2>Largest institutions</h2>
{cards([(c["url"], esc(c["name"]), human(c["enrollment"] or 0)) for c in colleges[:40]])}
<h2 id="states">Browse by state</h2>
{cards([(state_url[st], esc(STATE_NAMES.get(st, st)), human(len(v))) for st, v in states_sorted])}
<h2>What this directory answers</h2>
<p>Each page reports the numbers prospective students and parents actually compare: how many
students apply and are admitted (the acceptance rate), what the sticker price is for in-state and
out-of-state students, how large the student body is, and what share of students finish within
150% of normal time. All figures come from the federal IPEDS collection, the same source used by
the Department of Education's College Scorecard.</p>
{notice("Acceptance rate is admitted ÷ applicants for first-year students. Tuition is tuition and "
        "required fees only — it excludes housing, food, books and travel. A dash means the "
        "institution does not report that figure.")}
"""
    s.add("/", "US Colleges — Acceptance Rates, Tuition and Enrollment",
          "Compare US colleges and universities: acceptance rates, in-state and out-of-state "
          "tuition, enrollment and 150% graduation rates from federal IPEDS data.", home)

    s.add("/search/", "Search US Colleges and Universities",
          "Search US colleges by name, city or state and see acceptance rate, tuition and enrollment.",
          """<h1>Search US colleges</h1>
<p class="lede">Type a college name, city or state. The index loads once, then searches locally.</p>
<input type="search" id="q" placeholder="Harvard, Berkeley, Austin…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---- state pages
    for st, group in states_sorted:
        sname = STATE_NAMES.get(st, st)
        body = f"""
<h1>Colleges and universities in {esc(sname)}</h1>
<p class="lede">{human(len(group))} institutions in {esc(sname)}, ordered by enrollment. Each page
lists acceptance rate, tuition, graduation rate and location.</p>
{cards([(c["url"], esc(c["name"]), f'{human(c["enrollment"] or 0)} · {esc(c["control"])}') for c in group[:120]])}
<h2>About higher education in {esc(sname)}</h2>
<p>{esc(sname)} has {human(len(group))} institutions in this directory, from large public research
universities to small private and for-profit colleges. In-state tuition is usually far lower at
public institutions, while private colleges charge the same sticker price regardless of residence —
though most students receive institutional aid that lowers the actual net price.</p>
{related([("/#states", "All states"), ("/search/", "Search colleges"), ("/guides/", "Guides")])}
"""
        s.add(state_url[st], f"Colleges in {sname} — Acceptance Rates & Tuition",
              f"{human(len(group))} colleges and universities in {sname}: acceptance rates, tuition, "
              f"enrollment and graduation rates from federal IPEDS data.",
              body, crumbs=[("States", "/#states"), (sname, None)])

    # ---- college pages
    for c in colleges:
        sname = STATE_NAMES.get(c["state"], c["state"])
        loc = f'{c["city"]}, {c["state"]}'
        rows = [["Type", esc(c["sector_label"])],
                ["Control", esc(c["control"])],
                ["Level", esc(c["level"])],
                ["Location", f'{esc(loc)}{(" " + esc(c["zip"])) if c["zip"] else ""}'],
                ["County", esc(c["county"] or "—")],
                ["Enrollment", human(c["enrollment"]) if c["enrollment"] else "—"],
                ["Acceptance rate", pct(c.get("accept"))],
                ["Applicants / admitted", (f'{human(c["apps"])} / {human(c["admitted"])}'
                                           if c["apps"] and c["admitted"] is not None else "—")],
                ["In-state tuition &amp; fees", money(c["tuition_in"])],
                ["Out-of-state tuition &amp; fees", money(c["tuition_out"])],
                ["Graduation rate (150%)", pct(c.get("grad_rate"))],
                ["Transfer-out rate", pct(c.get("transfer_rate"))],
                ]
        if c.get("stufac"):
            rows.append(["Student–faculty ratio", f'{c["stufac"]}:1'])
        if c.get("ret_ft") is not None:
            rows.append(["Full-time retention rate", pct(c["ret_ft"])])
        if c.get("net_price"):
            rows.append(["Average net price (after aid)", money(c["net_price"])])
        if c.get("locale"):
            rows.append(["Campus setting", esc(c["locale"])])
        if c.get("size_cat"):
            rows.append(["Size category", esc(c["size_cat"])])
        if c.get("degree_top"):
            rows.append(["Highest degree offered", esc(c["degree_top"])])
        if c["sat_25"] and c["sat_75"]:
            rows.append(["SAT middle 50% (EBRW+Math)", f'{c["sat_25"]}–{c["sat_75"]}'])
        if c["act_25"] and c["act_75"]:
            rows.append(["ACT middle 50%", f'{c["act_25"]}–{c["act_75"]}'])
        rows.append(["Website", f'<a href="https://{esc(c["web"].replace("https://","").replace("http://","").rstrip("/"))}" target="_blank" rel="nofollow noopener">{esc(c["web"])}</a>' if c["web"] else "—"])
        rows.append(["Phone", esc(c["phone"] or "—")])
        if c["hbcu"]:
            rows.append(["Classification", "Historically Black College or University (HBCU)"])
        if c["tribal"]:
            rows.append(["Classification", "Tribal College or University"])
        near = nearby(c)
        entr = human(c["enrollment"]) if c["enrollment"] else "an unreported number of"
        lede = (f'{esc(c["name"])} is a {esc(c["control"])} {esc(c["level"])} institution in {esc(loc)}. '
                f'It enrolls about {entr} students')
        if c.get("accept") is not None:
            lede += f' and admits roughly {c["accept"]}% of first-year applicants'
        lede += "."
        grad_txt = ""
        if c.get("grad_rate") is not None and c["cohort"]:
            grad_txt = (f"<p>Of the {human(c['cohort'])} first-time, full-time students in the "
                        f"150% cohort, <strong>{c['grad_rate']}%</strong> completed their programme "
                        f"within 150% of normal time. That cohort definition matters: part-time "
                        f"students and transfers are not included, so a college that serves many of "
                        f"them can have a low reported rate while still graduating most of its "
                        f"students.</p>")
        cost_txt = ""
        if c["tuition_in"]:
            if c["tuition_out"] and c["tuition_out"] != c["tuition_in"]:
                cost_txt = (f"<p>In-state students pay about <strong>{money(c['tuition_in'])}</strong> in "
                            f"tuition and required fees; out-of-state students pay "
                            f"<strong>{money(c['tuition_out'])}</strong>. These are 2023-24 sticker "
                            f"prices for full-time first-year students and exclude housing, food and "
                            f"books. Most students pay less than the sticker price after institutional "
                            f"grants and scholarships.</p>")
            else:
                cost_txt = (f"<p>Tuition and required fees are about "
                            f"<strong>{money(c['tuition_in'])}</strong> for full-time first-year "
                            f"students, the same for in-state and out-of-state students, which is "
                            f"typical of private institutions. Room and board are extra.</p>")
        accept_ans = (
            f'About {c["accept"]}% of first-year applicants are admitted, based on federal IPEDS '
            f'data for {human(c["apps"] or 0)} applicants.'
            if c.get("accept") is not None else
            f'{c["name"]} does not report a selective admission rate to IPEDS; it may have open admission.')
        if c["tuition_in"]:
            cost_ans = (f'Tuition and required fees are about {money(c["tuition_in"])} for '
                        f'in-state students')
            if c["tuition_out"] and c["tuition_out"] != c["tuition_in"]:
                cost_ans += f' and {money(c["tuition_out"])} for out-of-state students'
            cost_ans += ', excluding room and board.'
        else:
            cost_ans = (f'Tuition is not reported in the federal data for {c["name"]}; check the '
                        f'college website for current charges.')
        enroll_ans = (f'About {human(c["enrollment"])} students are enrolled.' if c["enrollment"]
                      else f'Enrollment is not reported for {c["name"]} in the fall enrollment file.')
        faq_pairs = [
            (f'What is the acceptance rate at {c["name"]}?', accept_ans),
            (f'How much does {c["name"]} cost?', cost_ans),
            (f'How many students attend {c["name"]}?', enroll_ans),
        ]
        np_section = ""
        if c["np_bands"]:
            band_rows = [[esc(lbl), money(v)] for lbl, v in c["np_bands"]]
            np_section = (
                "<h2>Cost after financial aid</h2>"
                + (f'<p>The average net price — what students actually pay after grants and '
                   f'scholarships — is <strong>{money(c["net_price"])}</strong> per year for '
                   f'first-time, full-time students receiving Title IV aid.</p>' if c["net_price"] else '')
                + table(["Family income", "Average net price"], band_rows)
                + '<p>Net price falls as family income falls because need-based aid rises. These are '
                  '2022-23 figures reported to IPEDS; use them to compare institutions, and use each '
                  "college's own net price calculator for a personal estimate.</p>")
        body = f"""
<h1>{esc(c["label"])}</h1>
<p class="lede">{lede}</p>
{table(["Field", "Value"], rows)}
<h2>Admissions</h2>
<p>{("About " + human(c["apps"]) + " students applied and " + human(c["admitted"]) + " were admitted") if c["apps"] and c["admitted"] is not None else "This institution does not report first-year admission figures to IPEDS, often because admission is open"}.
{(" Of those admitted, " + human(c["enrolled"]) + " enrolled.") if c["enrolled"] else ""}</p>
<h2>Cost</h2>
{cost_txt or "<p>Tuition is not reported in the IPEDS charges file for this institution; check the college's own website for current tuition.</p>"}
{np_section}
<h2>Outcomes</h2>
{grad_txt or "<p>A 150% graduation rate is not reported for this institution in the 2023 collection — common for very small, new or specialised institutions.</p>"}
<h2>Where it is</h2>
<p>{esc(c["name"])} is in {esc(loc)}{(", " + esc(c["county"])) if c["county"] else ""}.
{("Its coordinates are " + f'{c["lat"]:.4f}, {c["lon"]:.4f}' + ".") if c["lat"] is not None else ""}</p>
<h2>Nearby institutions</h2>
{cards([(b["url"], esc(b["name"]), f'{d:,.0f} km · {esc(b["city"])}') for d, b in near]) or "<p>—</p>"}
{related([(state_url[c["state"]], f"All colleges in {sname}"), ("/search/", "Search colleges"),
          ("/guides/", "Guides to reading these numbers")])}
{faq(faq_pairs)}
"""
        s.add(c["url"], seo_title(c["label"], " — College Data"),
              f'{c["name"]} in {loc}: acceptance rate {pct(c.get("accept"))}, in-state tuition '
              f'{money(c["tuition_in"])}, enrollment {human(c["enrollment"] or 0)}, graduation rate '
              f'{pct(c.get("grad_rate"))}. Federal IPEDS data.',
              body, crumbs=[("States", "/#states"), (sname, state_url[c["state"]]), (c["name"], None)])

    s.add_file("/data/colleges.json", json.dumps(
        [[c["name"], c["city"], c["state"], c["enrollment"] or 0, c["url"]] for c in colleges],
        separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)
    add_guides(s)
    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(colleges))} active US institutions from the federal "
                    f"IPEDS collection (2023 provisional release): institutional directory, admissions, "
                    f"charges, fall enrollment and 150% graduation rates. IPEDS is public-domain data "
                    f"published by the National Center for Education Statistics. Figures are as "
                    f"reported by institutions; a dash means the institution did not report that item.</p>")
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'),res=document.getElementById('res'),st=document.getElementById('status');
  if(!q)return; var idx=null,loading=false;
  function load(){ if(idx||loading)return; loading=true;
    fetch('/data/colleges.json').then(function(r){return r.json()}).then(function(d){idx=d;loading=false;
      if(st)st.textContent=d.length.toLocaleString()+' institutions indexed.';});}
  q.addEventListener('focus',load);
  function esc(s){var d=document.createElement('div');d.textContent=s==null?'':s;return d.innerHTML;}
  function run(){ var v=q.value.trim().toLowerCase(); if(!v)return;
    if(!idx){load();return;}
    var out=idx.filter(function(c){return (c[0]+' '+c[1]+' '+c[2]).toLowerCase().indexOf(v)>=0;});
    res.innerHTML=out.length?'<div class="grid">'+out.slice(0,40).map(function(c){
      return '<a href="'+c[4]+'">'+esc(c[0])+' <span class="mut">'+esc(c[1])+', '+esc(c[2])+'</span></a>';
    }).join('')+'</div>':'<p class="mut">No institution found for that search.</p>';}
  var t;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(run,150);});
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
