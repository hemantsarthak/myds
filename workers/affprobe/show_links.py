import json
d = json.load(open("shared/travelpayouts_links.json", encoding="utf-8"))
for k,v in d.items():
    if v.get("status")=="SUCCESS":
        print(k, "|", v["shortUrl"], "|", v["fullUrl"])
