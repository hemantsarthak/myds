import re, json, http.cookiejar
from probe import get
cj = http.cookiejar.CookieJar()
att = json.load(open(r"..\..\shared\hostinger_signup_attempt.json", encoding="utf-8"))
s,u,body,h = get("https://affiliates.hostinger.com/", cj=cj)
data = {"_method":"POST", "data[_Token][key]":"", "data[User][email]": att["email"], "data[User][password]": att["password"]}
s2,u2,b2,h2 = get("https://affiliates.hostinger.com/", data=data, cj=cj)
# raw diff of body: search alerts
for m in re.finditer(r"(?is)<(?:div|p|span)[^>]*class=\"[^\"]*(?:alert|error|flash|message|notice)[^\"]*\"[^>]*>(.{0,400}?)</", b2):
    print("ALERT:", re.sub(r"<[^>]+>"," ",m.group(1)).strip()[:300])
# does page have a login error element id?
for m in re.finditer(r'id="[^"]*(?:error|alert|flash)[^"]*"', b2):
    print("ID:", m.group(0))
print("has loginForm:", "loginForm" in b2)
# check for the "review" text
print("review in body:", "being reviewed" in b2)
