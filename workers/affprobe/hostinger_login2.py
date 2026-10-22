import re, json, http.cookiejar
from probe import get
cj = http.cookiejar.CookieJar()
att = json.load(open(r"..\..\shared\hostinger_signup_attempt.json", encoding="utf-8"))
s,u,body,h = get("https://affiliates.hostinger.com/", cj=cj)
data = {"_method":"POST", "data[User][email]": att["email"], "data[User][password]": att["password"]}
s2,u2,b2,h2 = get("https://affiliates.hostinger.com/", data=data, cj=cj)
print("LOGIN POST", s2, u2, "len", len(b2))
txt = re.sub(r"<script.*?</script>|<style.*?</style>","",b2,flags=re.S|re.I)
txt = re.sub(r"<[^>]+>"," ",txt); txt = re.sub(r"\s+"," ",txt)
print("TITLE", (re.search(r"<title[^>]*>(.*?)</title>", b2, re.S) or [None,""])[1][:100])
# look for error messages
for m in re.finditer(r'(?i)(incorrect|invalid|wrong|not (?:yet )?approved|review|pending|error)', txt):
    print("MSG:", txt[max(0,m.start()-150):m.start()+200])
    break
print("COOKIES:", [c.name for c in cj])
print("SNIP:", txt[:600])
