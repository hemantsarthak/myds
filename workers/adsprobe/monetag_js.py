import re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8","replace")
base="https://publishers.monetag.com"
app=get(base+"/app-ea8e3fbee1d3ec5c441e.js")
lib=get(base+"/lib-54d6cf86129233b4d224.js")
open("workers/adsprobe/_monetag_app.js","w",encoding="utf-8").write(app)
open("workers/adsprobe/_monetag_lib.js","w",encoding="utf-8").write(lib)
print("app len", len(app), "lib len", len(lib))
for kw in ["signUp","signup","SignUp","register","Register","/api/","apiUrl","API_URL","recaptcha","captcha","turnstile"]:
    hits=[m.start() for m in re.finditer(re.escape(kw), app)]
    print(kw, len(hits), hits[:5])
