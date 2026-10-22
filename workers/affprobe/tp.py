import re
from probe import get
for u in ("https://www.travelpayouts.com/","https://app.travelpayouts.com/signup","https://www.travelpayouts.com/join","https://app.travelpayouts.com/"):
    s,u2,b,h = get(u)
    print("==",u,"->",s,u2,len(b), (re.search(r"<title[^>]*>(.*?)</title>",b,re.S) or [None,""])[1][:80])
    for l in sorted(set(re.findall(r'href="([^"]+)"', b))):
        if re.search(r"signup|register|join|affiliate", l, re.I): print("   LINK", l[:120])
