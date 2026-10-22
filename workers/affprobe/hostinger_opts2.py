import re
from probe import get
s,u,body,h = get("https://affiliates.hostinger.com/signup")
# find all <select ...name="data[SignupAnswer]..."> with raw inner html
for sel in re.finditer(r'(<select[^>]*name="(data\[SignupAnswer\][^"]*)"[^>]*>)', body):
    start = sel.start()
    end = body.find("</select>", start)
    raw = body[start:end+9]
    print("=== ", sel.group(2), "LEN", len(raw))
    print(raw[:1500].replace("\n"," "))
    print()
# also look for signup_question / options json
for kw in ("signup_question","SignupQuestion","options","optgroup"):
    idxs = [m.start() for m in re.finditer(kw, body)][:5]
    print(kw, idxs)
