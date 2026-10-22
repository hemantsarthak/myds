import re
app=open("workers/adsprobe/_monetag_app.js",encoding="utf-8").read()
def ctx(pos, w=420): return app[max(0,pos-w):pos+w].replace("\n"," ")
for kw in ["/api/","signUp","signup","captcha"]:
    print("="*20, kw)
    for m in list(re.finditer(re.escape(kw), app))[:8]:
        print("...", ctx(m.start())[:840]); print()
