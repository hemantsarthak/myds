import re
from probe import get
s,u,body,h = get("https://affiliates.opiemarketing.com/affiliates/signup.php")
print("STATUS",s,len(body))
i = body.find('id="SignupForm"')
print("idx", i)
frag = body[i-100:i+9000] if i>0 else body[:9000]
for mm in re.finditer(r"<(input|select|textarea)[^>]*>", frag):
    t=mm.group(0)
    nm=(re.search(r'name="([^"]*)"',t) or [None,""])[1]
    ty=(re.search(r'type="([^"]*)"',t) or [None,""])[1]
    print(f"  {mm.group(1):8s} {nm!r:38s} {ty!r}")
print("--- recaptcha/turnstile ---", len(re.findall(r"recaptcha|turnstile", frag, re.I)))
