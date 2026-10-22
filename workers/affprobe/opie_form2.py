import re
from probe import get
s,u,body,h = get("https://affiliates.opiemarketing.com/affiliates/signup.php")
for m in list(re.finditer(r'(?i)signupform', body))[:5]:
    print("HIT", m.start(), body[max(0,m.start()-120):m.start()+260].replace("\n"," "))
print("inputs total:", len(re.findall(r"<input", body)))
# show all input names
names = re.findall(r'<input[^>]*name="([^"]+)"', body)
print("input names:", names[:50])
print("recaptcha:", len(re.findall(r"recaptcha", body, re.I)), "turnstile:", len(re.findall(r"turnstile", body, re.I)))
