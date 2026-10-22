#!/usr/bin/env python3
"""Publish the portfolio's open datasets to Hugging Face and Zenodo.

Both platforms are heavily crawled and indexable, and an open dataset with a card that links to the
live directory is a legitimate, useful artifact — the most promising autonomous discovery path left.

Tokens (in shared/.env):
  HF_TOKEN=hf_...            create at https://huggingface.co/settings/tokens (write scope)
  ZENODO_TOKEN=...           create at https://zenodo.org/account/settings/applications/

Usage:
  python scripts/publish_datasets.py --check                 # show what would be published
  python scripts/publish_datasets.py --hf                    # create + upload HF dataset repos
  python scripts/publish_datasets.py --zenodo                # create + publish Zenodo records

Each dataset is a folder under datasets/<slug>/ with README.md (dataset card) and sample.csv.
"""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
UA = {"User-Agent": "tekify-dataset-publisher/1.0"}

META = {
    "ifsc-codes": dict(
        title="Indian Bank IFSC Codes",
        site="https://ifsccodes.tekify.xyz",
        source="Razorpay IFSC dataset (MIT)",
        licence="mit",
        keywords=["ifsc", "india", "banking", "branch", "open data"],
    ),
    "us-zip-codes": dict(
        title="US ZIP Codes",
        site="https://zipcodes.tekify.xyz",
        source="US Census Bureau / GeoNames",
        licence="cc-by-4.0",
        keywords=["zip codes", "united states", "geography", "census", "open data"],
    ),
    "cms-hospital-ratings": dict(
        title="US Hospital Ratings (CMS)",
        site="https://hospitals.tekify.xyz",
        source="CMS Provider Data Catalog",
        licence="cc0-1.0",
        keywords=["hospitals", "cms", "quality", "ratings", "medicare", "open data"],
    ),
    "us-dialysis-facilities": dict(
        title="US Dialysis Facilities (CMS)",
        site="https://dialysis.tekify.xyz",
        source="CMS Provider Data Catalog",
        licence="cc0-1.0",
        keywords=["dialysis", "cms", "quality", "medicare", "open data"],
    ),
}


def env() -> dict:
    out = {}
    p = ROOT / "shared" / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def http(method: str, url: str, data=None, headers=None, raw=False):
    hdrs = dict(UA)
    if headers:
        hdrs.update(headers)
    body = None
    if data is not None:
        body = data if raw else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def card(slug: str) -> str:
    m = META[slug]
    p = DATASETS / slug / "README.md"
    text = p.read_text(encoding="utf-8") if p.exists() else f"# {m['title']}\n"
    return text + f"\n\n## Live directory\n\n<{m['site']}>\n"


def check() -> int:
    rows = []
    for slug in META:
        folder = DATASETS / slug
        ok = (folder / "sample.csv").exists() and (folder / "README.md").exists()
        rows.append((slug, ok, (folder / "sample.csv").stat().st_size if (folder / "sample.csv").exists() else 0))
    for slug, ok, size in rows:
        print(f"{slug:<26} {'ready' if ok else 'MISSING':<8} {size/1024:.0f} KB")
    e = env()
    print("\ntokens: HF_TOKEN", "present" if e.get("HF_TOKEN") else "MISSING",
          "| ZENODO_TOKEN", "present" if e.get("ZENODO_TOKEN") else "MISSING")
    return 0 if all(ok for _, ok, _ in rows) else 1


def publish_hf() -> int:
    e = env()
    token = e.get("HF_TOKEN")
    if not token:
        sys.exit("HF_TOKEN missing in shared/.env — create a write token at https://huggingface.co/settings/tokens")
    hdr = {"Authorization": f"Bearer {token}"}
    user = "tekify"
    st, body = http("GET", "https://huggingface.co/api/whoami-v2", headers=hdr)
    if st == 200:
        try:
            user = json.loads(body).get("name") or user
        except Exception:
            pass
    for slug, m in META.items():
        repo = f"{user}/tekify-{slug}"
        st, body = http("POST", "https://huggingface.co/api/repos/create",
                        {"name": f"tekify-{slug}", "type": "dataset", "private": False}, headers=hdr)
        print(f"{repo}: create -> {st}")
        # upload README + sample via the commit endpoint (base64)
        import base64
        files = {}
        for name in ("README.md", "sample.csv"):
            p = DATASETS / slug / name
            if p.exists():
                files[name] = {"content": base64.b64encode(p.read_bytes()).decode(), "encoding": "base64"}
        payload = {"summary": f"Add {m['title']} sample", "files": files}
        st, body = http("POST", f"https://huggingface.co/api/datasets/{repo}/commit/main", payload, headers=hdr)
        print(f"  upload -> {st} {body[:160]}")
    return 0


def publish_zenodo() -> int:
    e = env()
    token = e.get("ZENODO_TOKEN")
    if not token:
        sys.exit("ZENODO_TOKEN missing in shared/.env — create one at https://zenodo.org/account/settings/applications/")
    hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for slug, m in META.items():
        meta = {
            "metadata": {
                "title": f"{m['title']} — sample dataset",
                "upload_type": "dataset",
                "description": card(slug),
                "license": m["licence"],
                "keywords": m["keywords"],
                "creators": [{"name": "Tekify"}],
                "related_identifiers": [{"identifier": m["site"], "relation": "isDocumentedBy",
                                         "resource_type": "other"}],
            }
        }
        st, body = http("POST", "https://zenodo.org/api/deposit/depositions", meta, headers=hdr)
        if st not in (200, 201):
            print(f"{slug}: create -> {st} {body[:200]}")
            continue
        dep = json.loads(body)
        bucket = dep["links"]["bucket"]
        for name in ("README.md", "sample.csv"):
            p = DATASETS / slug / name
            if not p.exists():
                continue
            st2, body2 = http("PUT", f"{bucket}/{name}", p.read_bytes(),
                              headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
                              raw=True)
            print(f"{slug}: upload {name} -> {st2}")
        st3, body3 = http("POST", f"https://zenodo.org/api/deposit/depositions/{dep['id']}/actions/publish",
                          {}, headers=hdr)
        print(f"{slug}: publish -> {st3}")
        if st3 in (200, 202):
            try:
                print("   doi:", json.loads(body3).get("doi"))
            except Exception:
                pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--hf", action="store_true")
    ap.add_argument("--zenodo", action="store_true")
    a = ap.parse_args()
    if a.check or not (a.hf or a.zenodo):
        return check()
    if a.hf:
        publish_hf()
    if a.zenodo:
        publish_zenodo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
