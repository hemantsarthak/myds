import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for pat in ("createPartnerLink(", "CreatePartnerLinkInput", "createPartnerLink({"):
    print("==", pat)
    for m in list(re.finditer(re.escape(pat), src))[:4]:
        print("  ", src[max(0,m.start()-260):m.start()+320].replace("\\n"," ")[:520])
