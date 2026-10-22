import re, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    r=op.open(req,timeout=30); return r.geturl(), r.read().decode("utf-8","replace")

# PopAds register detail
u, t = fetch("https://www.popads.net/users/register")
print("== POPADS", u, len(t))
for f in re.findall(r"<form[^>]*>.*?</form>", t, re.S|re.I)[:2]:
    print("FORM:", re.sub(r"\s+"," ",f)[:1500])
print("CAPTCHA HINTS:", [k for k in ("turnstile","recaptcha","hcaptcha","cf_chl","captcha") if k in t.lower()])

# HilltopAds signup
u, t = fetch("https://hilltopads.com/signup")
print("\n== HILLTOP", u, len(t))
print("CAPTCHA HINTS:", [k for k in ("turnstile","recaptcha","hcaptcha","cf_chl","captcha") if k in t.lower()])
for f in re.findall(r"<form[^>]*>", t, re.I)[:8]: print("FORM:", re.sub(r"\s+"," ",f)[:250])
for i in re.findall(r'<input[^>]*>', t)[:25]: print("IN:", re.sub(r"\s+"," ",i)[:200])

# Adcash links
u, t = fetch("https://adcash.com/")
print("\n== ADCASH", u, len(t))
links = sorted(set(re.findall(r'href="([^"]*(?:publish|signup|sign-up|register)[^"]*)"', t, re.I)))
print("LINKS:", links[:20])
