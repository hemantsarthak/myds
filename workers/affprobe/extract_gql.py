import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for name in ("GetPartnerMarker","GetPartnerLinks","GetPrograms"):
    i = src.find(name)
    # find the query string: search backwards for "query "
    if i < 0: print(name, "NOT FOUND"); continue
    start = src.rfind("query", 0, i)
    seg = src[start:start+1500]
    print("=====", name, "at", i)
    print(seg[:1200].replace("\\n","\n"))
    print()
