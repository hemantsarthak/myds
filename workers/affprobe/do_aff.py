import re
from probe import get
s,u,body,h = get("https://www.digitalocean.com/affiliates")
print("STATUS",s,u,len(body))
links = sorted(set(re.findall(r'href="([^"]+)"', body)))
for l in links:
    if any(k in l.lower() for k in ("affiliate","signup","register","partner","apply","impact","tune","refersion","postaffiliate")):
        print("LINK", l)
txt = re.sub(r"<script.*?</script>|<style.*?</style>","",body,flags=re.S|re.I)
txt = re.sub(r"<[^>]+>"," ",txt); txt = re.sub(r"\s+"," ",txt)
for kw in ("commission","payout","apply","100","%","minimum","program"):
    for m in list(re.finditer(re.escape(kw), txt, re.I))[:2]:
        print(f"[{kw}]", txt[max(0,m.start()-150):m.start()+250])
