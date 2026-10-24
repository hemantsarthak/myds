#!/usr/bin/env python3
"""Fetch and parse the CareScout (Genworth) 2025 Cost of Care Survey state tables.

Source: CareScout "Cost of Care Survey 2025 — Median Cost Data Tables" public PDF
(https://assets.carescout.com/x/8fcb50422f/282102.pdf, retrieved 2026-10-24).
Columns used: annual median costs for homemaker services (44 h/week), private duty nurse
(1 h/week, not published on the site), adult day health care (5 days/week), assisted living
community, nursing home semi-private room and private room; plus the per-state non-medical
caregiver hourly rate.

Output: .cache/carescout-costs.json
{
  "source": "...", "national": {...}, "hourly_national": {...},
  "states": {"Alabama": {"annual": {...}, "hourly": {...}}, ...}
}

Run: python sites/nursinghomes/fetch_costs.py
"""
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
PDF = CACHE / "carescout-2025.pdf"
OUT = CACHE / "carescout-costs.json"
URL = "https://assets.carescout.com/x/8fcb50422f/282102.pdf"

ANNUAL_KEYS = ["homemaker", "private_duty_nurse", "adult_day", "assisted_living",
               "nursing_semi", "nursing_private"]
HOURLY_KEYS = ["caregiver", "private_duty_nurse", "private_duty_visit"]
STATE_ORDER = [
    "USA National", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana",
    "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
    "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee",
    "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]


def money(v):
    if v == "N/A":
        return None
    return int(re.sub(r"[^\d]", "", v))


def main():
    CACHE.mkdir(exist_ok=True)
    if not PDF.exists() or PDF.stat().st_size < 50_000:
        print("downloading", URL)
        urllib.request.urlretrieve(URL, PDF)
    import pdfplumber

    pdf = pdfplumber.open(str(PDF))
    annual_text = "\n".join((p.extract_text() or "") for p in pdf.pages[:3])
    hourly_text = pdf.pages[7].extract_text() or ""

    annual_re = re.compile(
        r"^([A-Z][A-Za-z .]+?)\s+(\$[\d,]+|N/A)\s+(\$[\d,]+|N/A)\s+(\$[\d,]+|N/A)\s+"
        r"(\$[\d,]+|N/A)\s+(\$[\d,]+|N/A)\s+(\$[\d,]+|N/A)\s*$", re.M)
    annual_rows = [(m.group(1).strip(), [money(x) for x in m.groups()[1:]])
                   for m in annual_re.finditer(annual_text)]
    annual = {name: dict(zip(ANNUAL_KEYS, vals)) for name, vals in annual_rows[:51]}

    hourly_re = re.compile(r"([A-Z][A-Za-z .]+?)\s+(\$[\d,]+|N/A)\s+(\$[\d,]+|N/A)\s+(\$[\d,]+|N/A)")
    hourly_rows = [(m.group(1).strip(), [money(x) for x in m.groups()[1:]])
                   for m in hourly_re.finditer(hourly_text)]
    hourly = {name: dict(zip(HOURLY_KEYS, vals)) for name, vals in hourly_rows}

    states = {}
    for name in STATE_ORDER:
        if name == "USA National":
            continue
        a = annual.get(name)
        h = hourly.get(name)
        if not a:
            print("missing annual data:", name)
            continue
        states[name] = {"annual": a, "hourly": h}

    out = {
        "source": "CareScout / Genworth 2025 Cost of Care Survey (Median Cost Data Tables PDF)",
        "url": URL,
        "retrieved": "2026-10-24",
        "national": {"annual": annual.get("USA National"), "hourly": hourly.get("USA National")},
        "states": states,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("states:", len(states))
    print("national:", json.dumps(out["national"]))
    print("sample Alabama:", json.dumps(states["Alabama"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
