"""Smoke test: python test.py (needs network)."""
from tekify_data import zip_code, hospitals, ifsc_bank

print("zip:", zip_code("90210"))
print("hospitals:", hospitals("Johns Hopkins", 2))
print("ifsc branches:", len(ifsc_bank("HDFC")))
