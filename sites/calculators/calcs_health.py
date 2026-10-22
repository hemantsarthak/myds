#!/usr/bin/env python3
"""Health calculators: BMI, BMR, TDEE, Navy body fat, ideal weight, pregnancy due
date, ovulation estimate."""
from core import calc, num, sel, dat, fnum, r0, iso_add

MONEY = "USD"


def _kg(v, metric_key="weight_kg", lb_key="weight_lb"):
    return float(v[metric_key]) if v["units"] == "metric" else float(v[lb_key]) * 0.45359237


def _cm(v, metric_key="height_cm", ft_key="height_ft", in_key="height_in"):
    return float(v[metric_key]) if v["units"] == "metric" else (float(v[ft_key]) * 12 + float(v[in_key])) * 2.54


# ---------------------------------------------------------------------------
# 1. BMI
def _bmi_py(v):
    h_m = _cm(v) / 100
    w_kg = _kg(v)
    bmi = w_kg / (h_m * h_m) if h_m > 0 else 0.0
    cat = ("Underweight" if bmi < 18.5 else "Normal weight" if bmi < 25
           else "Overweight" if bmi < 30 else "Obese")
    lo, hi = 18.5 * h_m * h_m, 24.9 * h_m * h_m
    if v["units"] == "metric":
        rng = f"{r0(lo)}–{r0(hi)} kg"
    else:
        rng = f"{r0(lo * 2.2046226218)}–{r0(hi * 2.2046226218)} lb"
    return {"bmi": bmi, "category": cat, "range": rng}


BMI = calc(
    slug="bmi-calculator", name="BMI Calculator", cat="health",
    title="BMI Calculator — Body Mass Index for US and Metric Units",
    desc="Calculate your body mass index from your weight and height, see the WHO category and the "
         "healthy weight range for your height. Supports pounds and kilograms.",
    h1="BMI calculator",
    lede="Calculate body mass index from your height and weight, see which WHO category it falls "
         "into and the healthy weight range for your height.",
    fields=[sel("units", "Units", [("us", "US (lb, ft/in)"), ("metric", "Metric (kg, cm)")], "us"),
            num("weight_lb", "Weight", 180, unit="lb", mn=30, mx=1200, step="0.1", show=("units", "us")),
            num("height_ft", "Height — feet", 5, unit="ft", mn=1, mx=8, step=1, show=("units", "us")),
            num("height_in", "Height — inches", 10, unit="in", mn=0, mx=11.9, step="0.5", show=("units", "us")),
            num("weight_kg", "Weight", 80, unit="kg", mn=15, mx=500, step="0.1", show=("units", "metric")),
            num("height_cm", "Height", 178, unit="cm", mn=60, mx=260, step="0.5", show=("units", "metric"))],
    outs=[("bmi", "Body mass index (BMI)", "num1"), ("category", "WHO category", "text"),
          ("range", "Healthy weight range for your height", "text")],
    meter=dict(key="bmi", min=12, max=42, label="BMI", fmt="num1",
               bands=[[18.5, "Underweight", "#6ea8ff"], [25, "Normal weight", "#3aa657"],
                      [30, "Overweight", "#e0912f"], [42, "Obese", "#c75c5c"]]),
    js="""
var metric = v.units === 'metric';
var h = metric ? v.height_cm/100 : (v.height_ft*12+v.height_in)*0.0254;
var w = metric ? v.weight_kg : v.weight_lb*0.45359237;
var bmi = h>0 ? w/(h*h) : 0;
var cat = bmi<18.5?'Underweight':bmi<25?'Normal weight':bmi<30?'Overweight':'Obese';
var lo=18.5*h*h, hi=24.9*h*h;
var range = metric ? r0(lo)+'\\u2013'+r0(hi)+' kg'
                   : r0(lo*2.2046226218)+'\\u2013'+r0(hi*2.2046226218)+' lb';
return {bmi:bmi,category:cat,range:range};
""",
    py=_bmi_py,
    how="""<p>BMI is a single number that relates weight to height: weight in kilograms divided by
height in metres squared, or 703 × weight in pounds divided by height in inches squared. It was
designed as a quick population-level screening tool, not a diagnosis. For most adults it correlates
well enough with body fat to flag risk, which is why doctors, insurers and public health bodies
still use it.</p>
<p>It has real limitations. BMI cannot tell muscle from fat, so a trained athlete can be classified
overweight. It says nothing about where fat sits, and visceral fat around the organs matters more
than total weight. It also uses fixed thresholds that are applied differently for children, and
Asian populations are advised to use lower cut-offs because cardiometabolic risk rises at a lower
BMI. Use the category as a prompt for a conversation, not a verdict.</p>""",
    formula="""<p>Metric: <em>BMI = weight (kg) ÷ height (m)²</em>. US customary:
<em>BMI = 703 × weight (lb) ÷ height (in)²</em>. The healthy range is BMI 18.5–24.9, so the weight
range for a given height is <em>BMI × height²</em>:</p>
<div class="fml"><code>BMI = kg / m²
healthy weight low  = 18.5 × height²
healthy weight high = 24.9 × height²</code></div>
<p>Categories: under 18.5 underweight, 18.5–24.9 normal, 25.0–29.9 overweight, 30 and above
obese (WHO adult thresholds).</p>""",
    example="At {weight_lb} lb and {height_ft} ft {height_in} in, the BMI is {bmi}, which is in the "
            "{category} range. For that height, a BMI between 18.5 and 24.9 corresponds to roughly "
            "{range}.",
    mistakes=[
        "<strong>Using BMI to judge athletes.</strong> Muscle is denser than fat, so heavily "
        "muscled people often score in the overweight range while carrying little fat.",
        "<strong>Ignoring waist circumference.</strong> Waist size and waist-to-height ratio add "
        "information about visceral fat that BMI cannot see.",
        "<strong>Applying adult thresholds to children.</strong> Children and teenagers are assessed "
        "on age- and sex-specific percentile charts, not the adult cut-offs."
    ],
    faq=[
        ("What is a healthy BMI?",
         "For most adults the WHO defines 18.5–24.9 as the healthy range. Some guidelines suggest "
         "lower upper limits for people of Asian descent because risk rises at a lower BMI."),
        ("Does BMI measure body fat?",
         "Not directly. BMI is a proxy based on weight and height. Body-fat scales, calipers and the "
         "US Navy tape method give a better body-fat estimate; DEXA scans are the reference method."),
        ("Is BMI accurate for everyone?",
         "No. It is least reliable for very muscular people, older adults who have lost muscle, "
         "pregnant women and children. It is a screening tool, not a diagnosis."),
    ],
    related=["bmr-calculator", "tdee-calculator", "body-fat-navy", "ideal-weight-calculator"],
    note="Adult WHO thresholds. Not medical advice; BMI does not measure body fat directly.",
)


