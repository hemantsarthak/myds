import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for name in ("SetIntroStep","CreatePartnerLink"):
    for m in re.finditer(r"mutation " + name, src):
        seg = src[m.start():m.start()+1400]
        end = seg.find("`,")
        print("=====", name)
        print(seg[: end if end>0 else 900].replace("\\n","\n"))
        print()
        break
