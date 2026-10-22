import urllib.request, urllib.parse
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
tests = [
 "https://tp.media/r?marker=793747&u=" + urllib.parse.quote("https://www.booking.com/", safe=""),
 "https://tp.media/click?shmarker=793747&promo_id=0&source_type=link&type=click&campaign_id=84",
 "https://tp.media/r?marker=793747&p=0&u=" + urllib.parse.quote("https://www.booking.com/", safe=""),
]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print("  REDIRECT ->", code, newurl[:200])
        return None
op = urllib.request.build_opener(NoRedirect)
for t in tests:
    print("== ", t[:110])
    try:
        r = op.open(urllib.request.Request(t, headers={"User-Agent":UA}), timeout=25)
        print("  STATUS", r.status, r.geturl())
    except urllib.error.HTTPError as e:
        print("  HTTP", e.code, "Location:", (e.headers.get("Location") or "")[:220])
    except Exception as e:
        print("  ERR", repr(e)[:150])
