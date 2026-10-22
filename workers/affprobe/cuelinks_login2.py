import re, json, http.cookiejar, urllib.parse, urllib.request, time
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
H = {"User-Agent": UA,
 "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
 "Accept-Language":"en-US,en;q=0.9","Accept-Encoding":"identity",
 "Upgrade-Insecure-Requests":"1","Sec-Fetch-Dest":"document","Sec-Fetch-Mode":"navigate",
 "Sec-Fetch-Site":"none","Sec-Fetch-User":"?1","Cache-Control":"max-age=0"}
def req(url, data=None, ref=None):
    h = dict(H)
    if ref: h["Referer"]=ref; h["Origin"]="https://www.cuelinks.com"; h["Sec-Fetch-Site"]="same-origin"
    body=None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        h["Content-Type"]="application/x-www-form-urlencoded"
    r = urllib.request.Request(url, data=body, headers=h)
    try:
        resp = op.open(r, timeout=30)
        return resp.status, resp.geturl(), resp.read().decode("utf-8","replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, url, e.read().decode("utf-8","replace"), dict(e.headers)
att = json.load(open(r"..\..\shared\cuelinks_signup_attempt.json", encoding="utf-8"))
s,u,body,h = req("https://www.cuelinks.com/login")
tok = (re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', body) or [None,""])[1]
time.sleep(1)
s2,u2,b2,h2 = req("https://www.cuelinks.com/login", data={"authenticity_token":tok,"email":att["email"],"password":att["password"]}, ref="https://www.cuelinks.com/login")
print("LOGIN", s2, u2, len(b2))
open("cuelinks_login_out.html","w",encoding="utf-8").write(b2)
txt = re.sub(r"<script.*?</script>|<style.*?</style>","",b2,flags=re.S|re.I)
txt = re.sub(r"<[^>]+>"," ",txt); txt=re.sub(r"\s+"," ",txt)
print(txt[:800])
print("COOKIES:", [c.name for c in cj])
