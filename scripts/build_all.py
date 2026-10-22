#!/usr/bin/env python3
"""Build (and optionally deploy + IndexNow) every site in one command.

Usage:
  python scripts/build_all.py                 # build all, no deploy
  python scripts/build_all.py --deploy        # build + deploy + attach domains
  python scripts/build_all.py --only ifsc zip --deploy
  python scripts/build_all.py --indexnow      # submit sitemaps to IndexNow after deploy
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# slug, build command (relative), Pages project, public host
SITES = [
    ("hub", ["python", "sites/hub/build.py"], "hub", "tekify.xyz"),
    # pincode.tekify.xyz is deployed by the other (Minimax) agent that shares this Cloudflare
    # account; we keep the sources for reference but do not deploy that project any more.
    ("ifsc", ["python", "sites/ifsc/build.py"], "ifsc", "ifsccodes.tekify.xyz"),
    ("airport", ["python", "sites/airport/build.py"], "myds-airport", "airportcodes.tekify.xyz"),
    ("zip", ["python", "sites/zip/build.py"], "myds-zip", "zipcodes.tekify.xyz"),
    ("calculators", ["python", "sites/calculators/build.py"], "myds-calculators", "calculators.tekify.xyz"),
    ("places", ["python", "sites/places/build.py"], "myds-places", "places.tekify.xyz"),
    ("colleges", ["python", "sites/colleges/build.py"], "myds-colleges", "colleges.tekify.xyz"),
    ("areacodes", ["python", "sites/areacodes/build.py"], "myds-areacodes", "areacodes.tekify.xyz"),
    ("hospitals", ["python", "sites/hospitals/build.py"], "myds-hospitals", "hospitals.tekify.xyz"),
    ("nursinghomes", ["python", "sites/nursinghomes/build.py"], "myds-nursinghomes", "nursinghomes.tekify.xyz"),
]

SITE_DIR = {
    "hub": "sites/hub/site",
    "pincode": "sites/pincode-india/site",
    "ifsc": "sites/ifsc/site",
    "airport": "sites/airport/site",
    "zip": "sites/zip/site",
    "calculators": "sites/calculators/site",
    "places": "sites/places/site",
    "colleges": "sites/colleges/site",
    "areacodes": "sites/areacodes/site",
    "hospitals": "sites/hospitals/site",
    "nursinghomes": "sites/nursinghomes/site",
}


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=str(ROOT), **kw)
    if p.returncode != 0:
        sys.exit(f"FAILED ({p.returncode}): {' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--indexnow", action="store_true")
    ap.add_argument("--skip-build", action="store_true")
    a = ap.parse_args()
    sel = [s for s in SITES if not a.only or s[0] in a.only]
    for slug, build_cmd, project, host in sel:
        t = time.time()
        print(f"\n=== {slug} ===", flush=True)
        if not a.skip_build:
            run(build_cmd)
        print(f"build {time.time()-t:.0f}s", flush=True)
        if a.deploy:
            run(["python", "scripts/ops.py", "deploy", "--project", project,
                 "--dir", SITE_DIR[slug]])
            run(["python", "scripts/ops.py", "attach", "--project", project,
                 "--domain", host, "--wait", "3"])
        if a.indexnow:
            run(["python", "scripts/ops.py", "indexnow", "--dir", SITE_DIR[slug],
                 "--host", host])
    print("\nALL DONE", flush=True)


if __name__ == "__main__":
    main()
