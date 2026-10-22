import urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print("   ->", code, newurl[:120]); return None
op = urllib.request.build_opener(NR)
for u in ["https://aviasales.tpo.mx/J2vylIw9","https://airhelp.tpo.mx/U4U92Tbc","https://airalo.tpo.mx/EzBTKOZi","https://kiwi.tpo.mx/i2nhb9Sp"]:
    print("==", u)
    try:
        r = op.open(urllib.request.Request(u, headers={"User-Agent":UA}), timeout=25)
        print("   STATUS", r.status, r.geturl()[:100])
    except urllib.error.HTTPError as e:
        print("   HTTP", e.code, "loc:", (e.headers.get("Location") or "")[:140])
    except Exception as e:
        print("   ERR", repr(e)[:90])
