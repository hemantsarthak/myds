import re
from probe import get
s,u,body,h = get("https://affiliates.hostinger.com/")
m = re.search(r"<form[^>]*id=\"loginForm\"[^>]*>(.*?)</form>", body, re.S)
print(m.group(1)[:3000] if m else "NO FORM")
