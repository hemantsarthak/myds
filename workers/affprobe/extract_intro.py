import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
pats = ["IntroStepsEnum","setIntroStep","introStep"]
for p in pats:
    print("==", p)
    for m in list(re.finditer(re.escape(p), src))[:6]:
        print("  ", src[max(0,m.start()-160):m.start()+260].replace("\\n"," ")[:380])
