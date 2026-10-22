"""HilltopAds publisher panel client (GraphQL over cookies).

Recon notes (2026-10-22):
  - Signup:      POST https://hilltopads.com/signup  (HTML form: who=publisher, name,
                 email, password, legal=1, vertical=both, lang=en + hidden CSRF token).
                 No captcha was requested for this account/IP -> signup is fully scriptable.
  - Login:       POST https://hilltopads.com/login  {email,password,<CSRF name>:token}
  - Panel:       https://user.hilltopads.com  (Vue add + GraphQL at POST /api)
  - GraphQL body {"operationName":..., "variables":{...}, "query":"..."}

Usage:
  python workers/adsprobe/hilltop_api.py sites
  python workers/adsprobe/hilltop_api.py add-site tekify.xyz
  python workers/adsprobe/hilltop_api.py introspect Mutation
  python workers/adsprobe/hilltop_api.py call '<graphql>' '<json vars>'
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COOKIE_FILE = os.path.join(ROOT, "shared", "hilltop_cookies.json")
ACCOUNT_FILE = os.path.join(ROOT, "shared", "hilltop_signup_attempt.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
PANEL = "https://user.hilltopads.com"
API = PANEL + "/api"
SITE = "https://hilltopads.com"

EMAIL = "hilltopads@tekify.xyz"


def _cookies_from_file():
    cj = http.cookiejar.CookieJar()
    try:
        raw = json.load(open(COOKIE_FILE, encoding="utf-8"))
    except Exception:
        return cj
    for c in raw:
        cj.set_cookie(http.cookiejar.Cookie(
            version=0, name=c["name"], value=c["value"], port=None, port_specified=False,
            domain=c["domain"], domain_specified=True,
            domain_initial_dot=c["domain"].startswith("."), path=c["path"],
            path_specified=True, secure=True, expires=None, discard=False,
            comment=None, comment_url=None, rest={}, rfc2109=False))
    return cj


def _opener():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cookies_from_file()))
    return op


def _save_cookies(op):
    cj = op.handlers[0].cookiejar if op.handlers else None
    # find cookiejar handler
    for h in op.handlers:
        if isinstance(h, urllib.request.HTTPCookieProcessor):
            cj = h.cookiejar
    raw = [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
           for c in cj]
    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
    json.dump(raw, open(COOKIE_FILE, "w", encoding="utf-8"), indent=1)


def _password():
    try:
        return json.load(open(ACCOUNT_FILE, encoding="utf-8"))["password"]
    except Exception:
        raise SystemExit("missing password in " + ACCOUNT_FILE)


def login():
    op = _opener()
    h = {"User-Agent": UA, "Accept": "text/html,*/*", "Accept-Language": "en-US,en;q=0.9"}
    t = op.open(urllib.request.Request(SITE + "/login", headers=h), timeout=40).read().decode("utf-8", "replace")
    tok = re.search(r'<input id="csrfToken" type="hidden" name="([^"]+)" value="([^"]*)"', t)
    data = {"email": EMAIL, "password": _password()}
    if tok:
        data[tok.group(1)] = tok.group(2)
    body = urllib.parse.urlencode(data).encode()
    h2 = {"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "Accept": "application/json, text/javascript, */*; q=0.01",
          "X-Requested-With": "XMLHttpRequest", "Referer": SITE + "/login",
          "Origin": SITE, "Accept-Language": "en-US,en;q=0.9"}
    r = op.open(urllib.request.Request(SITE + "/login", data=body, headers=h2, method="POST"), timeout=40)
    resp = json.loads(r.read().decode("utf-8", "replace"))
    _save_cookies(op)
    return resp


def gql(query, variables=None, opname=None, retry_login=True):
    payload = {"operationName": opname, "variables": variables or {}, "query": query}
    data = json.dumps(payload).encode()
    h = {"User-Agent": UA, "Content-Type": "application/json", "Accept": "application/json",
         "X-Requested-With": "XMLHttpRequest", "Origin": PANEL,
         "Referer": PANEL + "/publisher/sites"}
    op = _opener()
    req = urllib.request.Request(API, data=data, headers=h, method="POST")
    try:
        r = op.open(req, timeout=60)
        st, body = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        st, body = e.code, e.read().decode("utf-8", "replace")
    if st in (401, 403) and retry_login:
        login()
        return gql(query, variables, opname, retry_login=False)
    return st, body


def query_sites():
    q = """query SitesAndZones {
      sites { siteId domain domainValid archived status type category statusApproval reason
              validationCode validationCodeTxt addZoneUrl editUrl
              validationCodeFile { file content }
              zoneTypesAllow { name value size prohibitionMessage }
              zones { zoneId siteId typeGroup size status statusApproval archived
                      invocationName titleUser
                      invocationCode { name type script description } } } }"""
    return json.loads(gql(q, opname="SitesAndZones")[1])      # noqa: E226


def add_site(domain):
    q = """mutation siteAdd($domain: String!, $type: SiteType!, $category: SiteCategoryType!) {
      siteAdd(domain: $domain, type: $type, category: $category) { siteId } }"""
    return json.loads(gql(q, {"domain": domain, "type": "TYPE_REGILAR",
                              "category": "CATEGORY_MAINSTREAM"}, "siteAdd")[1])


def introspect(type_name):
    q = '{ __type(name: "%s") { name fields { name args { name type { kind name ofType { kind name } } } } } }' % type_name
    return json.loads(gql(q)[1])


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "login":
        print(login())
    elif cmd == "sites":
        print(json.dumps(query_sites(), indent=1))
    elif cmd == "add-site":
        print(json.dumps(add_site(args[1]), indent=1))
    elif cmd == "introspect":
        print(json.dumps(introspect(args[1]), indent=1))
    elif cmd == "call":
        q = args[1]
        vars_ = json.loads(args[2]) if len(args) > 2 else {}
        print(gql(q, vars_)[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