# ---------------------------------------------------------------------------
# 2. BMR
def _bmr_py(v):
    w = _kg(v)
    h = _cm(v)
    age = float(v["age"])
    male = v["sex"] == "male"
    bmr = 10 * w + 6.25 * h - 5 * age + (5 if male else -161)
    return {"bmr": bmr, "sedentary": bmr * 1.2}


BMR = calc(
    slug="bmr-calculator", name="BMR Calculator", cat="health",
    title="BMR Calculator — Basal Metabolic Rate (Mifflin-St Jeor)",
    desc="Calculate your basal metabolic rate with the Mifflin-St Jeor equation: the calories your "
         "body burns at complete rest, by weight, height, age and sex.",
    h1="BMR calculator",
    lede="Estimate the calories your body needs at complete rest using the Mifflin-St Jeor equation — "
         "the current standard for basal metabolic rate.",
    fields=[sel("units", "Units", [("us", "US (lb, ft/in)"), ("metric", "Metric (kg, cm)")], "us"),
            sel("sex", "Sex", [("male", "Male"), ("female", "Female")], "male"),
            num("age", "Age", 30, unit="years", mn=15, mx=100, step=1),
            num("weight_lb", "Weight", 180, unit="lb", mn=30, mx=1200, step="0.1", show=("units", "us")),
            num("height_ft", "Height — feet", 5, unit="ft", mn=1, mx=8, step=1, show=("units", "us")),
            num("height_in", "Height — inches", 10, unit="in", mn=0, mx=11.9, step=0.5, show=("units", "us")),
            num("weight_kg", "Weight", 80, unit="kg", mn=15, mx=500, step="0.1", show=("units", "metric")),
            num("height_cm", "Height", 178, unit="cm", mn=60, mx=260, step=0.5, show=("units", "metric"))],
    outs=[("bmr", "Basal metabolic rate", "int"),
          ("sedentary", "Maintenance calories if sedentary", "int"),
          ("hourly", "Calories burned per hour at rest", "num1")],
    js="""
var w = v.units==='metric' ? v.weight_kg : v.weight_lb*0.45359237;
var h = v.units==='metric' ? v.height_cm : (v.height_ft*12+v.height_in)*2.54;
var male = v.sex==='male';
var bmr = 10*w + 6.25*h - 5*v.age + (male?5:-161);
return {bmr:bmr, sedentary:bmr*1.2, hourly:bmr/24};
""",
    py=lambda v: {"bmr": _bmr_py(v)["bmr"], "sedentary": _bmr_py(v)["sedentary"],
                  "hourly": _bmr_py(v)["bmr"] / 24},
    how="""<p>Basal metabolic rate is the energy your body uses for the things you cannot switch off:
breathing, circulation, brain activity, cell repair and temperature control. It is measured in a
rested, fasted state and typically accounts for 60–70% of daily calorie expenditure. The
Mifflin-St Jeor equation used here replaced the older Harris-Benedict formula as the standard
because it is more accurate across modern populations.</p>
<p>The result assumes no activity at all. Multiply it by an activity factor to get maintenance
calories (the TDEE calculator does this). BMR falls with age and with loss of muscle mass, and
rises with more muscle and a larger body. That is why two people of the same weight can have
noticeably different BMRs, and why resistance training is valuable for long-term weight
management.</p>""",
    formula="""<p>Mifflin-St Jeor, metric inputs:</p>
<div class="fml"><code>men:   BMR = 10·kg + 6.25·cm − 5·age + 5
women: BMR = 10·kg + 6.25·cm − 5·age − 161</code></div>
<p>To use pounds and inches, convert first: 1 lb = 0.4536 kg, 1 in = 2.54 cm. The sedentary
maintenance figure compounds BMR by the 1.2 activity factor.</p>""",
    example="A {age}-year-old {sex} with the default measurements has a BMR of {bmr} calories a day — "
            "about {hourly} calories an hour at complete rest. Doing nothing but sitting all day, "
            "maintenance would be around {sedentary} calories.",
    mistakes=[
        "<strong>Eating below BMR for long periods.</strong> Severe restriction encourages muscle "
        "loss and lowers BMR, making weight regain more likely.",
        "<strong>Treating BMR as maintenance.</strong> Any movement — walking, working, even "
        "fidgeting — adds to it. Use TDEE for a spending budget.",
        "<strong>Assuming the equation is exact.</strong> Individual variation is usually within "
        "about 10%, but thyroid conditions, some medications and very high muscle mass can shift it "
        "further."
    ],
    faq=[
        ("What is the difference between BMR and TDEE?",
         "BMR is the calories burned at complete rest. TDEE (total daily energy expenditure) "
         "includes BMR plus all activity — movement, exercise and the energy used digesting food."),
        ("Why does BMR drop as I age?",
         "Lean muscle mass tends to decline with age, and muscle is metabolically active tissue. "
         "Strength training and adequate protein slow that loss and help keep BMR higher."),
        ("Is Mifflin-St Jeor the best formula?",
         "It is the most widely recommended predictive equation for adults. If you have access to "
         "indirect calorimetry or a good smart scale trend, measured data beats any formula."),
    ],
    related=["tdee-calculator", "bmi-calculator", "body-fat-navy", "ideal-weight-calculator"],
    note="Predictive equation, not a measurement. Not medical advice.",
)


