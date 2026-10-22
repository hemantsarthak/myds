#!/usr/bin/env python3
"""Cloudflare + ops CLI for the moneyds revenue portfolio.

Usage:
  python scripts/ops.py zones
  python scripts/ops.py pages
  python scripts/ops.py deploy --project pincode-india --dir sites/pincode-india/site
  python scripts/ops.py attach --project pincode-india --domain pincode.tekify.xyz
  python scripts/ops.py indexnow --dir sites/pincode-india/site [--limit N]
  python scripts/ops.py analytics --host pincode.tekify.xyz
  python scripts/ops.py dns --name sub --target foo.pages.dev
  python scripts/ops.py pages-delete --project x
  python scripts/ops.py inbox --to ads@tekify.xyz [--latest|--json|--addresses]
  python scripts/ops.py mailbox-deploy            # deploy workers/mailbox + secret
  python scripts/ops.py mailbox-setup            # Email Routing catch-all -> worker
  python scripts/ops.py mailbox-selftest --to ads@tekify.xyz
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"
DOCS = ROOT / "docs"
API = "https://api.cloudflare.com/client/v4"


# ---------------------------------------------------------------- env / http
def load_env() -> None:
    for p in (SHARED / ".env", ROOT / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if "CF_API_TOKEN" not in os.environ:
        sys.exit("missing CF_API_TOKEN (shared/.env)")


def api(method: str, path: str, payload=None, expect_fail=False):
    url = API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + os.environ["CF_API_TOKEN"])
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            body = json.loads(raw or "{}")
        except Exception:
            body = {"success": False, "errors": [raw]}
        if expect_fail:
            return body
        sys.exit(f"API ERROR {method} {path}: {json.dumps(body.get('errors'))}")
    if not body.get("success") and not expect_fail:
        sys.exit(f"API ERROR {method} {path}: {json.dumps(body.get('errors'))}")
    return body.get("result")


def acct() -> str:
    return os.environ["CF_ACCOUNT_ID"]


def zone_id(name: str = "tekify.xyz") -> str:
    if name == "tekify.xyz":
        return os.environ["CF_ZONE_ID_TEKIFY"]
    for z in api("GET", "/zones"):
        if z["name"] == name:
            return z["id"]
    sys.exit(f"zone not found: {name}")


# ---------------------------------------------------------------- pages
def cmd_pages(args):
    projects = api("GET", f"/accounts/{acct()}/pages/projects")
    for p in projects:
        latest = p.get("latest_deployment") or {}
        doms = ",".join(p.get("domains") or [])
        print(f"{p['name']:<28} {doms:<45} {latest.get('modified_on','')} {latest.get('url','')}")


def ensure_project(name: str) -> None:
    r = api("GET", f"/accounts/{acct()}/pages/projects/{name}", expect_fail=True)
    if isinstance(r, dict) and r.get("id"):
        return
    print(f"creating pages project: {name}")
    api("POST", f"/accounts/{acct()}/pages/projects", {"name": name, "production_branch": "main"})


def cmd_deploy(args):
    d = (ROOT / args.dir).resolve()
    if not d.exists():
        sys.exit(f"dir not found: {d}")
    ensure_project(args.project)
    wrangler = ROOT / "node_modules" / ".bin" / ("wrangler.cmd" if os.name == "nt" else "wrangler")
    cmd = [str(wrangler) if wrangler.exists() else "npx", "pages", "deploy", str(d),
           f"--project-name={args.project}", "--branch=main", "--commit-dirty=true"]
    if not wrangler.exists():
        cmd = ["npx", "--yes", "wrangler@latest"] + cmd[1:]
    print("+", " ".join(cmd), flush=True)
    env = dict(os.environ)
    env.setdefault("WRANGLER_SEND_METRICS", "false")
    p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True,
                       shell=(os.name == "nt"))
    out = (p.stdout or "") + (p.stderr or "")
    tail = "\n".join(out.strip().splitlines()[-25:])
    if p.returncode != 0:
        print(tail)
        sys.exit(f"deploy failed (exit {p.returncode})")
    m = re.search(r"https://[a-z0-9-]+\.pages\.dev", out)
    print(tail)
    if m:
        print("DEPLOYED:", m.group(0))
    else:
        print("DEPLOYED (url not parsed)")


def cmd_attach(args):
    # 1) DNS CNAME -> project.pages.dev (proxied)
    rec_name = args.domain
    target = f"{args.project}.pages.dev"
    existing = api("GET", f"/zones/{zone_id()}/dns_records?name={rec_name}")
    if existing:
        rec = existing[0]
        if rec["type"] != "CNAME" or rec["content"] != target:
            api("PATCH", f"/zones/{zone_id()}/dns_records/{rec['id']}",
                {"type": "CNAME", "name": rec_name, "content": target, "proxied": True})
            print(f"dns updated {rec_name} -> {target}")
        else:
            print(f"dns ok {rec_name} -> {target}")
    else:
        api("POST", f"/zones/{zone_id()}/dns_records",
            {"type": "CNAME", "name": rec_name, "content": target, "proxied": True})
        print(f"dns created {rec_name} -> {target}")
    # 2) attach custom domain to Pages project
    body = api("POST", f"/accounts/{acct()}/pages/projects/{args.project}/domains",
               {"name": rec_name}, expect_fail=True)
    print("pages domain:", json.dumps(body)[:400])
    # 3) poll status briefly
    for _ in range(args.wait):
        r = api("GET", f"/accounts/{acct()}/pages/projects/{args.project}/domains/{rec_name}",
                expect_fail=True)
        status = (r or {}).get("status") if isinstance(r, dict) else None
        print("status:", status, flush=True)
        if status in ("active", "ok"):
            break
        time.sleep(15)


# ---------------------------------------------------------------- dns
def cmd_dns(args):
    existing = api("GET", f"/zones/{zone_id()}/dns_records?name={args.name}")
    if existing:
        rec = existing[0]
        api("PATCH", f"/zones/{zone_id()}/dns_records/{rec['id']}",
            {"type": args.type, "name": args.name, "content": args.target, "proxied": True})
        print("updated", rec["id"])
    else:
        r = api("POST", f"/zones/{zone_id()}/dns_records",
                {"type": args.type, "name": args.name, "content": args.target, "proxied": True})
        print("created", r["id"])


# ---------------------------------------------------------------- indexnow
def sitemap_urls(site_dir: Path, limit=None):
    urls = []
    for sm in sorted(site_dir.glob("sitemap*.xml")):
        try:
            root = ElementTree.parse(sm).getroot()
        except Exception as e:
            print(f"warn: {sm.name}: {e}")
            continue
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        for loc in root.iter(f"{ns}loc"):
            if loc.text and loc.text.strip().endswith(".xml") is False:
                urls.append(loc.text.strip())
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:limit] if limit else out


def indexnow_submit(urls, host, key):
    if not urls:
        print("no urls")
        return
    payload = {"host": host, "key": key, "keyLocation": f"https://{host}/{key}.txt",
               "urlList": urls}
    req = urllib.request.Request("https://api.indexnow.org/indexnow",
                                 data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print("indexnow:", r.status, len(urls), "urls", host)
    except urllib.error.HTTPError as e:
        print("indexnow error:", e.code, e.read().decode()[:300])


def cmd_indexnow(args):
    site = (ROOT / args.dir).resolve()
    key = os.environ.get("INDEXNOW_KEY", "")
    host = args.host
    if not host:
        # infer from CNAME file or args required
        sys.exit("--host required, e.g. --host pincode.tekify.xyz")
    urls = sitemap_urls(site, args.limit)
    print(f"{len(urls)} urls from sitemaps")
    if args.dry:
        print("\n".join(urls[:5]))
        return
    batch = 10000 if args.batch == 0 else args.batch
    for i in range(0, len(urls), batch):
        indexnow_submit(urls[i:i + batch], host, key)
        if i + batch < len(urls):
            time.sleep(2)


# ---------------------------------------------------------------- mailbox
# Self-hosted inbox: workers/mailbox (Email Worker + KV + JSON API).
# Any address @tekify.xyz is valid (Email Routing catch-all). Read with `inbox`.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def mailbox_base() -> str:
    return os.environ.get("MAILBOX_INBOX_URL", "https://mailbox.monetec2.workers.dev").rstrip("/")


def mailbox_get(path: str, params=None) -> dict:
    token = os.environ.get("MAILBOX_INBOX_TOKEN", "")
    if not token:
        sys.exit("missing MAILBOX_INBOX_TOKEN (shared/.env)")
    q = urllib.parse.urlencode({"token": token, **(params or {})})
    req = urllib.request.Request(f"{mailbox_base()}{path}?{q}")
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            sys.exit(f"inbox error {e.code}: {body[:400]}")
        if e.code == 404 and data.get("message") is None:
            return data
        sys.exit(f"inbox error {e.code}: {json.dumps(data)[:400]}")


def print_message(m: dict, full=False) -> None:
    print(f"  from:    {m.get('from_name','')} <{m.get('from','')}>")
    print(f"  to:      {m.get('to','')}")
    print(f"  subject: {m.get('subject','')}")
    print(f"  date:    {m.get('received_at','')}")
    if m.get("links"):
        print("  links:")
        for u in m["links"]:
            print(f"    - {u}")
    if m.get("attachments"):
        print("  attachments:", ", ".join(f"{a.get('filename')}({a.get('size')}B)" for a in m["attachments"]))
    body = m.get("text", "")
    if body:
        print("  ---")
        for line in body[: int(4000 if not full else 20000)].splitlines():
            print("  " + line)


def cmd_inbox(args):
    if args.addresses:
        d = mailbox_get("/inbox/addresses")
        print("\n".join(d.get("addresses", [])) if not args.json else print(json.dumps(d, indent=2)))
        return
    params = {}
    if args.to:
        params["to"] = args.to
    if args.latest:
        d = mailbox_get("/inbox/latest", params)
        m = d.get("message")
        if not m:
            print(f"no mail for {args.to or '*'} yet")
            return
        if args.json:
            print(json.dumps(m, indent=2))
        else:
            print("LATEST MESSAGE")
            print_message(m, full=True)
        return
    params["limit"] = str(args.limit)
    d = mailbox_get("/inbox", params)
    msgs = d.get("messages", [])
    if args.json:
        print(json.dumps(d, indent=2))
        return
    print(f"{d.get('count',0)} message(s) for {d.get('address','*')} (newest first)")
    for m in msgs:
        print(f"\n[{m['received_at']}] {m.get('from_name','')} <{m.get('from','')}> -> {m.get('subject','')}")
        if args.full:
            print_message(m, full=True)
        elif m.get("links"):
            for u in m["links"][:5]:
                print(f"   link: {u}")


def cmd_mailbox_setup(args):
    zid = zone_id()
    print("enable email routing:", json.dumps(api("POST", f"/zones/{zid}/email/routing/enable", {})))
    body = {
        "name": "catch-all to mailbox worker",
        "enabled": True,
        "matchers": [{"type": "all"}],
        "actions": [{"type": "worker", "value": [args.worker]}],
    }
    r = api("PUT", f"/zones/{zid}/email/routing/rules/catch_all", body)
    print("catch_all:", json.dumps(r))
    print("status:", json.dumps(api("GET", f"/zones/{zid}/email/routing")))


def cmd_mailbox_deploy(args):
    wdir = ROOT / "workers" / "mailbox"
    if not wdir.exists():
        sys.exit(f"missing {wdir}")
    wrangler = ROOT / "node_modules" / ".bin" / ("wrangler.cmd" if os.name == "nt" else "wrangler")
    env = dict(os.environ)
    env["CLOUDFLARE_API_TOKEN"] = os.environ["CF_API_TOKEN"]
    env["CLOUDFLARE_ACCOUNT_ID"] = os.environ["CF_ACCOUNT_ID"]
    env.setdefault("WRANGLER_SEND_METRICS", "false")
    p = subprocess.run([str(wrangler), "deploy"], cwd=str(wdir), env=env, capture_output=True,
                       text=True, shell=(os.name == "nt"))
    out = (p.stdout or "") + (p.stderr or "")
    print("\n".join(out.strip().splitlines()[-15:]))
    if p.returncode != 0:
        sys.exit(f"wrangler deploy failed (exit {p.returncode})")
    token = os.environ.get("MAILBOX_INBOX_TOKEN", "")
    if not token:
        sys.exit("missing MAILBOX_INBOX_TOKEN (shared/.env) — worker deployed but secret not set")
    (ROOT / ".cache").mkdir(exist_ok=True)
    sec = ROOT / ".cache" / "mailbox_secret.json"
    sec.write_text(json.dumps({"INBOX_TOKEN": token}), encoding="utf-8")
    try:
        p = subprocess.run([str(wrangler), "secret", "bulk", str(sec)], cwd=str(wdir), env=env,
                           capture_output=True, text=True, shell=(os.name == "nt"))
    finally:
        sec.unlink(missing_ok=True)
    tail = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-6:]
    print("\n".join(tail))
    if p.returncode != 0:
        sys.exit(f"wrangler secret bulk failed (exit {p.returncode})")
    print(f"DEPLOYED: {mailbox_base()}")


def cmd_mailbox_selftest(args):
    """Deliver a real test email by SMTP-ing straight to the Cloudflare MX (port 25)."""
    import smtplib
    from email.message import EmailMessage
    token = os.environ.get("MAILBOX_INBOX_TOKEN", "")
    if not token:
        sys.exit("missing MAILBOX_INBOX_TOKEN (shared/.env)")
    msg = EmailMessage()
    msg["From"] = "Mailbox Selftest <verify@mailbox-test.example>"
    msg["To"] = args.to
    msg["Subject"] = f"tekify mailbox selftest {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
    msg.set_content("Selftest: direct SMTP to Cloudflare MX -> Email Routing catch-all -> worker -> KV.\n"
                    "Read it back with: python scripts/ops.py inbox --to " + args.to + "\n")
    try:
        s = smtplib.SMTP(args.smtp_host, args.port, timeout=30)
        s.ehlo("mailbox-test.example")
        try:
            code, resp = s.send_message(msg)
            print("SMTP accepted:", code, resp)
        except ValueError as e:
            # Some Mail Exchange servers answer DATA in a way smtplib mishandles; the
            # message is normally still accepted, so keep polling instead of failing.
            print(f"SMTP client warning after DATA (message likely queued): {e}")
        try:
            s.quit()
        except Exception:
            pass
    except Exception as e:
        sys.exit(f"SMTP send failed: {type(e).__name__}: {e}")
    for _ in range(12):
        time.sleep(10)
        d = mailbox_get("/inbox", {"to": args.to, "limit": "1"})
        if d.get("count"):
            m = d["messages"][0]
            print(f"DELIVERED: {m.get('received_at')} from <{m.get('from')}> subject={m.get('subject')!r}")
            print(json.dumps(m, indent=2)[:2000])
            return
    print("sent, but message not visible yet (KV propagation); retry inbox in ~60s")


# ---------------------------------------------------------------- analytics
def cmd_analytics(args):
    for host in args.host:
        r = api("POST", f"/accounts/{acct()}/rum/site_info",
                {"host": host, "auto_install": False}, expect_fail=True)
        print(host, "->", json.dumps(r)[:400])


def main():
    load_env()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("zones")
    sub.add_parser("pages")

    d = sub.add_parser("deploy")
    d.add_argument("--project", required=True)
    d.add_argument("--dir", required=True)
    d.set_defaults(func=cmd_deploy)

    a = sub.add_parser("attach")
    a.add_argument("--project", required=True)
    a.add_argument("--domain", required=True)
    a.add_argument("--wait", type=int, default=8)
    a.set_defaults(func=cmd_attach)

    dn = sub.add_parser("dns")
    dn.add_argument("--name", required=True)
    dn.add_argument("--target", required=True)
    dn.add_argument("--type", default="CNAME")
    dn.set_defaults(func=cmd_dns)

    ix = sub.add_parser("indexnow")
    ix.add_argument("--dir", required=True)
    ix.add_argument("--host", required=True)
    ix.add_argument("--limit", type=int, default=0)
    ix.add_argument("--batch", type=int, default=0)
    ix.add_argument("--dry", action="store_true")
    ix.set_defaults(func=cmd_indexnow)

    an = sub.add_parser("analytics")
    an.add_argument("--host", nargs="+", required=True)
    an.set_defaults(func=cmd_analytics)

    ib = sub.add_parser("inbox", help="read mail from the tekify.xyz mailbox worker")
    ib.add_argument("--to", help="address, e.g. ads@tekify.xyz (omit for all)")
    ib.add_argument("--limit", type=int, default=10)
    ib.add_argument("--latest", action="store_true", help="newest message only (full body)")
    ib.add_argument("--addresses", action="store_true", help="list addresses that received mail")
    ib.add_argument("--json", action="store_true")
    ib.add_argument("--full", action="store_true", help="include full text in list mode")
    ib.set_defaults(func=cmd_inbox)

    ms = sub.add_parser("mailbox-setup", help="enable Email Routing + catch-all -> worker")
    ms.add_argument("--worker", default="mailbox")
    ms.set_defaults(func=cmd_mailbox_setup)

    md = sub.add_parser("mailbox-deploy", help="deploy workers/mailbox + set INBOX_TOKEN secret")
    md.set_defaults(func=cmd_mailbox_deploy)

    mt = sub.add_parser("mailbox-selftest", help="send a real test mail to --to via SMTP to CF MX")
    mt.add_argument("--to", default="ads@tekify.xyz")
    mt.add_argument("--smtp-host", default="route1.mx.cloudflare.net")
    mt.add_argument("--port", type=int, default=25)
    mt.set_defaults(func=cmd_mailbox_selftest)

    args = ap.parse_args()
    if args.cmd == "zones":
        for z in api("GET", "/zones"):
            print(z["name"], z["id"], z["status"])
        return
    if args.cmd == "pages":
        cmd_pages(args)
        return
    args.func(args)


if __name__ == "__main__":
    main()
