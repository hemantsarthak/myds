import urllib.request, urllib.parse
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print("   ->", code, newurl[:200]); return None
op = urllib.request.build_opener(NR)
tests = [
 "https://tp.media/click?shmarker=793747&promo_id=84&source_type=link&type=click&campaign_id=84",
 "https://tp.media/click?shmarker=793747&promo_id=84&campaign_id=84",
 "https://tp.media/r?marker=793747&p=84&u=" + urllib.parse.quote("https://www.booking.com/", safe=""),
]
for t in tests:
    print("==", t[:110])
    try:
        r = op.open(urllib.request.Request(t, headers={"User-Agent":UA}), timeout=20)
        print("   STATUS", r.status, r.geturl()[:150])
    except urllib.error.HTTPError as e:
        print("   HTTP", e.code, "loc:", (e.headers.get("Location") or "")[:150], "body:", e.read()[:100])
    except Exception as e:
        print("   ERR", repr(e)[:80])
