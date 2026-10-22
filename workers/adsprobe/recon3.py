import re, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
urls = [
 ("popads_signup2","https://www.popads.net/users/signup"),
 ("popads_signup3","https://www.popads.net/users/register"),
 ("popads_signup4","https://www.popads.net/signup/user"),
 ("adsterra_beta_signup","https://beta.publishers.adsterra.com/signup"),
 ("adsterra_beta","https://beta.publishers.adsterra.com/"),
 ("aads_root","https://aads.com/"),
 ("adcash_home","https://adcash.com/"),
]
cj=http.cookiejar.CookieJar()
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
for name,url in urls:
    try:
        req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"text/html,*/*"})
        r=op.open(req,timeout=25); b=r.read(); t=b.decode("utf-8","replace")
        title=re.search(r"<title[^>]*>(.*?)</title>",t,re.S|re.I)
        forms=re.findall(r"<form[^>]*>",t,re.I)[:6]
        script_tags=re.findall(r'<script[^>]*src="([^"]+)"[^>]*>',t)[:8]
        print(f"== {name} {r.status} {r.geturl()[:80]} len={len(b)} title={(title.group(1).strip()[:60] if title else '')!r}")
        for f in forms: print("   FORM", f[:150])
        for s in script_tags: print("   SCRIPT", s[:130])
    except Exception as e:
        print(f"== {name} ERR {type(e).__name__}: {str(e)[:100]}")
