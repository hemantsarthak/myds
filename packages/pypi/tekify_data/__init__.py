"""tekify-data — keyless client for the Tekify open-data JSON endpoints.

Data sources: US Census Bureau, CMS, NCES/IPEDS, GeoNames (CC BY), OurAirports, Razorpay IFSC (MIT).
Every endpoint is CORS-enabled and needs no API key.
Docs: https://hemantsarthak.github.io/myds/data.html
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

__version__ = "0.1.0"

ENDPOINTS: Dict[str, str] = {
    "zip": "https://zipcodes.tekify.xyz/data/zips.json",
    "places": "https://places.tekify.xyz/data/places.json",
    "colleges": "https://colleges.tekify.xyz/data/colleges.json",
    "hospitals": "https://hospitals.tekify.xyz/data/hospitals.json",
    "nursing_homes": "https://nursinghomes.tekify.xyz/data/nursinghomes.json",
    "home_health": "https://homehealth.tekify.xyz/data/homehealth.json",
    "dialysis": "https://dialysis.tekify.xyz/data/dialysis.json",
    "airports": "https://airportcodes.tekify.xyz/data/airports.json",
    "area_codes": "https://areacodes.tekify.xyz/data/search.json",
}

FIELDS = {
    "zip": ["zip", "city", "state", "county", "population", "timezone"],
    "places": ["name", "state", "county", "population", "url"],
    "colleges": ["name", "city", "state", "unitid", "url"],
    "hospitals": ["name", "city", "state", "rating", "url"],
    "nursing_homes": ["name", "city", "state", "rating", "url"],
    "home_health": ["name", "city", "state", "rating", "url"],
    "dialysis": ["name", "city", "state", "rating", "url"],
    "airports": ["iata", "ident", "icao", "name", "city", "country"],
    "area_codes": ["code", "label", "url"],
    "ifsc": ["ifsc", "branch", "district", "state"],
}

_CACHE: Dict[str, List[list]] = {}


def _load(url: str) -> List[list]:
    if url in _CACHE:
        return _CACHE[url]
    req = urllib.request.Request(url, headers={"User-Agent": "tekify-data/0.1 (+https://tekify.xyz/)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rows = json.loads(r.read().decode())
    _CACHE[url] = rows
    return rows


def _objects(rows: List[list], fields: List[str]) -> List[Dict[str, Any]]:
    return [dict(zip(fields, row)) for row in rows]


def _filter(key: str, query: str, keys: List[str], limit: int) -> List[Dict[str, Any]]:
    rows = _objects(_load(ENDPOINTS[key]), FIELDS[key])
    q = str(query).lower()
    out = []
    for row in rows:
        hay = " ".join(str(row.get(k, "")) for k in keys).lower()
        if q in hay:
            out.append(row)
            if len(out) >= limit:
                break
    return out


def zip_code(zip_code: str) -> Optional[Dict[str, Any]]:
    """Look up a US ZIP code; returns a dict or None."""
    for row in _load(ENDPOINTS["zip"]):
        if str(row[0]) == str(zip_code):
            return dict(zip(FIELDS["zip"], row))
    return None


def hospitals(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("hospitals", query, ["name", "city", "state"], limit)


def nursing_homes(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("nursing_homes", query, ["name", "city", "state"], limit)


def home_health(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("home_health", query, ["name", "city", "state"], limit)


def dialysis(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("dialysis", query, ["name", "city", "state"], limit)


def colleges(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("colleges", query, ["name", "city", "state"], limit)


def places(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("places", query, ["name", "county", "state"], limit)


def airports(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("airports", query, ["iata", "ident", "icao", "name", "city", "country"], limit)


def area_codes(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return _filter("area_codes", query, ["code", "label"], limit)


def ifsc_bank(bank: str) -> List[Dict[str, Any]]:
    """All Indian bank branches for a bank code (e.g. "HDFC")."""
    url = f"https://ifsccodes.tekify.xyz/data/bank/{urllib.parse.quote(str(bank).upper())}.json"
    return _objects(_load(url), FIELDS["ifsc"])

