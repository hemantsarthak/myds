import re, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    r=op.open(req,timeout=30); return r.geturl(), r.read().decode("utf-8","replace")
u,t = fetch("https://hilltopads.com/signup")
# extract the signup form block
m = re.search(r'<form class="form form_auth[^>]*>(.*?)</form>', t, re.S)
form = m.group(1) if m else ""
print("FORM LEN", len(form))
print(re.sub(r"\s+"," ", form)[:4000])
print("\n--- recaptcha mentions in page ---")
for mm in re.finditer(r'recaptcha', t, re.I):
    print(re.sub(r"\s+"," ", t[max(0,mm.start()-200):mm.start()+200])[:400]); print()
