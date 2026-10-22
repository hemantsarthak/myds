import socket
for h in ["monetag.com","publishers.monetag.com","publisher.monetag.com","adsterra.com","publishers.adsterra.com","publisher.adsterra.com","www.popads.net","hilltopads.com","aads.com","adcash.com","www.adcash.com"]:
    try: print(h, socket.gethostbyname(h))
    except Exception as e: print(h, "DNSFAIL", e)
