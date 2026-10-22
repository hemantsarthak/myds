import re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    r = urllib.request.urlopen(req, timeout=25)
    return r.geturl(), r.read()
u, body = get("https://publishers.monetag.com/signup")
txt = body.decode("utf-8","replace")
print("FINAL", u)
print(txt[:3000])
print("---scripts---")
for m in re.findall(r'<script[^>]*src="([^"]+)"', txt): print(m)
for m in re.findall(r'href="([^"]+)"', txt)[:20]: print("HREF", m)
