import re, json, http.cookiejar
from probe import get
cj = http.cookiejar.CookieJar()
att = json.load(open(r"..\..\shared\cuelinks_signup_attempt.json", encoding="utf-8"))
s,u,body,h = get("https://www.cuelinks.com/login", cj=cj)
tok = (re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', body) or [None,""])[1]
print("login GET", s, "token", bool(tok))
data = {"authenticity_token": tok, "email": att["email"], "password": att["password"]}
s2,u2,b2,h2 = get("https://www.cuelinks.com/login", data=data, cj=cj)
print("LOGIN POST", s2, u2, len(b2))
txt = re.sub(r"<script.*?</script>|<style.*?</style>","",b2,flags=re.S|re.I)
txt = re.sub(r"<[^>]+>"," ",txt); txt=re.sub(r"\s+"," ",txt)
print("TXT:", txt[:900])
print("COOKIES:", [c.name for c in cj])
open(r"..\..\shared\cuelinks_cookies.json","w",encoding="utf-8").write(json.dumps({c.name:c.value for c in cj}, indent=1))
