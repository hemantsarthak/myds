import re, json
from probe import get
import http.cookiejar
cj = http.cookiejar.CookieJar()
att = json.load(open(r"..\..\shared\hostinger_signup_attempt.json", encoding="utf-8"))
# try login
s,u,body,h = get("https://affiliates.hostinger.com/", cj=cj)
hk = {}
for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', body):
    t=m.group(0); n=(re.search(r'name="([^"]*)"',t) or [None,""])[1]; v=(re.search(r'value="([^"]*)"',t) or [None,""])[1]
    if n: hk[n]=v
print("login hidden:", list(hk.keys()))
data={k:v for k,v in hk.items()}
data["data[AffiliateUser][email]"]=att["email"]
data["data[AffiliateUser][password]"]=att["password"]
s2,u2,b2,h2 = get("https://affiliates.hostinger.com/", data=data, cj=cj)
print("LOGIN POST", s2, u2, "len", len(b2))
print("TITLE", (re.search(r"<title[^>]*>(.*?)</title>", b2, re.S) or [None,""])[1][:120])
txt = re.sub(r"<script.*?</script>","",b2,flags=re.S)
txt = re.sub(r"<style.*?</style>","",txt,flags=re.S)
txt = re.sub(r"<[^>]+>"," ",txt)
txt = re.sub(r"\s+"," ",txt)
print("BODY:", txt[:1200])
