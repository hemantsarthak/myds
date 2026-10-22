import re, sys, json
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
i = src.find("query CurrentPartner")
seg = src[i:i+3000]
end = seg.find("`,SFe")
print(seg[:end].replace("\\n","\n"))
