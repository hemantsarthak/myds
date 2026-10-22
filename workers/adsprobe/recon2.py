import re, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
urls = [
 ("monetag_signup","https://monetag.com/signup/"),
 ("monetag_pub_signup","https://publishers.monetag.com/signup"),
 ("adsterra_pub","https://publishers.adsterra.com/"),
 ("adsterra_signup","https://publishers.adsterra.com/signup"),
 ("popads_signup","https://www.popads.net/signup"),
 ("popads_users","https://www.popads.net/users/signup"),
 ("hilltop_pub","https://hilltopads.com/publishers/"),
 ("hilltop_signup","https://hilltopads.com/signup"),
 ("aads_signup","https://aads.com/signup"),
 ("aads_pub","https://aads.com/publisher"),
 ("adcash","https://www.adcash.com/en/publisher/"),
 ("adcash_signup","https://adcash.com/signup"),
]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
for name, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"text/html,*/*"})
        r = op.open(req, timeout=25); body=r.read(); txt=body.decode("utf-8","replace")
        t = re.search(r"<title[^>]*>(.*?)</title>", txt, re.S|re.I)
        print(f"{name:20} {r.status} final={r.geturl()[:80]} len={len(body)} title={(t.group(1).strip()[:60] if t else '')!r}")
    except urllib.error.HTTPError as e:
        print(f"{name:20} HTTP {e.code} {url} -> {e.geturl()[:80]}")
    except Exception as e:
        print(f"{name:20} ERR {type(e).__name__}: {str(e)[:100]}")
