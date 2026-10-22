import urllib.request, urllib.parse
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print("   ->", code, newurl[:220]); return None
op = urllib.request.build_opener(NR)
for p in (1,2,3,4119,84):
    u = f"https://tp.media/r?marker=793747&p={p}&u=" + urllib.parse.quote("https://www.booking.com/", safe="")
    try:
        r = op.open(urllib.request.Request(u, headers={"User-Agent":UA}), timeout=20)
        print(f"p={p} STATUS", r.status)
    except urllib.error.HTTPError as e:
        body = e.read()[:200]
        print(f"p={p} HTTP", e.code, "loc:", (e.headers.get("Location") or "")[:160], "body:", body[:120])
    except Exception as e:
        print(f"p={p} ERR", repr(e)[:100])
