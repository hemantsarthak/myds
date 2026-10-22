import re, json, http.cookiejar, secrets
from probe import get
cj = http.cookiejar.CookieJar()
s,u,body,h = get("https://affiliates.hostinger.com/users/signup/", cj=cj)
print("GET", s, u, len(body))
hidden={}
for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', body):
    t=m.group(0); n=(re.search(r'name="([^"]*)"',t) or [None,""])[1]; v=(re.search(r'value="([^"]*)"',t) or [None,""])[1]
    if n: hidden[n]=v
pwd = "Ab" + secrets.token_hex(4) + "!9z"   # 12 chars
data={"_method":"POST","data[_Token][key]":hidden.get("data[_Token][key]","")}
data.update({
 "data[Affiliate][id]":"", "data[Affiliate][referral_id]":"", "data[AffiliateUser][id]":"",
 "data[Affiliate][company]":"Tekify", "data[Affiliate][website]":"https://tekify.xyz",
 "data[Affiliate][address1]":"401 Andheri East","data[Affiliate][address2]":"Near WEH Metro",
 "data[Affiliate][city]":"Mumbai","data[Affiliate][country]":"IN","data[Affiliate][region]":"MH",
 "data[Affiliate][zipcode]":"400069","data[Affiliate][phone]":"+91 9000000000",
 "data[AffiliateMeta][ssn_tax]":"",
 "data[AffiliateUser][first_name]":"Hemant","data[AffiliateUser][last_name]":"Sarthak",
 "data[AffiliateUser][title]":"Owner","data[AffiliateUser][email]":"hostinger@tekify.xyz",
 "data[AffiliateUser][password]":pwd,"data[AffiliateUser][password_confirmation]":pwd,
 "data[SignupAnswer][1][answer]":"Blog/Site","data[SignupAnswer][2][answer]":"https://tekify.xyz",
 "data[SignupAnswer][3][answer]":"Hosting","data[SignupAnswer][4][answer]":"Under 1,000/month",
 "data[SignupAnswer][7][answer]":"I understand","data[SignupAnswer][8][answer]":"I understand",
 "data[SignupAnswer][9][answer]":"Yes","data[SignupAnswer][10][answer]":"data utility sites",
 "data[AffiliateUser][terms_agreement]":"1","data[AffiliateUser][terms_third_party_agreement]":"1",
 "data[_Token][fields]":hidden.get("data[_Token][fields]",""),
})
s2,u2,b2,h2 = get("https://affiliates.hostinger.com/users/signup/", data=data, cj=cj)
print("POST2", s2, u2)
for m in re.finditer(r"(?is)<(?:div|p|span|li)[^>]*>(.{0,400}?)</(?:div|p|span|li)>", b2):
    t=re.sub(r"<[^>]+>"," ",m.group(1)); t=re.sub(r"\s+"," ",t).strip()
    if any(k in t.lower() for k in ("already","review","error","exist","failed")) and len(t)>10:
        print("MSG:", t[:300])
