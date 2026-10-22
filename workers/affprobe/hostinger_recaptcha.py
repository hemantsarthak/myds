import re
from probe import get
s,u,body,h = get("https://affiliates.hostinger.com/signup")
print("recaptcha refs:", len(re.findall("recaptcha", body, re.I)))
for m in re.finditer(r".{200}recaptcha.{300}", body, re.I|re.S):
    ctx = re.sub(r"\s+"," ",m.group(0))
    print("---", ctx[:500])