# ---------------------------------------------------------------------------
# 3. TDEE
ACTIVITY = [("1.2", "Sedentary — desk job, little exercise"),
            ("1.375", "Lightly active — 1–3 workouts a week"),
            ("1.55", "Moderately active — 3–5 workouts a week"),
            ("1.725", "Very active — 6–7 workouts a week"),
            ("1.9", "Extremely active — physical job or 2× daily training")]


def _tdee_py(v):
    bmr = _bmr_py(v)["bmr"]
    factor = float(v["activity"])
    tdee = bmr * factor
    return {"tdee": tdee, "bmr": bmr, "cut": tdee - 500, "bulk": tdee + 300}


TDEE = calc(
    slug="tdee-calculator", name="TDEE Calculator", cat="health",
    title="TDEE Calculator — Daily Calorie Needs With Activity Level",
    desc="Calculate total daily energy expenditure from your BMR and activity level, with calorie "
         "targets for losing, maintaining and gaining weight.",
    h1="TDEE calculator",
    lede="Estimate the calories you burn in a day including activity — then see targets for losing, "
         "maintaining or gaining weight.",
    fields=[sel("units", "Units", [("us", "US (lb, ft/in)"), ("metric", "Metric (kg, cm)")], "us"),
            sel("sex", "Sex", [("male", "Male"), ("female", "Female")], "male"),
            num("age", "Age", 30, unit="years", mn=15, mx=100, step=1),
            num("weight_lb", "Weight", 180, unit="lb", mn=30, mx=1200, step="0.1", show=("units", "us")),
            num("height_ft", "Height — feet", 5, unit="ft", mn=1, mx=8, step=1, show=("units", "us")),
            num("height_in", "Height — inches", 10, unit="in", mn=0, mx=11.9, step=0.5, show=("units", "us")),
            num("weight_kg", "Weight", 80, unit="kg", mn=15, mx=500, step="0.1", show=("units", "metric")),
            num("height_cm", "Height", 178, unit="cm", mn=60, mx=260, step=0.5, show=("units", "metric")),
            sel("activity", "Activity level", ACTIVITY, "1.55")],
    outs=[("tdee", "Daily calories to maintain weight", "int"),
          ("cut", "Lose about 1 lb a week", "int"),
          ("bulk", "Lean gain (+300 kcal)", "int"),
          ("bmr", "Basal metabolic rate", "int")],
    js="""
var w = v.units==='metric' ? v.weight_kg : v.weight_lb*0.45359237;
var h = v.units==='metric' ? v.height_cm : (v.height_ft*12+v.height_in)*2.54;
var male = v.sex==='male';
var bmr = 10*w + 6.25*h - 5*v.age + (male?5:-161);
var tdee = bmr * Number(v.activity);
return {tdee:tdee, cut:tdee-500, bulk:tdee+300, bmr:bmr};
""",
    py=_tdee_py,
    how="""<p>TDEE is your total calorie burn for a day: BMR plus everything else — moving around,
exercise, digesting food and the small cost of staying upright. The usual approach is to multiply
BMR by an activity factor that ranges from 1.2 for a completely sedentary desk job to 1.9 for
athletes training twice a day. It is a rough multiplier, which is why the estimate can be off for
people whose real activity does not match a label.</p>
<p>The weight-change targets are based on the widely used approximation that 500 calories a day
below maintenance produces roughly 1 lb of loss a week, since a pound of fat stores about 3,500
calories. That rule works for about 8–12 weeks before metabolic adaptation, water shifts and
changes in movement slow it down. For sustainable loss, a 300–500 calorie deficit and resistance
training to preserve muscle is usually the better plan than an aggressive cut.</p>""",
    formula="""<p>TDEE = BMR × activity factor, where BMR comes from Mifflin-St Jeor:</p>
<div class="fml"><code>BMR  = 10·kg + 6.25·cm − 5·age + (5 men / −161 women)
TDEE = BMR × activity factor
deficit target  = TDEE − 500
surplus target  = TDEE + 300</code></div>
<p>Activity factors: 1.2 sedentary, 1.375 light, 1.55 moderate, 1.725 very active, 1.9 extremely
active.</p>""",
    example="With a BMR of {bmr} and the selected activity level, maintenance calories are {tdee} a "
            "day. A 500-calorie deficit gives {cut} for roughly 1 lb of loss a week, while a lean "
            "gaining phase targets {bulk}.",
    mistakes=[
        "<strong>Overestimating activity.</strong> Most office workers who exercise three times a "
        "week land in the light-to-moderate range, not very active. Start conservative.",
        "<strong>Cutting too hard.</strong> Very large deficits reduce adherence, encourage muscle "
        "loss and slow metabolic rate. 15–25% below TDEE is a more sustainable target.",
        "<strong>Eating back all exercise calories.</strong> Calorie burn from cardio is often "
        "overestimated by machines and watches, which double-counts activity already included in "
        "the TDEE factor."
    ],
    faq=[
        ("How accurate is a TDEE estimate?",
         "Usually within 10–15% for most people, but outliers exist. Track your weight and intake "
         "for 2–3 weeks and adjust the number based on the actual trend — that measurement beats any "
         "formula."),
        ("How many calories should I eat to lose weight?",
         "Start with 300–500 calories below TDEE. That produces roughly 0.5–1 lb of loss a week, "
         "which is the range most guidelines recommend for sustainable fat loss."),
        ("Should I eat back my exercise calories?",
         "If you chose a TDEE activity factor that already accounts for exercise, no. If you use a "
         "sedentary multiplier and add exercise on top, you can eat back part of the burn."),
    ],
    related=["bmr-calculator", "bmi-calculator", "body-fat-navy", "ideal-weight-calculator"],
    note="Estimates only. Calorie needs vary with body composition, medication and health conditions.",
)


