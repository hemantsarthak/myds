import base64, urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
for marker in ("793747",):
    b64 = base64.b64encode(marker.encode()).decode()
    for url in (f"https://tp-em.com/{b64}.js",
                f"https://tp-em.com/{b64}.js?t=764877",
                f"https://tp-em.com/{b64}".replace("{b64}", b64),
                "https://tp-em.com/" ):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":UA}), timeout=15)
            body = r.read()[:300]
            print("OK", r.status, url, "|", body[:200])
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, url, "|", e.read()[:100])
        except Exception as e:
            print("ERR", url, repr(e)[:80])
