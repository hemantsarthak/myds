import sys, json, re, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
urls = [
 ("monetag", "https://monetag.com/"),
 ("monetag_pub", "https://publisher.monetag.com/"),
 ("monetag_pub2", "https://publishers.monetag.com/"),
 ("adsterra", "https://publisher.adsterra.com/"),
 ("popads", "https://www.popads.net/"),
 ("hilltop", "https://hilltopads.com/"),
 ("aads", "https://aads.com/"),
 ("adcash", "https://adcash.com/publisher/"),
]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPRedirectHandler())
op.addheaders = [("User-Agent", UA), ("Accept", "text/html,application/xhtml+xml")]
for name, url in urls:
    try:
        r = op.open(url, timeout=25)
        body = r.read()
        txt = body.decode("utf-8", "replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", txt, re.S|re.I)
        caps = [c for c in ("recaptcha","hcaptcha","turnstile","cf-challenge","g-recaptcha","captcha") if c in txt.lower()]
        forms = len(re.findall(r"<form", txt, re.I))
        print(f"{name:14} {r.status} final={r.geturl()[:90]} len={len(body)} title={(title.group(1).strip()[:70] if title else '')!r} forms={forms} caps={caps}")
    except Exception as e:
        print(f"{name:14} ERR {type(e).__name__}: {str(e)[:120]}")