# ---------------------------------------------------------------------------
# 4. Navy body fat
def _bf_py(v):
    male = v["sex"] == "male"
    if v["units"] == "metric":
        height = float(v["height_cm"]) / 2.54
        neck = float(v["neck_cm"]) / 2.54
        waist = float(v["waist_cm"]) / 2.54
        hip = float(v["hip_cm"]) / 2.54
    else:
        height = float(v["height_ft"]) * 12 + float(v["height_in"])
        neck = float(v["neck_in"])
        waist = float(v["waist_in"])
        hip = float(v["hip_in"])
    import math
    if male:
        bf = 86.010 * math.log10(max(1e-6, waist - neck)) - 70.041 * math.log10(max(1e-6, height)) + 36.76
    else:
        bf = (163.205 * math.log10(max(1e-6, waist + hip - neck))
              - 97.684 * math.log10(max(1e-6, height)) - 78.387)
    bf = max(0.0, min(75.0, bf))
    if male:
        cat = ("Essential fat" if bf < 6 else "Athletic" if bf < 14 else "Fitness" if bf < 18
               else "Average" if bf < 25 else "High")
    else:
        cat = ("Essential fat" if bf < 14 else "Athletic" if bf < 21 else "Fitness" if bf < 25
               else "Average" if bf < 32 else "High")
    return {"body_fat": bf, "category": cat, "fat_free": 100 - bf}


