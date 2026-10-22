import re
from probe import get
s,u,body,h = get("https://www.cuelinks.com/signup")
i = body.find('id="signupForm"'); j = body.find("</form>", i)
frag = body[i:j]
print("FORM LEN", len(frag))
for mm in re.finditer(r"<(input|select|textarea|button)[^>]*>", frag):
    t=mm.group(0)
    nm=(re.search(r'name="([^"]*)"',t) or [None,""])[1]
    ty=(re.search(r'type="([^"]*)"',t) or [None,""])[1]
    idd=(re.search(r'id="([^"]*)"',t) or [None,""])[1]
    print(f"  {mm.group(1):8s} name={nm!r:26s} type={ty!r:10s} id={idd!r}")
print("--- text of labels ---")
for m in re.finditer(r"<label[^>]*>(.*?)</label>", frag, re.S):
    t=re.sub(r"<[^>]+>","",m.group(1)).strip()
    if t: print("LBL:", t[:90])
# hidden inputs exist? (g-recaptcha)
print("recaptcha:", re.findall(r"(g-recaptcha|recaptcha)", frag))
