import json, pathlib
shared = pathlib.Path("shared")
part = json.loads((shared/"travelpayouts_partner.json").read_text(encoding="utf-8"))["data"]
att = json.loads((shared/"travelpayouts_signup_attempt.json").read_text(encoding="utf-8"))
progs = json.loads((shared/"travelpayouts_programs.json").read_text(encoding="utf-8"))["data"]["brandPrograms"]
cp = part["currentPartner"]
out = {
 "service": "travelpayouts",
 "email": att["email"], "password": att["password"],
 "login_url": "https://app.travelpayouts.com/",
 "partner_id": cp["id"],
 "marker": cp["userInfo"]["marker"],
 "api_token": part["authorizedUser"]["userInfo"]["apiToken"],
 "currency": cp["currency"], "created_at": cp["createdAt"],
 "payment_requisite": cp.get("unconfirmedRequisite"),
 "programs_count": len(progs),
 "programs": {str(p["id"]): p["name"] for p in progs if p.get("id") is not None},
 "created_by": "agent (autonomous)", "date": "2026-10-22",
}
(shared/"travelpayouts_account.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("wrote shared/travelpayouts_account.json ; marker", out["marker"], "programs", out["programs_count"])