BODY_FAT = calc(
    slug="body-fat-navy", name="Navy Body Fat Calculator", cat="health",
    title="Body Fat Calculator (US Navy Method) — Tape Measure Estimate",
    desc="Estimate body fat percentage from height, neck, waist and hip measurements using the US "
         "Navy formula, with a category range. Supports inches and centimetres.",
    h1="Navy body fat calculator",
    lede="Estimate body-fat percentage from a tape measure using the US Navy formula — height, neck "
         "and waist, plus hip for women.",
    fields=[sel("units", "Units", [("us", "US (in)"), ("metric", "Metric (cm)")], "us"),
            sel("sex", "Sex", [("male", "Male"), ("female", "Female")], "male"),
            num("height_ft", "Height — feet", 5, unit="ft", mn=1, mx=8, step=1, show=("units", "us")),
            num("height_in", "Height — inches", 10, unit="in", mn=0, mx=11.9, step=0.5, show=("units", "us")),
            num("height_cm", "Height", 178, unit="cm", mn=60, mx=260, step=0.5, show=("units", "metric")),
            num("neck_in", "Neck circumference", 15, unit="in", mn=8, mx=30, step="0.1", show=("units", "us")),
            num("waist_in", "Waist circumference (at navel)", 36, unit="in", mn=15, mx=80, step="0.1", show=("units", "us")),
            num("neck_cm", "Neck circumference", 38, unit="cm", mn=20, mx=80, step="0.1", show=("units", "metric")),
            num("waist_cm", "Waist circumference (at navel)", 91, unit="cm", mn=40, mx=200, step="0.1", show=("units", "metric")),
            num("hip_in", "Hip circumference", 40, unit="in", mn=15, mx=80, step="0.1", show=("sex", "female")),
            num("hip_cm", "Hip circumference", 102, unit="cm", mn=40, mx=200, step="0.1", show=("sex", "female"))],
    outs=[("body_fat", "Estimated body fat", "pct1"), ("category", "Category", "text"),
          ("fat_free", "Lean mass percentage", "pct1")],
    js="""
var metric = v.units === 'metric';
var male = v.sex === 'male';
var h = metric ? v.height_cm/2.54 : v.height_ft*12+v.height_in;
var neck = metric ? v.neck_cm/2.54 : v.neck_in;
var waist = metric ? v.waist_cm/2.54 : v.waist_in;
var hip = metric ? v.hip_cm/2.54 : v.hip_in;
function lg(x){return Math.log(x)/Math.LN10;}
var bf;
if (male) bf = 86.010*lg(Math.max(1e-6,waist-neck)) - 70.041*lg(Math.max(1e-6,h)) + 36.76;
else bf = 163.205*lg(Math.max(1e-6,waist+hip-neck)) - 97.684*lg(Math.max(1e-6,h)) - 78.387;
bf = Math.max(0, Math.min(75, bf));
var cat;
if (male) cat = bf<6?'Essential fat':bf<14?'Athletic':bf<18?'Fitness':bf<25?'Average':'High';
else cat = bf<14?'Essential fat':bf<21?'Athletic':bf<25?'Fitness':bf<32?'Average':'High';
return {body_fat:bf, category:cat, fat_free:100-bf};
""",
    py=_bf_py,
    how="""<p>The US Navy method estimates body fat from circumference measurements. It was developed
as a practical field alternative to hydrostatic weighing for the military, where tape measures are
available but laboratory equipment is not. For men the formula uses neck and waist; for women it
adds hip circumference. The idea is that fat distribution changes the shape of the body, and those
tape measurements capture the change well enough to estimate fat percentage.</p>
<p>Accuracy is typically within 3–4 percentage points for a careful measurement — close enough to
track progress, not precise enough to compare with a DEXA scan. Measure at the same time of day,
with the tape snug but not compressing the skin, after breathing out normally. Waist is measured at
the navel for this formula, not at the narrowest point. If the tape slips by half an inch the
estimate can move a full percentage point, so consistency matters more than absolute precision.</p>""",
    formula="""<p>US Navy circumference formulas (measurements in inches):</p>
<div class="fml"><code>men:   %BF = 86.010·log10(waist − neck) − 70.041·log10(height) + 36.76
women: %BF = 163.205·log10(waist + hip − neck) − 97.684·log10(height) − 78.387</code></div>
<p>The result is expressed as a percentage; lean mass percentage is 100 minus body-fat percentage.
For metric measurements, convert to inches first (cm ÷ 2.54).</p>""",
    example="For the default measurements the Navy formula estimates {body_fat} body fat, which falls "
            "in the {category} range, and {fat_free} lean mass. Change any measurement by an inch "
            "and watch how the estimate moves — that is why consistent measuring matters.",
    mistakes=[
        "<strong>Measuring at the wrong point.</strong> A relaxed waist at the navel is not the "
        "narrowest waist. Check the standard site for the method you are using.",
        "<strong>Pulling the tape tight.</strong> Compressing the skin underestimates circumference "
        "and underestimates body fat. Snug, level and not compressing.",
        "<strong>Comparing men and women on one scale.</strong> Essential fat is roughly 2–5% for "
        "men and 10–13% for women, so the categories are sex-specific."
    ],
    faq=[
        ("How accurate is the Navy body fat formula?",
         "Typically within 3–4 percentage points of a DEXA scan when measurements are taken "
         "carefully. It is best used to track direction of change rather than as an exact number."),
        ("Where exactly should I measure my waist?",
         "For the US Navy method, men measure the waist horizontally at the navel. Women measure the "
         "waist at the narrowest point and the hips at the widest point."),
        ("What is a healthy body fat percentage?",
         "Roughly 10–20% for men and 18–28% for women is often described as healthy/fitness range, "
         "but age, genetics and athletic goals all shift the target. Very low body fat can harm "
         "hormones and health."),
    ],
    related=["bmi-calculator", "bmr-calculator", "tdee-calculator", "ideal-weight-calculator"],
    note="Tape-measure estimate from the US Navy formula; not a substitute for a DEXA scan.",
)


