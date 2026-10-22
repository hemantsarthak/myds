import re, json, sys, time, urllib.request, urllib.parse, http.cookiejar, subprocess

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
EMAIL = "hilltopads@tekify.xyz"
NAME = "Tekify Ads"
PASSWORD = json.load(open("shared/monetag_signup.json"))  # placeholder, replaced below
PW = "Ht!" + "Q7m2Kx9Pz4Wv" + "n8R"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
base = "https://hilltopads.com"

def get(url, referer=None):
    h = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language":"en-US,en;q=0.9"}
    if referer: h["Referer"] = referer
    r = op.open(urllib.request.Request(url, headers=h), timeout=40)
    return r.geturl(), r.status, r.read().decode("utf-8", "replace")

def post(url, data, referer):
    body = urllib.parse.urlencode(data, doseq=True).encode()
    h = {"User-Agent": UA, "Accept": "application/json, text/javascript, */*; q=0.01",
         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
         "X-Requested-With": "XMLHttpRequest", "Referer": referer,
         "Accept-Language": "en-US,en;q=0.9", "Origin": "https://hilltopads.com"}
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        r = op.open(req, timeout=40)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace"), dict(e.headers)

u, st, t = get(base + "/signup")
print("GET", st, u, len(t))
print("recaptcha script:", re.findall(r'[^"\']*recaptcha[^"\']*\.js[^"\']*', t)[:5])
csrf = re.search(r'<input id="csrfToken" type="hidden" name="([^"]+)" value="([^"]*)"', t)
print("csrf found:", bool(csrf), csrf.groups()[:1] if csrf else None)
redirect = re.search(r'<input type="hidden" name="redirect" value="([^"]*)"', t)
print("redirect:", redirect.group(1)[:60] if redirect else None)

data = {
    "who": "publisher",
    "name": NAME,
    "email": EMAIL,
    "password": PW,
    "legal": "1",
    "vertical": "both",
    "lang": "en",
}
if redirect: data["redirect"] = redirect.group(1)
if csrf: data[csrf.group(1)] = csrf.group(2)

st, body, headers = post(base + "/signup", data, base + "/signup")
print("POST", st)
print("BODY:", body[:1500])
print("HDRS:", {k:v for k,v in headers.items() if k.lower() in ("content-type","location","set-cookie")})
json.dump({"email": EMAIL, "password": PW, "status": st, "body": body[:2000]}, open("shared/hilltop_signup_attempt.json","w"), indent=2)
