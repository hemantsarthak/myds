"""Regression checks for calculator maths.

Each check is derived from the *closed-form* answer, not from the code under test, so a
broken formula fails here before it reaches the site. Run: python sites/calculators/check_formulas.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

import catalog  # noqa: E402
from core import defaults  # noqa: E402

BY = catalog.BY
fails = []


def near(name, got, want, tol=0.02):
    ok = abs(float(got) - float(want)) <= tol
    print(("  ok   " if ok else "  FAIL ") + f"{name}: got {got!r} want {want!r}")
    if not ok:
        fails.append(name)


def run(slug, **over):
    c = BY[slug]
    v = defaults(c)
    v.update(over)
    return c["py"](v)


# mortgage: 250,000 at 6%/yr for 30 years -> 1498.88/month (standard amortisation)
near("mortgage payment", run("mortgage-payment")["payment"], 1498.88)
# loan: 20,000 at 8%/yr for 5 years -> 405.53/month
near("loan payment", run("loan-payment")["payment"], 405.53)
# 100 m -> 328.084 ft
near("length 100m -> ft", float(run("length-converter")["ft"].split()[0].replace(",", "")), 328.084)
# 70 kg -> 154.324 lb
near("weight 70kg -> lb", float(run("weight-converter")["lb"].split()[0].replace(",", "")), 154.324)
# 100 C -> 212 F
near("100C -> F", float(run("temperature-converter")["f"].split()[0]), 212.0)
# 8.25% sales tax on $100 -> $8.25
near("sales tax", run("sales-tax")["tax"], 8.25)
# 180 lb, 5'10" -> BMI 25.83
near("bmi", run("bmi-calculator")["bmi"], 25.83, 0.05)
# 1.5 kW x 4 h x 30 d at $0.15/kWh -> $27
near("electricity", run("electricity-cost")["cost"], 27.0)
# 300 mi at 30 mpg, $3.50/gal -> $35
near("fuel", run("fuel-cost-mpg")["cost"], 35.0)
# 22% APR, $5,000 balance, $200/mo -> ~34 months
near("card months", float(str(run("credit-card-payoff")["months"]).split()[0]), 34, 1)
# 10,000 -> 20,000 over 5 years -> CAGR 14.87%
near("cagr", run("cagr-calculator")["cagr"], 14.87, 0.02)

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