# ---------------------------------------------------------------------------
# 5. ideal weight
def _ideal_py(v):
    h_m = _cm(v) / 100
    target = 22 * h_m * h_m
    lo, hi = 18.5 * h_m * h_m, 24.9 * h_m * h_m
    if v["units"] == "metric":
        return {"target": fnum(target, 1) + " kg", "low": fnum(lo, 1) + " kg",
                "high": fnum(hi, 1) + " kg"}
    conv = 2.2046226218
    return {"target": fnum(target * conv, 1) + " lb", "low": fnum(lo * conv, 1) + " lb",
            "high": fnum(hi * conv, 1) + " lb"}


IDEAL = calc(
    slug="ideal-weight-calculator", name="Ideal Weight Calculator", cat="health",
    title="Ideal Weight Calculator — Healthy Weight Range for Your Height",
    desc="Find a healthy weight range for your height from BMI thresholds, plus a BMI 22 target "
         "weight. Works in pounds or kilograms.",
    h1="Ideal weight calculator",
    lede="Find the healthy weight range for your height from BMI thresholds, plus the weight that "
         "corresponds to a BMI of 22 — the middle of the healthy band.",
    fields=[sel("units", "Units", [("us", "US (lb, ft/in)"), ("metric", "Metric (kg, cm)")], "us"),
            num("height_ft", "Height — feet", 5, unit="ft", mn=1, mx=8, step=1, show=("units", "us")),
            num("height_in", "Height — inches", 10, unit="in", mn=0, mx=11.9, step=0.5, show=("units", "us")),
            num("height_cm", "Height", 178, unit="cm", mn=60, mx=260, step=0.5, show=("units", "metric"))],
    outs=[("target", "Target weight (BMI 22)", "text"),
          ("low", "Healthy range — lower end (BMI 18.5)", "text"),
          ("high", "Healthy range — upper end (BMI 24.9)", "text")],
    js="""
var metric = v.units === 'metric';
var h_m = metric ? v.height_cm/100 : (v.height_ft*12+v.height_in)*0.0254;
function f1(x){return (Math.floor(x*10+0.5)/10).toFixed(1);}
var target = 22*h_m*h_m, lo=18.5*h_m*h_m, hi=24.9*h_m*h_m;
if (metric) return {target:f1(target)+' kg', low:f1(lo)+' kg', high:f1(hi)+' kg'};
var c = 2.2046226218;
return {target:f1(target*c)+' lb', low:f1(lo*c)+' lb', high:f1(hi*c)+' lb'};
""",
    py=_ideal_py,
    how="""<p>“Ideal weight” has no single scientific definition. The practical answer is a range: for
most adults, a BMI between 18.5 and 24.9 corresponds to a healthy weight for a given height, and the
risk curve is flat-to-lowest in the middle of that band. This calculator shows both ends of the
range and the weight at BMI 22 as a target point.</p>
<p>Older formulas — Robinson, Devine, Hamwi, Miller — were designed for prescribing drug doses and
produce single numbers that can look oddly precise. They assume a frame and body composition that
may not match yours. A range based on BMI plus waist circumference and body-fat percentage is a
more honest guide. Athletes should expect to sit above the BMI range with low body fat, and people
with low muscle mass can be inside the range while carrying too much fat.</p>""",
    formula="""<p>Healthy weight range = 18.5 × height² to 24.9 × height² (metres, kilograms).
Target = 22 × height², near the middle of the healthy band. Convert with 1 kg = 2.205 lb,
1 in = 2.54 cm.</p>
<div class="fml"><code>low    = 18.5 · height_m²
target = 22.0 · height_m²
high   = 24.9 · height_m²</code></div>
<p>For example, at 1.78 m the healthy range is about 59–79 kg (129–174 lb) and the BMI 22 target is
about 69.7 kg.</p>""",
    example="At {height_ft} ft {height_in} in ({height_cm} cm in metric mode), a BMI of 22 corresponds "
            "to about {target}. The healthy range for that height runs from {low} to {high}.",
    mistakes=[
        "<strong>Chasing the lowest number in the range.</strong> Being at the bottom of the healthy "
        "BMI band is not automatically better; muscle mass and body composition matter more.",
        "<strong>Comparing with outdated ideal-weight formulas.</strong> Robinson, Devine and Hamwi "
        "were built for dosing, not wellness, and ignore body composition.",
        "<strong>Ignoring waist circumference.</strong> Two people at the same weight can have very "
        "different risk depending on where the fat is stored."
    ],
    faq=[
        ("What is my ideal weight?",
         "Use the healthy BMI range for your height as the primary guide, then adjust with body-fat "
         "percentage and waist circumference. There is no single exact ideal number."),
        ("Should athletes use BMI?",
         "BMI can mislabel muscular athletes as overweight. For athletes, body-fat percentage and "
         "performance metrics are far more useful than weight for height."),
        ("Does ideal weight change with age?",
         "The healthy BMI band is the same for all adults, but some research suggests slightly "
         "higher body weight is protective in older age. Discuss individual targets with a "
         "clinician rather than relying on a single formula."),
    ],
    related=["bmi-calculator", "body-fat-navy", "bmr-calculator", "tdee-calculator"],
    note="BMI-based reference range, not a personal medical target.",
)


