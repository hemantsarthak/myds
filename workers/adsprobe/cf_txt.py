"""Add a DNS TXT record to a Cloudflare zone via API (reads secrets from shared/.env).

Used to verify ad-network domain ownership (e.g. HilltopAds siteValidate) without
touching site code or waiting for a deploy.

Usage:
  python workers/adsprobe/cf_txt.py add <zone_id> <record_name> <content>
  python workers/adsprobe/cf_txt.py list <zone_id>
  python workers/adsprobe/cf_txt.py doh-check <fqdn> [expected_substring]
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def env():
    out = {}
    path = os.path.join(ROOT, "shared", ".env")
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


E = env()
CF_TOKEN = E["CF_API_TOKEN"]
API = "https://api.cloudflare.com/client/v4"


def cf(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": "Bearer " + CF_TOKEN,
                                          "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=40)
        return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def add_txt(zone_id, name, content, ttl=60):
    body = {"type": "TXT", "name": name, "content": content, "ttl": ttl}
    res = cf("POST", f"/zones/{zone_id}/dns_records", body)
    return res


def list_txt(zone_id):
    res = cf("GET", f"/zones/{zone_id}/dns_records?type=TXT&per_page=100")
    return [(r["name"], r["content"], r["id"]) for r in res.get("result", [])]


def doh_txt(fqdn):
    req = urllib.request.Request(
        "https://cloudflare-dns.com/dns-query?name=%s&type=TXT" % fqdn,
        headers={"Accept": "application/dns-json", "User-Agent": "Mozilla/5.0"})
    try:
        r = urllib.request.urlopen(req, timeout=25)
        return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "add":
        res = add_txt(args[1], args[2], args[3])
        print(json.dumps({"success": res.get("success"), "errors": res.get("errors"),
                          "id": (res.get("result") or {}).get("id")}, indent=1))
    elif cmd == "list":
        for row in list_txt(args[1]):
            print(row)
    elif cmd == "doh-check":
        res = doh_txt(args[1])
        answers = [a.get("data", "") for a in res.get("Answer", [])]
        print(json.dumps({"status": res.get("Status"), "answers": answers}, indent=1))
        if len(args) > 2:
            ok = any(args[2] in a for a in answers)
            print("MATCH:", ok)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
