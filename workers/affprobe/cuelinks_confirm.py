import re, json, http.cookiejar
from probe import get
cj = http.cookiejar.CookieJar()
url = "https://www.cuelinks.com/users/confirmation?confirmation_token=DQVLcfkqBTU2hYyxP1jg"
s,u,body,h = get(url, cj=cj)
print("CONFIRM", s, u, len(body))
txt = re.sub(r"<script.*?</script>|<style.*?</style>","",body,flags=re.S|re.I)
txt = re.sub(r"<[^>]+>"," ",txt); txt=re.sub(r"\s+"," ",txt)
for kw in ("verified","confirmed","Thank","approved","pending","login","review"):
    for m in list(re.finditer(kw, txt, re.I))[:2]:
        print(f"[{kw}]", txt[max(0,m.start()-120):m.start()+220]); break
print("COOKIES:", [c.name for c in cj])
