"""Spot-check a sample of URLs from every sitemap to catch 404s / broken deployments."""
import random
import re
import urllib.request
from xml.etree import ElementTree

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124"}
HOSTS = ["tekify.xyz", "ifsccodes.tekify.xyz", "airportcodes.tekify.xyz", "zipcodes.tekify.xyz",
         "places.tekify.xyz", "colleges.tekify.xyz", "areacodes.tekify.xyz",
         "hospitals.tekify.xyz", "nursinghomes.tekify.xyz", "homehealth.tekify.xyz",
         "calculators.tekify.xyz"]
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def sitemap_urls(host):
    body = get(f"https://{host}/sitemap.xml").read()
    root = ElementTree.fromstring(body)
    locs = [e.text.strip() for e in root.iter(f"{NS}loc") if e.text]
    if locs and all(u.endswith(".xml") for u in locs):
        out = []
        for sm in locs:
            r = ElementTree.fromstring(get(sm).read())
            out += [e.text.strip() for e in r.iter(f"{NS}loc") if e.text]
        return out
    return locs


random.seed(7)
failures = 0
for host in HOSTS:
    try:
        urls = sitemap_urls(host)
        sample = random.sample(urls, min(6, len(urls)))
        bad = []
        for u in sample:
            try:
                r = get(u)
                if r.status != 200:
                    bad.append((u, r.status))
            except Exception as e:  # noqa: BLE001
                bad.append((u, str(e)[:40]))
        print(f"{host:<28} {len(urls):>6} urls | sample ok {len(sample)-len(bad)}/{len(sample)}"
              + (f" | BAD: {bad[:3]}" if bad else ""))
        failures += len(bad)
    except Exception as e:  # noqa: BLE001
        print(f"{host:<28} SITEMAP ERROR {e}")
        failures += 1
print("total failures:", failures)
