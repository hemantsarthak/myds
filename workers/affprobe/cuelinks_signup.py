import re
from probe import get
s,u,body,h = get("https://www.cuelinks.com/signup")
m = re.search(r"<form[^>]*>(.*?)</form>", body, re.S)
frag = m.group(1) if m else ""
print("FORM LEN", len(frag))
for mm in re.finditer(r"<(input|select|textarea)[^>]*>", frag):
    t=mm.group(0)
    print(" ", (re.search(r'name="([^"]*)"',t) or [None,""])[1], (re.search(r'type="([^"]*)"',t) or [None,""])[1])
# maybe React app -> look for api endpoints / js bundle
print("react?", "__NEXT_DATA__" in body, "script srcs:", re.findall(r'<script[^>]*src="([^"]+)"', body)[:10])