# ---------------------------------------------------------------------------
# 6. pregnancy due date
def _due_py(v):
    lmp = v["lmp"]
    cycle = int(round(float(v["cycle"])))
    due = iso_add(lmp, 280 + (cycle - 28))
    conception = iso_add(lmp, cycle - 14)
    first_tri = iso_add(lmp, 97)
    return {"due": due, "conception": conception, "first_tri": first_tri}


DUE_DATE = calc(
    slug="pregnancy-due-date", name="Pregnancy Due Date Calculator", cat="health",
    title="Pregnancy Due Date Calculator — Naegele's Rule",
    desc="Estimate a pregnancy due date from the first day of your last period and cycle length, "
         "using Naegele's rule, plus the estimated conception date.",
    h1="Pregnancy due date calculator",
    lede="Estimate the due date from the first day of your last menstrual period and your usual "
         "cycle length, plus the likely conception date and the end of the first trimester.",
    fields=[dat("lmp", "First day of last period", "2026-08-13", hint="The first day of bleeding, not the last."),
            num("cycle", "Usual cycle length", 28, unit="days", mn=20, mx=45, step=1,
                hint="28 days is average; the due date shifts by the difference.")],
    outs=[("due", "Estimated due date", "date"),
          ("conception", "Estimated conception date", "date"),
          ("first_tri", "End of first trimester", "date")],
    js="""
var cycle = Math.round(v.cycle);
return {due: addDays(v.lmp, 280 + (cycle-28)),
        conception: addDays(v.lmp, cycle-14),
        first_tri: addDays(v.lmp, 97)};
""",
    py=_due_py,
    how="""<p>A pregnancy due date is estimated as 40 weeks — 280 days — from the first day of the last
menstrual period. This is Naegele's rule, and it assumes a regular 28-day cycle with ovulation on
day 14. If your cycle is longer or shorter, the estimated ovulation day moves, so this calculator
adjusts the due date by the difference between your cycle length and 28 days.</p>
<p>Because the estimate depends on ovulation timing, only about 4% of babies arrive exactly on the
due date; most births happen within two weeks either side. An early ultrasound (dating scan) is
more accurate than LMP dating, especially for irregular cycles, and clinicians usually revise the
due date based on it. Treat the result as a planning window rather than an appointment: arrange
leave and appointments around the range, not the single day.</p>""",
    formula="""<p>Naegele's rule: due date = first day of last period + 280 days. Corrected for cycle
length <em>L</em>:</p>
<div class="fml"><code>due date       = LMP + 280 + (L − 28) days
conception est. = LMP + (L − 14) days
first trimester ends = LMP + 97 days (13 weeks 6 days)</code></div>
<p>The 280-day figure corresponds to 40 weeks from LMP, or 38 weeks from conception.</p>""",
    example="With a last period starting {lmp} and a {cycle}-day cycle, the estimated due date is "
            "{due}. Estimated conception is {conception}, and the first trimester ends around "
            "{first_tri}.",
    mistakes=[
        "<strong>Using the last day of the period.</strong> The calculation starts from the first "
        "day of bleeding; using the end date shifts the due date by several days.",
        "<strong>Ignoring cycle length.</strong> A 35-day cycle moves ovulation later and the due "
        "date about a week later than the unadjusted rule.",
        "<strong>Treating the due date as exact.</strong> Only a small share of births happen on "
        "the estimated date; a dating ultrasound is more accurate."
    ],
    faq=[
        ("How accurate is a due date calculated from LMP?",
         "Reasonably accurate for regular cycles, but an early dating ultrasound is more precise. "
         "Most clinicians adjust the date if the scan differs from the LMP estimate."),
        ("How is the due date calculated?",
         "Add 280 days (40 weeks) to the first day of your last period. If your cycle is not 28 "
         "days, shift the result by the difference between your cycle length and 28."),
        ("What if my cycles are irregular?",
         "LMP dating becomes unreliable, and an early ultrasound or known ovulation date should be "
         "used instead. Ask your clinician to set the date from the scan."),
    ],
    related=["ovulation-calculator", "age-calculator", "date-difference", "bmi-calculator"],
    note="Estimate only. Dating ultrasound and clinical assessment take precedence.",
)


