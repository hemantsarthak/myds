import re, json, secrets, string, http.cookiejar, time, sys
from probe import get, UA
import urllib.parse, urllib.request

cj = http.cookiejar.CookieJar()
s,u,body,h = get("https://affiliates.hostinger.com/signup", cj=cj)
print("GET", s, len(body))
hidden = {}
for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', body):
    t = m.group(0)
    n = (re.search(r'name="([^"]*)"', t) or [None,""])[1]
    v = (re.search(r'value="([^"]*)"', t) or [None,""])[1]
    if n: hidden[n] = v
print("hidden keys:", list(hidden.keys())[:20])

pwd = "Tk" + secrets.token_urlsafe(8)[:10] + "!7x"  # <=16 chars
data = {
 "_method": "POST",
 "data[_Token][key]": hidden.get("data[_Token][key]",""),
 "data[Affiliate][id]": "", "data[Affiliate][referral_id]": "", "data[AffiliateUser][id]": "",
 "data[Affiliate][company]": "Tekify",
 "data[Affiliate][website]": "https://tekify.xyz",
 "data[Affiliate][address1]": "401 Andheri East",
 "data[Affiliate][address2]": "Near WEH Metro",
 "data[Affiliate][city]": "Mumbai",
 "data[Affiliate][country]": "IN",
 "data[Affiliate][region]": "MH",
 "data[Affiliate][zipcode]": "400069",
 "data[Affiliate][phone]": "+91 9000000000",
 "data[AffiliateMeta][ssn_tax]": "",
 "data[AffiliateUser][first_name]": "Hemant",
 "data[AffiliateUser][last_name]": "Sarthak",
 "data[AffiliateUser][title]": "Owner",
 "data[AffiliateUser][email]": "hostinger@tekify.xyz",
 "data[AffiliateUser][password]": pwd,
 "data[AffiliateUser][password_confirmation]": pwd,
 "data[SignupAnswer][1][answer]": "Blog/Site",
 "data[SignupAnswer][1][signup_question_id]": "1",
 "data[SignupAnswer][1][class]": "select",
 "data[SignupAnswer][1][required]": "1",
 "data[SignupAnswer][2][answer]": "https://tekify.xyz , https://ifsccodes.tekify.xyz , https://calculators.tekify.xyz",
 "data[SignupAnswer][2][signup_question_id]": "2",
 "data[SignupAnswer][2][class]": "textarea", "data[SignupAnswer][2][required]": "1",
 "data[SignupAnswer][3][answer]": "Hosting",
 "data[SignupAnswer][3][signup_question_id]": "3",
 "data[SignupAnswer][3][class]": "select", "data[SignupAnswer][3][required]": "1",
 "data[SignupAnswer][4][answer]": "Under 1,000 visitors/month (new sites launched 2026-10-22, indexing in progress). Focus: data/utility pages - IFSC bank codes, US ZIP codes, airport codes, calculators.",
 "data[SignupAnswer][4][signup_question_id]": "4",
 "data[SignupAnswer][4][class]": "textarea", "data[SignupAnswer][4][required]": "1",
 "data[SignupAnswer][7][answer]": "I understand",
 "data[SignupAnswer][7][signup_question_id]": "7",
 "data[SignupAnswer][7][class]": "select", "data[SignupAnswer][7][required]": "1",
 "data[SignupAnswer][8][answer]": "I understand",
 "data[SignupAnswer][8][signup_question_id]": "8",
 "data[SignupAnswer][8][class]": "select", "data[SignupAnswer][8][required]": "1",
 "data[SignupAnswer][9][answer]": "Yes",
 "data[SignupAnswer][9][signup_question_id]": "9",
 "data[SignupAnswer][9][class]": "select", "data[SignupAnswer][9][required]": "1",
 "data[SignupAnswer][10][answer]": "We run a network of data-driven utility sites (IFSC codes, US ZIP codes, airport codes, financial calculators) with organic search traffic. Hosting and domains are the natural next purchase for our readers building sites or moving a business online.",
 "data[SignupAnswer][10][signup_question_id]": "10",
 "data[SignupAnswer][10][class]": "textarea", "data[SignupAnswer][10][required]": "1",
 "data[AffiliateUser][terms_agreement]": "1",
 "data[AffiliateUser][terms_third_party_agreement]": "1",
 "data[_Token][fields]": hidden.get("data[_Token][fields]",""),
 "data[_Token][unlocked]": hidden.get("data[_Token][unlocked]",""),
}
s2,u2,body2,h2 = get("https://affiliates.hostinger.com/signup", data=data, cj=cj)
print("POST", s2, u2, "len", len(body2))
title = (re.search(r"<title[^>]*>(.*?)</title>", body2, re.S) or [None,""])[1]
print("TITLE", title[:120])
errs = re.findall(r'<div[^>]*class="[^"]*(?:error|alert|danger|flash)[^"]*"[^>]*>(.*?)</div>', body2, re.S|re.I)
for e in errs[:10]:
    print("ERRBLOCK", re.sub(r"<[^>]+>"," ",e).strip()[:300])
# any "already" / "success" text
for kw in ("success","thank","already","invalid","required","captcha","recaptcha","verify"):
    for m in re.finditer(kw, body2, re.I):
        ctx = re.sub(r"<[^>]+>"," ",body2[max(0,m.start()-120):m.start()+160])
        print("CTX",kw,":", re.sub(r"\s+"," ",ctx)[:260]); break
json.dump({"email":"hostinger@tekify.xyz","password":pwd,"status":s2,"url":u2}, open(r"..\\..\\shared\\hostinger_signup_attempt.json","w",encoding="utf-8"), indent=1)
print("saved attempt file")

