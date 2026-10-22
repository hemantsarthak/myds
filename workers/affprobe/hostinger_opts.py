import re
from probe import get
s,u,body,h = get("https://affiliates.hostinger.com/signup")
m = re.search(r"<form[^>]*action=\"/signup\"[^>]*>(.*?)</form>", body, re.S)
frag = m.group(1)
# options for each select
for sel in re.finditer(r"<select[^>]*name=\"([^\"]+)\"[^>]*>(.*?)</select>", frag, re.S):
    name = sel.group(1); inner = sel.group(2)
    opts = re.findall(r"<option[^>]*value=\"([^\"]*)\"[^>]*>(.*?)</option>", inner, re.S)
    print("SELECT", name)
    for v,t in opts:
        t = re.sub(r"<[^>]+>","",t).strip()
        print("   ", repr(v), "->", t[:100])
