import re
from probe import get
s,u,body,h = get("https://www.digitalocean.com/referral-program")
links = sorted(set(re.findall(r'href="([^"]+)"', body)))
for l in links:
    if any(k in l.lower() for k in ("referral","signup","register","affiliate","partner","auth")):
        print("LINK", l)
print("--- text mentions ---")
txt = re.sub(r"<script.*?</script>|<style.*?</style>","",body,flags=re.S|re.I)
txt = re.sub(r"<[^>]+>"," ",txt); txt = re.sub(r"\s+"," ",txt)
for kw in ("Sign up","referral link","$200","$25","credit","affiliate"):
    for m in list(re.finditer(re.escape(kw), txt, re.I))[:3]:
        print(f"[{kw}]", txt[max(0,m.start()-120):m.start()+220])
