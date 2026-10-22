import re, json, http.cookiejar, secrets
from probe import get
cj = http.cookiejar.CookieJar()
s,u,body,h = get("https://www.cuelinks.com/signup", cj=cj)
print("GET", s, len(body))
tok = (re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', body) or re.search(r'value="([^"]+)"[^>]*name="authenticity_token"', body) or [None,""])[1]
print("token:", bool(tok))
pwd = "Cuelinks!9" + secrets.token_hex(3)   # upper/lower/digit/special, >=8
data = {
 "authenticity_token": tok,
 "country_id": "252", "signup_platform": "Desktop",
 "signup_entry_source": "", "signup_keywords": "", "signup_landing_page_url": "",
 "referrer_url": "", "utm_source": "", "utm_medium": "", "utm_campaign": "", "utm_term": "",
 "referral_id": "",
 "first_name": "Hemant", "last_name": "Sarthak",
 "mobile_number": "9000000000", "country_code": "+91",
 "email": "cuelinks@tekify.xyz",
 "password": pwd, "company_name": "Tekify",
 "[channels_attributes][0][source_url]": "https://tekify.xyz",
}
s2,u2,b2,h2 = get("https://www.cuelinks.com/signup", data=data, cj=cj)
print("POST", s2, u2, "len", len(b2))
print("CT:", h2.get("Content-Type"))
title = (re.search(r"<title[^>]*>(.*?)</title>", b2, re.S) or [None,""])[1]
print("TITLE", re.sub(r"\s+"," ",title)[:150])
if "json" in (h2.get("Content-Type") or ""):
    print(b2[:1500])
else:
    txt = re.sub(r"<script.*?</script>|<style.*?</style>","",b2,flags=re.S|re.I)
    txt = re.sub(r"<[^>]+>"," ",txt); txt=re.sub(r"\s+"," ",txt)
    print("TXT:", txt[:1500])
json.dump({"email":"cuelinks@tekify.xyz","password":pwd,"status":s2,"url":u2}, open(r"..\..\shared\cuelinks_signup_attempt.json","w",encoding="utf-8"), indent=1)
