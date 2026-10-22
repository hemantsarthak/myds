"""Submit the GitHub Pages URLs to IndexNow using a keyLocation on the same host (project subpath).

IndexNow allows a custom keyLocation as long as it is on the submitted host; the project Pages site
hosts the key file at /myds/<key>.txt, which may be accepted."""
import json
import re
import urllib.request

KEY = "moneyds7f3a9c2e5b1d4f8a6c0e2d9b5a7f1c3e"
HOST = "hemantsarthak.github.io"
BASE = f"https://{HOST}/myds"
KEY_LOCATION = f"{BASE}/{KEY}.txt"

sm = urllib.request.urlopen(urllib.request.Request(f"{BASE}/sitemap.xml", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
urls = re.findall(r"<loc>([^<]+)</loc>", sm)
print("urls to submit:", len(urls))
payload = {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls}
body = json.dumps(payload).encode()
for endpoint in ("https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow"):
    req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "Mozilla/5.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            print(endpoint, "->", r.status, r.read()[:200])
    except urllib.error.HTTPError as e:
        print(endpoint, "-> HTTP", e.code, e.read()[:300])
    except Exception as e:
        print(endpoint, "-> ERR", str(e)[:120])
