import re, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    r=op.open(req,timeout=30); return r.geturl(), r.read().decode("utf-8","replace")
try:
    u,t = fetch("https://adcash.myadcash.com/register")
    print("ADCASH", u, len(t))
    title=re.search(r"<title[^>]*>(.*?)</title>",t,re.S|re.I); print("TITLE", title.group(1).strip() if title else "")
    for f in re.findall(r"<form[^>]*>", t, re.I)[:6]: print("FORM:", re.sub(r"\s+"," ",f)[:300])
    for i in re.findall(r'<input[^>]*>', t)[:20]: print("IN:", re.sub(r"\s+"," ",i)[:200])
    print("CAPS:", [k for k in ("turnstile","recaptcha","hcaptcha","captcha") if k in t.lower()])
    print("TEXT:", re.sub(r"\s+"," ", re.sub(r"<[^>]+>"," ",t))[:800])
except Exception as e:
    print("ERR", e)