# ---------------------------------------------------------------------------
# 7. ovulation
def _ovu_py(v):
    lmp = v["lmp"]
    cycle = int(round(float(v["cycle"])))
    ovu = iso_add(lmp, cycle - 14)
    return {"ovulation": ovu, "fertile_start": iso_add(ovu, -5), "fertile_end": iso_add(ovu, 1),
            "next_period": iso_add(lmp, cycle)}


OVULATION = calc(
    slug="ovulation-calculator", name="Ovulation Calculator", cat="health",
    title="Ovulation Calculator — Fertile Window and Next Period",
    desc="Estimate ovulation day, the fertile window and the next period from your last period date "
         "and typical cycle length.",
    h1="Ovulation calculator",
    lede="Estimate when ovulation is likely and which days make up the fertile window, from the first "
         "day of your last period and your usual cycle length.",
    fields=[dat("lmp", "First day of last period", "2026-10-12"),
            num("cycle", "Usual cycle length", 28, unit="days", mn=20, mx=45, step=1)],
    outs=[("ovulation", "Estimated ovulation date", "date"),
          ("fertile_start", "Fertile window starts", "date"),
          ("fertile_end", "Fertile window ends", "date"),
          ("next_period", "Next period expected", "date")],
    js="""
var cycle = Math.round(v.cycle);
var ovu = addDays(v.lmp, cycle-14);
return {ovulation:ovu, fertile_start:addDays(ovu,-5), fertile_end:addDays(ovu,1),
        next_period:addDays(v.lmp, cycle)};
""",
    py=_ovu_py,
    how="""<p>The ovulation calculator estimates the day an egg is released using the luteal phase:
ovulation usually happens about 14 days before the next period, not 14 days after the last one. So
for a 28-day cycle, ovulation is around day 14; for a 30-day cycle, around day 16. Sperm can
survive up to about five days in the reproductive tract, and the egg is viable for roughly a day,
which is why the fertile window is usually given as the five days before ovulation plus the day
after.</p>
<p>This is a calendar estimate, not a measurement. Cycle length varies, stress and illness can delay
ovulation, and the luteal phase is not always exactly 14 days. If you are trying to conceive, adding
ovulation predictor kits, basal body temperature tracking or cervical mucus observations will give
you much better timing. If you are trying to avoid pregnancy, do not use calendar methods alone —
they have a high typical-use failure rate.</p>""",
    formula="""<p>With cycle length <em>L</em> days:</p>
<div class="fml"><code>ovulation      = LMP + (L − 14) days
fertile window = ovulation − 5 days  …  ovulation + 1 day
next period    = LMP + L days</code></div>
<p>The fertile window reflects sperm survival (about five days) and egg viability (about 24 hours).
The calculation assumes a regular cycle and a 14-day luteal phase.</p>""",
    example="For a last period starting {lmp} and a {cycle}-day cycle, ovulation is estimated around "
            "{ovulation}, with the fertile window running from {fertile_start} to {fertile_end}. The "
            "next period would be expected around {next_period}.",
    mistakes=[
        "<strong>Assuming ovulation is always day 14.</strong> That is only true for a 28-day cycle; "
        "the timing moves with cycle length.",
        "<strong>Using it as contraception.</strong> Calendar estimates fail often because ovulation "
        "shifts between cycles. Use a method designed for contraception.",
        "<strong>Ignoring cycle variability.</strong> If your cycles vary by more than a few days, "
        "the fertile window estimate is too narrow to rely on.",
    ],
    faq=[
        ("How accurate is an ovulation calculator?",
         "It is a reasonable estimate for people with regular cycles, but it cannot confirm "
         "ovulation. Ovulation predictor kits detect the hormonal surge directly and are more "
         "accurate for timing."),
        ("When is the fertile window?",
         "Roughly the five days before ovulation plus the day after, because sperm survive several "
         "days while the egg lives for about a day. The most fertile days are the two before "
         "ovulation."),
        ("Can I get pregnant right after my period?",
         "It is possible, especially with short cycles and long periods, because sperm can survive "
         "several days. The calendar estimate here shows when the fertile window is likely for your "
         "cycle length."),
    ],
    related=["pregnancy-due-date", "age-calculator", "date-difference", "bmi-calculator"],
    note="Calendar estimate only; not a contraceptive method. Consult a clinician for medical advice.",
)


CALCS = [BMI, BMR, TDEE, BODY_FAT, IDEAL, DUE_DATE, OVULATION]
