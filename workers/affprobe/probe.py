import sys, re, json, urllib.request, urllib.parse, http.cookiejar, ssl
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
def get(url, data=None, cj=None, timeout=30, extra=None):
    ctx = ssl.create_default_context()
    if cj is not None:
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    else:
        op = urllib.request.build_opener()
    hdrs = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "identity"}
    if extra: hdrs.update(extra)
    if data is not None and isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=data, headers=hdrs)
    try:
        r = op.open(req, timeout=timeout)
        return r.status, r.geturl(), r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, url, e.read().decode("utf-8","replace"), dict(e.headers)
    except Exception as e:
        return -1, url, "ERR: %r" % (e,), {}
if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv)>1 else "https://www.hostinger.com/affiliates"
    s, u, body, h = get(url)
    print("STATUS", s, u, "len", len(body))
    print("TITLE", (re.search(r"<title[^>]*>(.*?)</title>", body, re.S) or [None,""])[1][:200])
    links = sorted(set(re.findall(r'href="(https?://[^"]+)"', body)))
    for l in links:
        if any(k in l.lower() for k in ("affiliate","signup","register","partner","affiliates.hostinger","postaffiliate")):
            print("LINK", l)
    forms = re.findall(r"<form[^>]*>", body)
    for f in forms[:10]: print("FORM", f[:300])
