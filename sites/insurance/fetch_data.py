#!/usr/bin/env python3
"""Fetch and condense the CMS Health Insurance Exchange PUF data for sites/insurance.

Sources (public domain, CMS):
  https://download.cms.gov/marketplace-puf/2026/plan-attributes-puf.zip
  https://download.cms.gov/marketplace-puf/2026/rate-puf.zip
  https://download.cms.gov/marketplace-puf/2026/service-area-puf.zip
  .cache/gaz/2023_Gaz_counties_national.txt  (Census county FIPS -> name)

Output (.cache/insurance/):
  plans.json    plan-level records for the 2026 individual market (exchange plans)
  counties.json county FIPS -> {state, name, plan ids covering it}
  meta.json     business year, states covered, counts

Only tobacco-free rates for ages 21 / 40 / 60 are kept (the three reference ages shown on
the site). Service areas covering the entire state are expanded to every county in the state.

Run: python sites/insurance/fetch_data.py
"""
import collections
import csv
import json
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
EXCH = CACHE / "exchange2026"
OUT = CACHE / "insurance"
YEAR = 2026
BASE = f"https://download.cms.gov/marketplace-puf/{YEAR}/"
FILES = ["plan-attributes-puf.zip", "rate-puf.zip", "service-area-puf.zip"]
AGES = {"21", "40", "60"}

TARGET_METALS = {"Bronze", "Expanded Bronze", "Silver", "Gold", "Platinum", "Catastrophic"}


def ensure_files():
    EXCH.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        zpath = EXCH / name
        csvpath = EXCH / name.replace(".zip", ".csv")
        if not csvpath.exists() or csvpath.stat().st_size < 1000:
            if not zpath.exists() or zpath.stat().st_size < 1000:
                print("downloading", BASE + name)
                urllib.request.urlretrieve(BASE + name, zpath)
            with zipfile.ZipFile(zpath) as z:
                z.extractall(EXCH)
            print("extracted", csvpath.name, f"{csvpath.stat().st_size/1e6:.1f} MB")
        else:
            print("cached", csvpath.name)


def county_table():
    """GEOID -> (state, name) for every US county, plus state -> [GEID]."""
    geo = CACHE / "gaz" / "2023_Gaz_counties_national.txt"
    names, by_state = {}, collections.defaultdict(list)
    with geo.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            fips = row["GEOID"].strip().zfill(5)
            st = row["USPS"].strip()
            names[fips] = (st, row["NAME"].strip())
            by_state[st].append(fips)
    return names, by_state


def fnum(v):
    try:
        return round(float(str(v).replace(",", "").replace("$", "").strip()), 2)
    except (TypeError, ValueError):
        return None


def main():
    ensure_files()
    names, by_state = county_table()

    # ---- plans (individual market, medical only)
    plans = {}
    csr_rank = {"": 0, "Standard": 0, "0": 0, "01": 1, "02": 2, "03": 3}
    with (EXCH / "plan-attributes-puf.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("BusinessYear") or "").strip() != str(YEAR):
                continue
            if (r.get("MarketCoverage") or "").strip() != "Individual":
                continue
            if (r.get("DentalOnlyPlan") or "").strip() != "No":
                continue
            metal = (r.get("MetalLevel") or "").strip()
            if metal not in TARGET_METALS:
                continue
            plan_id = (r.get("PlanId") or "").strip()
            standard_id = (r.get("StandardComponentId") or "").strip()
            if not plan_id or not standard_id:
                continue
            csr = (r.get("CSRVariationType") or "").strip()
            prev = plans.get(standard_id)
            if prev is not None and csr_rank.get(prev["csr"], 9) <= csr_rank.get(csr, 9):
                continue  # prefer the standard (non-CSR) variant per standard component
            plans[standard_id] = {
                "id": plan_id,
                "standard_id": standard_id,
                "csr": csr,
                "state": (r.get("StateCode") or "").strip(),
                "issuer": (r.get("IssuerId") or "").strip(),
                "issuer_name": (r.get("IssuerMarketPlaceMarketingName") or "").strip(),
                "name": (r.get("PlanMarketingName") or "").strip(),
                "variant": (r.get("PlanVariantMarketingName") or "").strip(),
                "metal": metal,
                "type": (r.get("PlanType") or "").strip(),
                "sa": (r.get("ServiceAreaId") or "").strip(),
                "network": (r.get("NetworkId") or "").strip(),
                "ded": fnum(r.get("MEHBDedInnTier1Individual")),
                "moop": fnum(r.get("MEHBInnTier1IndividualMOOP")),
                "hsa": (r.get("IsHSAEligible") or "").strip().lower() == "yes",
            }
    print(f"plans kept: {len(plans)}")

    # ---- service area -> counties
    sa_counties = collections.defaultdict(set)
    ffm_states = set()
    with (EXCH / "service-area-puf.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            st = (r.get("StateCode") or "").strip()
            sa = (r.get("ServiceAreaId") or "").strip()
            if not st or not sa:
                continue
            ffm_states.add(st)
            if (r.get("CoverEntireState") or "").strip().lower() == "yes":
                sa_counties[(st, sa)] = set(by_state.get(st, []))
            else:
                fips = (r.get("County") or "").strip().zfill(5)
                if fips and fips != "00000":
                    sa_counties[(st, sa)].add(fips)
    print(f"service areas: {len(sa_counties)} in {len(ffm_states)} states")

    # ---- rates: reference ages, base (non-tobacco) rate
    rates = {}
    seen = 0
    with (EXCH / "rate-puf.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            seen += 1
            age = (r.get("Age") or "").strip()
            if age not in AGES:
                continue
            tob = (r.get("Tobacco") or "").strip()
            rate = fnum(r.get("IndividualRate"))
            if rate is None or rate <= 0:
                continue
            key = ((r.get("StateCode") or "").strip(), (r.get("PlanId") or "").strip(), age)
            prev = rates.get(key)
            if prev is None or (tob == "No Preference" and prev[0] != "No Preference"):
                rates[key] = (tob, rate)
            if seen % 1_000_000 == 0:
                print("  rate rows scanned:", seen)
    rates = {k: v[1] for k, v in rates.items()}
    print(f"rate rows scanned: {seen}; rates kept: {len(rates)}")

    # ---- join plans -> counties and rates
    counties = {}
    for plan in plans.values():
        st, sa = plan["state"], plan["sa"]
        fips_set = sa_counties.get((st, sa), set())
        plan["counties"] = len(fips_set)
        for age in AGES:
            plan[f"p{age}"] = rates.get((st, plan["standard_id"], age))
        for fips in fips_set:
            entry = counties.setdefault(fips, {"state": st, "name": names.get(fips, ("", ""))[1], "plans": []})
            entry["plans"].append(plan["standard_id"])

    # ---- write outputs
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "plans.json").write_text(json.dumps(plans, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    (OUT / "counties.json").write_text(json.dumps(counties, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    meta = {
        "year": YEAR,
        "plans": len(plans),
        "counties": len(counties),
        "states": sorted({p["state"] for p in plans.values()}),
        "issuers": len({(p["issuer"], p["state"]) for p in plans.values()}),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta, indent=1))
    print("outputs in", OUT)


if __name__ == "__main__":
    main()
