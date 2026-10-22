import re
from probe import get
from probe import UA
s,u,body,h = get("https://www.cuelinks.com/signup")
i = body.find('id="signupForm"')
print(body[i-200:i+12000])
