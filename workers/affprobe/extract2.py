import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for m in re.finditer(r"GetPartnerMarker", src):
    seg = src[m.start()-80:m.start()+700]
    if "query" in seg: print("----", m.start()); print(seg.replace("\\n","\n")[:700]); print()
