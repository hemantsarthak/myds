import re, sys, json
from probe import get
s,u,body,h = get("https://affiliates.hostinger.com/signup")
print("STATUS",s,len(body))
# print the signup form region
m = re.search(r"<form[^>]*action=\"/signup\"[^>]*>(.*?)</form>", body, re.S)
frag = m.group(1) if m else body
print("FORM LEN", len(frag))
for mm in re.finditer(r"<(input|select|textarea)[^>]*>", frag, re.S):
    t = mm.group(0)
    name = (re.search(r'name=\"([^\"]*)\"', t) or [None,""])[1]
    typ = (re.search(r'type=\"([^\"]*)\"', t) or [None,""])[1]
    val = (re.search(r'value=\"([^\"]*)\"', t) or [None,""])[1]
    print(f"  {mm.group(1):8s} name={name!r:40s} type={typ!r:12s} value={val[:60]!r}")
print("--- labels/selects options ---")
for mm in re.finditer(r"<label[^>]*>(.*?)</label>", frag, re.S):
    print("LBL", re.sub(r"<[^>]+>","",mm.group(1)).strip()[:80])
