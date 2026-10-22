#!/usr/bin/env python3
"""Conversions and practical quantity calculators: length, weight, temperature,
speed, area, volume, fuel cost, electricity cost, paint, tiles."""
import json
import math

from core import calc, num, sel, fnum, r0, table_html

MONEY = "USD"

JS_F3 = r"""
function f(x){var n=Math.floor(x*1000+0.5)/1000,neg=n<0;if(neg)n=-n;
  var s=n.toFixed(3).split('.');
  return (neg?'-':'')+s[0].replace(/\B(?=(\d{3})+(?!\d))/g,',')+'.'+s[1];}
"""


def _converter(*, slug, name, cat, title, desc, h1, lede, units, default_value, default_from,
               out_keys, how, formula, example, mistakes, faq, related, note):
    factors = {k: f for k, _l, f, _s in units}
    suffix = {k: s for k, _l, _f, s in units}
    label = {k: l for k, l, _f, _s in units}
    outs = [(k, f"{label[k]} ({suffix[k]})", "text") for k in out_keys]
    pairs = ",".join(
        f"{k}: f(base/factors['{k}'])+' {suffix[k]}'" for k in out_keys)
    js = (JS_F3 + "\nvar factors=" + json.dumps(factors) + ";\n"
          "var base=v.value*factors[v.from];\nreturn {" + pairs + "};")

    def pyfn(v, factors=factors, out_keys=tuple(out_keys), suffix=suffix):
        base = float(v["value"]) * factors[v["from"]]
        return {k: fnum(base / factors[k], 3) + " " + suffix[k] for k in out_keys}

    return calc(
        slug=slug, name=name, cat=cat, title=title, desc=desc, h1=h1, lede=lede,
        fields=[num("value", "Value to convert", default_value, unit="", mn=0, mx=10**12, step="any"),
                sel("from", "Convert from", [(k, label[k]) for k, _l, _f, _s in units], default_from)],
        outs=outs, js=js, py=pyfn,
        how=how, formula=formula, example=example, mistakes=mistakes, faq=faq,
        related=related, note=note)


# ---------------------------------------------------------------------------
LENGTH = _converter(
    slug="length-converter", name="Length Converter", cat="conversions",
    title="Length Converter — Metres, Feet, Miles, Kilometres, Inches",
    desc="Convert length and distance between metres, kilometres, miles, yards, feet, inches, "
         "centimetres and millimetres with exact conversion factors.",
    h1="Length converter",
    lede="Convert a length between metric and imperial units — metres, feet, miles, kilometres, "
         "inches, centimetres, yards and millimetres — all at once.",
    units=[("m", "Metres", 1.0, "m"), ("km", "Kilometres", 1000.0, "km"),
           ("cm", "Centimetres", 0.01, "cm"), ("mm", "Millimetres", 0.001, "mm"),
           ("mi", "Miles", 1609.344, "mi"), ("yd", "Yards", 0.9144, "yd"),
           ("ft", "Feet", 0.3048, "ft"), ("in", "Inches", 0.0254, "in")],
    default_value=100, default_from="m",
    out_keys=["m", "ft", "mi", "km", "in", "cm"],
    how="""<p>Length conversions rely on a small set of exact definitions. The metre is the SI base
unit; the inch is defined as exactly 25.4 millimetres, which fixes the foot (12 inches = 304.8 mm),
the yard (0.9144 m) and the mile (1,609.344 m). Kilometres are 1,000 metres and centimetres are
one hundredth of a metre. Because these are definitions rather than roundings, conversions between
metric and imperial lengths are exact to the number of decimals displayed.</p>
<p>The most common source of error is mixing up the direction of the conversion: multiplying by
3.28 when you meant to divide (for example converting feet to metres). The calculator computes a
base value in metres first, then converts that base to every other unit, so one entry produces the
full set of equivalents at once. Navigation, DIY and travel planning are the usual use cases; for
surveying and engineering, keep more decimal places than the three shown here.</p>""",
    formula="""<p>Convert to metres, then out of metres:</p>
<div class="fml"><code>metres = value × factor(from)
result = metres / factor(to)

1 in  = 0.0254 m      1 ft = 0.3048 m
1 yd  = 0.9144 m      1 mi = 1,609.344 m
1 km  = 1,000 m       1 cm = 0.01 m</code></div>
<p>So 100 m = 328.084 ft = 0.062 mi = 0.1 km = 3,937.008 in = 10,000 cm.</p>""",
    example="Converting {value} {from} gives {ft} in feet, {mi} in miles and {km} in kilometres. "
            "The same distance is also {in} tall and {cm} wide when split into smaller units.",
    mistakes=[
        "<strong>Multiplying instead of dividing.</strong> Feet to metres divides by 3.281; metres "
        "to feet multiplies. Check that a metre is longer than a foot than a centimetre.",
        "<strong>Mixing inches and centimetres.</strong> Screen sizes and tools often mix units; "
        "convert everything to one unit before adding or comparing.",
        "<strong>Rounding mid-calculation.</strong> Round only at the end. Rounding each step can "
        "move a distance by several centimetres.",
    ],
    faq=[
        ("How many feet in a metre?",
         "One metre is 3.28084 feet. One foot is 0.3048 metres, so 100 m is 328.084 ft."),
        ("How many kilometres in a mile?",
         "One mile is 1.609344 kilometres, and one kilometre is 0.621371 miles. A 5 km run is about "
         "3.11 miles; a 10K is 6.21 miles."),
        ("How many inches in a centimetre?",
         "One centimetre is 0.393701 inches, because the inch is exactly 2.54 cm. To go the other "
         "way, multiply inches by 2.54."),
    ],
    related=["weight-converter", "area-converter", "volume-converter", "speed-converter"],
    note="Exact conversion factors. Results rounded to three decimals.",
)


WEIGHT = _converter(
    slug="weight-converter", name="Weight Converter", cat="conversions",
    title="Weight Converter — Kilograms, Pounds, Ounces, Stones",
    desc="Convert weight between kilograms, pounds, ounces, grams, milligrams and stones using "
         "exact conversion factors.",
    h1="Weight converter",
    lede="Convert between kilograms, pounds, ounces, grams and stones — useful for body weight, "
         "shipping and recipes.",
    units=[("kg", "Kilograms", 1.0, "kg"), ("g", "Grams", 0.001, "g"),
           ("mg", "Milligrams", 0.000001, "mg"), ("lb", "Pounds", 0.45359237, "lb"),
           ("oz", "Ounces", 0.028349523125, "oz"), ("st", "Stones", 6.35029318, "st")],
    default_value=70, default_from="kg",
    out_keys=["kg", "lb", "st", "oz", "g"],
    how="""<p>Weight conversions look simple but the units are not equally spaced: there are 16
ounces in a pound, 14 pounds in a stone, 1,000 grams in a kilogram, and a kilogram is 2.20462
pounds. The calculator converts everything to kilograms first, then out to each unit, which avoids
cascading rounding errors.</p>
<p>Be aware of one terminology trap: in everyday use “weight” means mass, and the conversion factors
above are for mass. Strictly, the pound-force is a unit of force measured in poundals, but scales
report pounds as mass, so the everyday conversion is fine. Stones are still common in the UK and
Ireland for body weight; the US and most of the world use pounds or kilograms. For anything
regulated — medication doses, aircraft loading, freight — use the exact figure from the governing
standard rather than a rounded conversion.</p>""",
    formula="""<p>Convert to kilograms, then to the target unit:</p>
<div class="fml"><code>kg = value × factor(from)
result = kg / factor(to)

1 lb  = 0.45359237 kg
1 oz  = 0.028349523125 kg
1 st  = 6.35029318 kg  (14 lb)
1 g   = 0.001 kg</code></div>
<p>So 70 kg = 154.324 lb = 11.023 st = 2,469.178 oz = 70,000 g.</p>""",
    example="Converting {value} {from} gives {lb} in pounds and {st} in stones — {oz} if you need "
            "ounces, or {g} on a metric kitchen scale.",
    mistakes=[
        "<strong>Mixing pounds and ounces.</strong> A weight of 10 lb 8 oz is 10.5 lb, not 10.8 lb. "
        "Convert the ounces first.",
        "<strong>Using 2.2 instead of 2.20462.</strong> The shortcut is fine for a rough check but "
        "drifts by about 0.2% — noticeable over large shipments.",
        "<strong>Confusing mass and force.</strong> Strict physics uses the pound-force for force "
        "and the pound for mass; household scales measure mass."
    ],
    faq=[
        ("How many pounds in a kilogram?",
         "One kilogram is 2.20462 pounds. To go the other way, one pound is 0.453592 kilograms."),
        ("How many ounces in a pound?",
         "Sixteen ounces make one pound. One ounce is 28.3495 grams."),
        ("How many stones is 70 kg?",
         "70 kg is 11.02 stone, or 154.32 pounds. One stone is 6.35029 kg."),
    ],
    related=["length-converter", "temperature-converter", "volume-converter", "bmi-calculator"],
    note="Exact mass conversion factors; results rounded to three decimals.",
)


# ---------------------------------------------------------------------------
def _temp_py(v):
    val = float(v["value"])
    unit = v["from"]
    c = val if unit == "c" else (val - 32) * 5 / 9 if unit == "f" else val - 273.15
    return {"c": fnum(c, 2) + " °C", "f": fnum(c * 9 / 5 + 32, 2) + " °F",
            "k": fnum(c + 273.15, 2) + " K"}


TEMPERATURE = calc(
    slug="temperature-converter", name="Temperature Converter", cat="conversions",
    title="Temperature Converter — Celsius, Fahrenheit and Kelvin",
    desc="Convert between Celsius, Fahrenheit and Kelvin instantly, with the formulas for each "
         "direction and a worked example.",
    h1="Temperature converter",
    lede="Convert a temperature between Celsius, Fahrenheit and Kelvin — useful for weather, cooking, "
         "science and travel.",
    fields=[num("value", "Temperature", 100, unit="", mn=-500, mx=10000, step="any"),
            sel("from", "Convert from",
                [("c", "Celsius (°C)"), ("f", "Fahrenheit (°F)"), ("k", "Kelvin (K)")], "c")],
    outs=[("c", "Celsius", "text"), ("f", "Fahrenheit", "text"), ("k", "Kelvin", "text")],
    js="""
function f2(x){var n=Math.floor(x*100+0.5)/100,neg=n<0;if(neg)n=-n;
  var s=n.toFixed(2).split('.');
  return (neg?'-':'')+s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g,',')+'.'+s[1];}
var val=v.value, u=v.from;
var c = u==='c' ? val : (u==='f' ? (val-32)*5/9 : val-273.15);
return {c:f2(c)+' \\u00b0C', f:f2(c*9/5+32)+' \\u00b0F', k:f2(c+273.15)+' K'};
""",
    py=_temp_py,
    how="""<p>Celsius and Fahrenheit are both interval scales, but they start at different points and
use different step sizes. Water freezes at 0 °C or 32 °F and boils at 100 °C or 212 °F, so 100
Celsius degrees span 180 Fahrenheit degrees — a ratio of 9/5. Kelvin uses the same step size as
Celsius but starts at absolute zero, which is −273.15 °C, so a Kelvin temperature is simply
Celsius plus 273.15.</p>
<p>Because of the offset, you cannot convert a temperature by scaling alone: the formula subtracts
or adds the offset as well. A handy mental check is the crossover — −40 °C equals −40 °F — and that
a normal body temperature of 37 °C is 98.6 °F. The calculator uses exact definitions (the Kelvin is
defined by the Boltzmann constant; the degree sizes are exact multiples), so displayed values are
correct to two decimals.</p>""",
    formula="""<div class="fml"><code>°F = °C × 9/5 + 32
°C = (°F − 32) × 5/9
K  = °C + 273.15
°C = K − 273.15</code></div>
<p>Always convert to Celsius (or Kelvin) first, then to the target unit. Absolute zero is 0 K,
−273.15 °C and −459.67 °F.</p>""",
    example="The default input of {value} {from} is {c}, which is {f} and {k}.",
    mistakes=[
        "<strong>Scaling without the offset.</strong> Doubling Celsius does not double Fahrenheit. "
        "The 32° offset must be applied.",
        "<strong>Treating Kelvin as degrees.</strong> Kelvin is written without the degree symbol: "
        "300 K, not 300 °K.",
        "<strong>Rounding before converting.</strong> Convert first, then round. Rounding 98.6 °F to "
        "99 °F before converting shifts the Celsius result noticeably."
    ],
    faq=[
        ("How do I convert Celsius to Fahrenheit?",
         "Multiply by 9, divide by 5, then add 32. For example, 20 °C × 9/5 + 32 = 68 °F."),
        ("What is 100 °F in Celsius?",
         "100 °F is 37.78 °C, using (100 − 32) × 5/9. Normal body temperature is about 37 °C or "
         "98.6 °F."),
        ("Why is Kelvin not written in degrees?",
         "Kelvin is an absolute thermodynamic scale, so its unit is simply kelvin (K), not degrees "
         "kelvin. Its step size matches the Celsius degree."),
    ],
    related=["length-converter", "weight-converter", "volume-converter", "speed-converter"],
    note="Exact standard conversion formulas; results rounded to two decimals.",
)


SPEED = _converter(
    slug="speed-converter", name="Speed Converter", cat="conversions",
    title="Speed Converter — mph, km/h, m/s, Knots",
    desc="Convert speed between miles per hour, kilometres per hour, metres per second, knots and "
         "feet per second.",
    h1="Speed converter",
    lede="Convert between mph, km/h, m/s, knots and ft/s — for driving abroad, running, sailing and "
         "physics problems.",
    units=[("ms", "Metres per second", 1.0, "m/s"), ("kmh", "Kilometres per hour", 0.2777777777777778, "km/h"),
           ("mph", "Miles per hour", 0.44704, "mph"), ("knot", "Knots", 0.5144444444444445, "kn"),
           ("fts", "Feet per second", 0.3048, "ft/s")],
    default_value=100, default_from="kmh",
    out_keys=["kmh", "mph", "ms", "knot", "fts"],
    how="""<p>Speed is distance divided by time, so unit conversions multiply or divide twice: once for
the distance unit and once for the time unit. A kilometre per hour is 1,000 metres per 3,600
seconds, which is 0.2778 m/s — the factor used here. A mile per hour is exactly 0.44704 m/s, and a
knot is exactly 1,852 metres per hour, or 0.5144 m/s.</p>
<p>Knots are used in aviation and marine navigation because they relate directly to degrees of
latitude: one nautical mile is one minute of latitude. Running pace is often given in minutes per
kilometre or per mile, which is a reciprocal relationship — a faster speed means a smaller pace
number, so pace conversions cannot be done by simple multiplication. This tool converts speed
only; for pace, divide 60 by the speed value in the same unit system.</p>""",
    formula="""<p>Convert to metres per second, then to the target unit:</p>
<div class="fml"><code>m/s  = value × factor(from)
result = m/s / factor(to)

1 km/h = 0.27778 m/s    1 mph = 0.44704 m/s
1 kn   = 0.51444 m/s    1 ft/s = 0.3048 m/s</code></div>
<p>So 100 km/h = 62.137 mph = 27.778 m/s = 53.996 knots = 91.134 ft/s.</p>""",
    example="Converting {value} {from} gives {mph} in miles per hour, {ms} in metres per second and "
            "{knot} in knots.",
    mistakes=[
        "<strong>Ignoring the time unit.</strong> Distance conversions alone are not enough: mph to "
        "km/h multiplies by 1.609, because the hour cancels out.",
        "<strong>Confusing speed and pace.</strong> Running pace is minutes per unit, the reciprocal "
        "of speed. Converting pace needs 60 ÷ speed, not a unit factor.",
        "<strong>Rounding speed for navigation.</strong> In aviation and marine work, small speed "
        "errors become large position errors; keep enough decimals."
    ],
    faq=[
        ("How fast is 100 km/h in mph?",
         "100 km/h is 62.14 mph. Multiply km/h by 0.621371 to get mph, or mph by 1.609344 to get "
         "km/h."),
        ("What is a knot in mph?",
         "One knot is 1.15078 mph, or 0.51444 m/s. Knots are nautical miles per hour."),
        ("How do I convert running pace to speed?",
         "Divide 60 by the pace in minutes per unit. A 5:00 min/km pace is 12 km/h; a 6:00 pace is "
         "10 km/h."),
    ],
    related=["length-converter", "temperature-converter", "fuel-cost-mpg", "area-converter"],
    note="Exact conversion factors; results rounded to three decimals.",
)


AREA = _converter(
    slug="area-converter", name="Area Converter", cat="conversions",
    title="Area Converter — Square Metres, Square Feet, Acres, Hectares",
    desc="Convert area between square metres, square feet, square yards, acres, hectares, square "
         "kilometres and square miles.",
    h1="Area converter",
    lede="Convert an area between square metres, square feet, square yards, acres, hectares, square "
         "kilometres and square miles.",
    units=[("m2", "Square metres", 1.0, "m²"), ("ft2", "Square feet", 0.09290304, "ft²"),
           ("yd2", "Square yards", 0.83612736, "yd²"), ("acre", "Acres", 4046.8564224, "ac"),
           ("ha", "Hectares", 10000.0, "ha"), ("km2", "Square kilometres", 1000000.0, "km²"),
           ("mi2", "Square miles", 2589988.110336, "mi²")],
    default_value=100, default_from="m2",
    out_keys=["m2", "ft2", "yd2", "acre", "ha", "km2"],
    how="""<p>Area units are squared length units, so conversion factors are the square of the
corresponding length factors: one foot is 0.3048 m, so one square foot is 0.3048² = 0.09290304 m².
Three land-area units matter in practice: the acre (4,046.856 m², originally the area a team of
oxen could plough in a day), the hectare (10,000 m²) and the square mile (2.59 km²).</p>
<p>Real estate is where unit confusion costs money. Floor area in the US is quoted in square feet;
in most of Europe and Asia in square metres; UK property listings often show both. Land is quoted
in acres (US, UK) or hectares (most metric countries), and larger plots in square feet or
hectares depending on the market. Always confirm whether a floor-area figure is gross internal
area, net internal area or gross external area — converting the units does not fix a different
measurement convention.</p>""",
    formula="""<p>Convert to square metres, then to the target unit:</p>
<div class="fml"><code>m² = value × factor(from)
result = m² / factor(to)

1 ft²   = 0.09290304 m²
1 yd²   = 0.83612736 m²
1 acre  = 4,046.8564224 m²
1 ha    = 10,000 m²
1 km²   = 1,000,000 m²
1 mi²   = 2,589,988.11 m²</code></div>
<p>So 100 m² = 1,076.391 ft² = 119.599 yd² = 0.0247 acres = 0.01 ha.</p>""",
    example="Converting {value} {from} gives {ft2} in square feet, {yd2} in square yards and {acre} "
            "in acres — or {ha} hectares.",
    mistakes=[
        "<strong>Squaring the linear factor incorrectly.</strong> A metre is 3.281 feet, but a "
        "square metre is 10.764 square feet — the factor is squared.",
        "<strong>Confusing acres and hectares.</strong> One hectare is about 2.471 acres. Mixing "
        "them changes the size of a plot by a factor of 2.5.",
        "<strong>Assuming floor-area conventions are the same.</strong> US square footage is usually "
        "gross living area; many other markets quote net internal area, which is smaller."
    ],
    faq=[
        ("How many square feet in a square metre?",
         "One square metre is 10.764 square feet. To convert, multiply square metres by 10.764 or "
         "divide square feet by 10.764."),
        ("How many square feet in an acre?",
         "One acre is 43,560 square feet, or 4,046.86 square metres. A hectare is 10,000 m², about "
         "2.471 acres."),
        ("How do I convert a room size to square metres?",
         "Measure length and width in metres and multiply them. For feet, multiply the foot "
         "measurements and divide by 10.764 to get square metres."),
    ],
    related=["length-converter", "volume-converter", "tile-quantity", "paint-quantity"],
    note="Exact conversion factors; results rounded to three decimals.",
)


VOLUME = _converter(
    slug="volume-converter", name="Volume Converter", cat="conversions",
    title="Volume Converter — Litres, Gallons, Cups, Fluid Ounces",
    desc="Convert volume between litres, millilitres, cubic metres, US gallons, quarts, cups and "
         "fluid ounces, with US and imperial differences noted.",
    h1="Volume converter",
    lede="Convert between litres, millilitres, cubic metres, US gallons, quarts, cups and fluid "
         "ounces — for cooking, fuel and shipping.",
    units=[("l", "Litres", 1.0, "L"), ("ml", "Millilitres", 0.001, "mL"),
           ("m3", "Cubic metres", 1000.0, "m³"), ("gal", "US gallons", 3.785411784, "US gal"),
           ("qt", "US quarts", 0.946352946, "US qt"), ("pt", "US pints", 0.473176473, "US pt"),
           ("cup", "US cups", 0.2365882365, "US cup"), ("floz", "US fluid ounces", 0.0295735295625, "US fl oz"),
           ("ukgal", "Imperial gallons", 4.54609, "imp gal")],
    default_value=10, default_from="l",
    out_keys=["l", "gal", "qt", "cup", "floz", "m3"],
    how="""<p>Volume conversions are full of traps because several “gallon”, “pint” and “ounce” units
exist. A US liquid gallon is 3.78541 litres; an imperial (UK) gallon is 4.54609 litres — about 20%
larger. A US pint is 473.18 mL, while a UK pint is 568.26 mL, which is why a British beer glass and
an American pint are different sizes. The fluid ounce is a volume unit unrelated in size to the
ounce of mass.</p>
<p>For cooking, US recipes use cups of 236.59 mL and fluid ounces of 29.57 mL. For fuel, most of the
world sells petrol by the litre while the US uses gallons, which is why fuel-economy figures need
converting too. For shipping and storage, cubic metres are standard: one cubic metre is 1,000
litres. This calculator uses US customary volumes unless the unit label says otherwise; convert
imperial values with the labels provided.</p>""",
    formula="""<p>Convert to litres, then to the target unit:</p>
<div class="fml"><code>L = value × factor(from)
result = L / factor(to)

1 US gal = 3.785411784 L     1 imp gal = 4.54609 L
1 US qt  = 0.946352946 L     1 US cup = 0.2365882365 L
1 US fl oz = 0.0295735296 L  1 m³ = 1,000 L</code></div>
<p>So 10 L = 2.642 US gallons = 10.567 US quarts = 42.268 US cups = 338.14 US fl oz.</p>""",
    example="Converting {value} {from} gives {gal} in US gallons, {qt} in US quarts and {cup} in US "
            "cups — {floz} in fluid ounces.",
    mistakes=[
        "<strong>Mixing US and imperial gallons.</strong> An imperial gallon is 20% larger than a US "
        "gallon. Fuel economy and beer sizes are the usual casualties.",
        "<strong>Confusing fluid ounces with ounces of weight.</strong> A fluid ounce measures volume; "
        "an ounce (28.35 g) measures mass. They are not interchangeable.",
        "<strong>Rounding cups in recipes.</strong> One cup is 236.6 mL, not 250 mL. For baking, small "
        "errors change texture, so use millilitres for accuracy."
    ],
    faq=[
        ("How many litres in a gallon?",
         "A US gallon is 3.785 litres; an imperial gallon is 4.546 litres. Check which gallon a "
         "recipe or fuel figure uses."),
        ("How many cups in a litre?",
         "One litre is 4.227 US cups (236.6 mL each) or about 3.52 UK/imperial cups (284 mL each)."),
        ("How many millilitres in a US fluid ounce?",
         "One US fluid ounce is 29.574 mL. An imperial fluid ounce is 28.413 mL, which is why UK "
         "cookbooks can differ slightly."),
    ],
    related=["length-converter", "weight-converter", "area-converter", "fuel-cost-mpg"],
    note="US customary volumes unless the label says imperial; results rounded to three decimals.",
)


# ---------------------------------------------------------------------------
def _fuel_py(v):
    dist = float(v["distance"])
    mpg = float(v["mpg"]) or 0.0001
    price = float(v["price"])
    gallons = dist / mpg
    cost = gallons * price
    return {"cost": cost, "gallons": gallons, "per_mile": cost / dist if dist else 0.0,
            "per_100km": 235.214583 / mpg}


FUEL = calc(
    slug="fuel-cost-mpg", name="Fuel Cost & MPG Calculator", cat="conversions",
    title="Fuel Cost Calculator — Trip Cost, Gallons and MPG",
    desc="Calculate the fuel needed and the cost of a trip from distance, miles per gallon and the "
         "price of fuel. Includes cost per mile and the L/100km equivalent.",
    h1="Fuel cost and MPG calculator",
    lede="Enter a trip distance, your car's miles per gallon and the price of fuel to see how many "
         "gallons the trip needs, what it costs and the cost per mile.",
    fields=[num("distance", "Trip distance", 300, unit="miles", mn=0, mx=100000, step=1),
            num("mpg", "Fuel economy", 30, unit="mpg", mn=1, mx=200, step="0.1"),
            num("price", "Fuel price", 3.5, unit="USD / gal", pre="$", mn=0, mx=20, step="0.01")],
    outs=[("cost", "Trip fuel cost", "money"), ("gallons", "Fuel needed", "num2"),
          ("per_mile", "Cost per mile", "money"), ("per_100km", "L/100 km equivalent", "num1")],
    js="""
var dist=v.distance, mpg=(v.mpg||0.0001), gallons=dist/mpg, cost=gallons*v.price;
return {cost:cost, gallons:gallons, per_mile:dist?cost/dist:0, per_100km:235.214583/mpg};
""",
    py=_fuel_py,
    how="""<p>Fuel cost is distance divided by fuel economy, multiplied by the price per gallon. MPG
(miles per gallon) is the US convention; most other countries quote L/100 km, which is a
consumption figure rather than a distance figure — lower is better, and the two are reciprocal, not
linear. The conversion is <em>L/100 km = 235.215 ÷ MPG</em>. That is why a jump from 20 to 25 mpg
saves more fuel than a jump from 40 to 45 mpg.</p>
<p>Real-world fuel economy is usually worse than the sticker: cold starts, air conditioning, roof
racks, heavy loads and city traffic all raise consumption. EPA figures are tested in a laboratory.
For a trip estimate, use your own measured MPG from the last few tanks — miles driven divided by
gallons pumped. The calculator also gives cost per mile, the number to compare against public
transport or a rental car, and the L/100 km equivalent for international readers.</p>""",
    formula="""<div class="fml"><code>gallons     = distance / mpg
fuel cost   = gallons × price per gallon
cost/mile   = fuel cost / distance
L/100 km    = 235.214583 / mpg</code></div>
<p>To go the other way, US MPG = 235.214583 ÷ L/100 km. The constant comes from
(100 km × 3.785411784 L/gal ÷ 1.609344 km/mi).</p>""",
    example="A {distance}-mile trip at {mpg} mpg uses {gallons} gallons of fuel. At {price} per "
            "gallon the trip costs {cost}, or {per_mile} per mile. That fuel economy is {per_100km} "
            "L/100 km.",
    mistakes=[
        "<strong>Using the sticker MPG.</strong> Real-world economy is often 10–20% lower than the "
        "lab figure, especially in winter or city driving.",
        "<strong>Comparing MPG linearly.</strong> Going from 15 to 20 mpg saves 5 gallons per 300 "
        "miles; going from 30 to 35 saves just 1.4 gallons.",
        "<strong>Forgetting return trips and tolls.</strong> Enter the full round-trip distance, and "
        "treat tolls, parking and wear separately."
    ],
    faq=[
        ("How do I calculate MPG?",
         "Fill the tank, note the odometer, drive, then refill and divide the miles driven by the "
         "gallons added at the second fill. Repeat over several tanks for a reliable figure."),
        ("What is 30 mpg in L/100 km?",
         "30 mpg is about 7.84 L/100 km, using 235.215 ÷ 30. A 7 L/100 km car is about 33.6 mpg."),
        ("How much does a 300-mile trip cost in fuel?",
         "It depends on the car and fuel price. At 30 mpg and $3.50 a gallon it is 10 gallons and "
         "$35, assuming steady highway driving."),
    ],
    related=["electricity-cost", "speed-converter", "volume-converter", "length-converter"],
    note="US gallons and miles. Real fuel economy varies with speed, load, weather and driving style.",
)


# ---------------------------------------------------------------------------
def _elec_py(v):
    kw = float(v["watts"]) / 1000
    hours = float(v["hours"])
    days = float(v["days"])
    rate = float(v["rate"])
    kwh = kw * hours * days
    cost = kwh * rate
    per_day = cost / days if days else 0.0
    return {"cost": cost, "kwh": kwh, "per_day": per_day, "annual": per_day * 365}


ELEC = calc(
    slug="electricity-cost", name="Electricity Cost Calculator", cat="conversions",
    title="Electricity Cost Calculator — Appliance Energy Use & Cost",
    desc="Calculate what an appliance costs to run from its wattage, hours of use per day, days and "
         "your electricity price per kWh.",
    h1="Electricity cost calculator",
    lede="Enter an appliance's wattage, how many hours a day it runs and your electricity price to "
         "see the energy used, the cost for the period and the annual cost.",
    fields=[num("watts", "Power rating", 1500, unit="watts", mn=1, mx=100000, step=1, hint="Check the label on the appliance."),
            num("hours", "Hours used per day", 4, unit="hours", mn=0, mx=24, step="0.5"),
            num("days", "Days in period", 30, unit="days", mn=1, mx=366, step=1),
            num("rate", "Electricity price", 0.15, unit="USD / kWh", pre="$", mn=0, mx=5, step="0.001")],
    outs=[("cost", "Cost for the period", "money"), ("kwh", "Energy used", "num1"),
          ("per_day", "Cost per day", "money"), ("annual", "Cost per year at this usage", "money0")],
    js="""
var kwh=(v.watts/1000)*v.hours*v.days, cost=kwh*v.rate, perDay=cost/v.days;
return {cost:cost, kwh:kwh, per_day:perDay, annual:perDay*365};
""",
    py=_elec_py,
    how="""<p>Electricity is billed in kilowatt-hours (kWh). One kWh is 1,000 watts used for one hour,
so an appliance's cost is its power rating in kilowatts, times the hours it runs, times the price
per kWh. A 1,500 W space heater running 4 hours a day uses 6 kWh a day; at $0.15 per kWh that is
$0.90 a day, around $27 a month.</p>
<p>Heating and cooling appliances dominate household bills because they run for long periods at high
wattage. A 60 W television watched 4 hours a day uses 0.24 kWh — under 4 cents. The same logic
explains why switching an old incandescent bulb for an LED saves real money: an 8 W LED replacing a
60 W bulb for 5 hours a day saves 0.26 kWh a day, or about 95 kWh a year per bulb. Use the
appliance's actual label rating; some devices draw less than the label suggests in normal use, and
older appliances often draw more.</p>""",
    formula="""<div class="fml"><code>kWh    = (watts / 1,000) × hours/day × days
cost   = kWh × price per kWh
per day = cost / days
per year ≈ cost per day × 365</code></div>
<p>For a 1,500 W appliance used 4 h/day for 30 days at $0.15/kWh: 6 kWh/day × 30 = 180 kWh, and
180 × $0.15 = $27.00.</p>""",
    example="A {watts}-watt appliance used {hours} hours a day for {days} days consumes {kwh} kWh. "
            "At {rate} per kWh that costs {cost} for the period — about {per_day} a day and {annual} "
            "a year at the same usage.",
    mistakes=[
        "<strong>Using the maximum wattage for a variable appliance.</strong> Fridges, heat pumps and "
        "laptops cycle on and off; average draw is lower than the peak rating.",
        "<strong>Forgetting standby power.</strong> Devices on standby can draw 1–10 W continuously, "
        "which adds up across a house.",
        "<strong>Ignoring time-of-use tariffs.</strong> If your price changes by hour, run heavy "
        "appliances off-peak and calculate with the applicable rate."
    ],
    faq=[
        ("How much does it cost to run a 1,500 W heater?",
         "At 4 hours a day and $0.15/kWh, it uses 6 kWh a day and costs $0.90 — about $27 a month "
         "and $328 a year at that usage."),
        ("How many kWh does a refrigerator use?",
         "A typical modern fridge uses about 1–1.5 kWh a day, so 30–45 kWh a month. Older "
         "appliances can use noticeably more."),
        ("How do I read my electricity meter?",
         "Your bill shows kWh consumed and the price per kWh, which may include several components. "
         "Divide the total bill by the kWh used to get the effective all-in rate to enter here."),
    ],
    related=["fuel-cost-mpg", "paint-quantity", "tile-quantity", "temperature-converter"],
    note="Uses the rated wattage; variable-speed and standby consumption are approximated.",
)


# ---------------------------------------------------------------------------
def _paint_py(v):
    length = float(v["length"])
    width = float(v["width"])
    height = float(v["height"])
    coats = float(v["coats"])
    coverage = float(v["coverage"]) or 350.0
    openings = float(v["openings"])
    area = max(0.0, 2 * (length + width) * height - openings)
    gallons = area * coats / coverage
    cans = math.ceil(gallons - 1e-9)
    cost = cans * float(v["price"])
    return {"cans": cans, "gallons": gallons, "area": area, "cost": cost}


PAINT = calc(
    slug="paint-quantity", name="Paint Quantity Calculator", cat="conversions",
    title="Paint Calculator — How Much Paint Do I Need",
    desc="Calculate paint needed from room dimensions, coats, coverage per gallon and openings — "
         "in gallons, cans and cost.",
    h1="Paint quantity calculator",
    lede="Work out how much paint a room needs from its size, the number of coats and the paint's "
         "coverage, then turn it into cans and cost.",
    fields=[num("length", "Room length", 12, unit="ft", mn=1, mx=200, step="0.5"),
            num("width", "Room width", 15, unit="ft", mn=1, mx=200, step="0.5"),
            num("height", "Wall height", 8, unit="ft", mn=1, mx=30, step="0.5"),
            num("coats", "Number of coats", 2, unit="coats", mn=1, mx=5, step=1),
            num("openings", "Doors and windows area", 40, unit="sq ft", mn=0, mx=2000, step=5),
            num("coverage", "Coverage per gallon", 350, unit="sq ft / gal", mn=50, mx=1000, step=10),
            num("price", "Paint price per gallon", 40, unit="USD / gal", pre="$", mn=0, mx=500, step=1)],
    outs=[("cans", "Gallons (cans) to buy", "int"), ("gallons", "Paint required", "num2"),
          ("area", "Paintable wall area", "int"), ("cost", "Estimated paint cost", "money")],
    js="""
var area=Math.max(0, 2*(v.length+v.width)*v.height - v.openings);
var gallons=area*v.coats/(v.coverage||350);
var cans=Math.ceil(gallons-1e-9);
return {cans:cans, gallons:gallons, area:area, cost:cans*v.price};
""",
    py=_paint_py,
    how="""<p>Paint quantity is wall area divided by coverage, multiplied by the number of coats. Wall
area is the perimeter of the room (2 × length + 2 × width) times the ceiling height, minus the area
of doors and windows that will not be painted. A standard interior door is about 20 sq ft including
the frame and a window about 15 sq ft, which is why the default allowance is 40 sq ft.</p>
<p>Coverage matters more than people expect. Most paints state 350–400 sq ft per gallon on smooth,
primed drywall, but porous or textured surfaces absorb much more, and a drastic colour change may
need three coats rather than two. Buy the next whole can up from the calculated amount: leftover
paint is useful for touch-ups, whereas a shortfall means a second trip and a possible colour-batch
mismatch. Ceiling paint and primer are separate calculations — add the ceiling area if you are
painting it too.</p>""",
    formula="""<div class="fml"><code>wall area = 2 × (length + width) × height − openings
gallons  = wall area × coats / coverage per gallon
cans     = ceil(gallons)
cost     = cans × price per gallon</code></div>
<p>For a 12 × 15 ft room with 8 ft walls: 2 × 27 × 8 = 432 sq ft, minus 40 sq ft of openings = 392
sq ft. Two coats at 350 sq ft/gallon needs 2.24 gallons, so buy 3 cans.</p>""",
    example="A {length} × {width} ft room with {height} ft walls has {area} sq ft of paintable wall "
            "after openings. At {coats} coats and {coverage} sq ft per gallon you need {gallons} "
            "gallons, so buy {cans} cans — about {cost} at {price} per gallon.",
    mistakes=[
        "<strong>Forgetting the second coat.</strong> One coat of paint over a different colour "
        "rarely covers evenly; two coats is standard and some colours need three.",
        "<strong>Using ceiling square footage instead of wall area.</strong> Paint quantity depends on "
        "wall area — perimeter times height — not floor area.",
        "<strong>Not subtracting openings.</strong> Doors and windows can remove 10–15% of the wall "
        "area, which is often most of a can."
    ],
    faq=[
        ("How much paint do I need for a 12x15 room?",
         "With 8 ft walls that is about 392 sq ft of paintable wall. Two coats at 350 sq ft per "
         "gallon needs 2.24 gallons, so buy 3 gallons."),
        ("How many square feet does a gallon of paint cover?",
         "Usually 350–400 sq ft per gallon on smooth, primed drywall. Textured or porous surfaces "
         "and colour changes reduce coverage."),
        ("Do I need to add primer to the calculation?",
         "Primer is a separate coat with its own coverage, usually similar to paint. Add it as an "
         "extra coat when painting bare drywall, a strong colour or a repaired surface."),
    ],
    related=["tile-quantity", "area-converter", "length-converter", "electricity-cost"],
    note="Assumes smooth interior walls and one-room walls only; ceiling and trim not included.",
)


# ---------------------------------------------------------------------------
def _tile_py(v):
    floor = float(v["length"]) * float(v["width"])
    tw = float(v["tile_w"]) / 12
    th = float(v["tile_h"]) / 12
    per_tile = tw * th
    waste = 1 + float(v["waste"]) / 100
    needed = math.ceil(floor * waste / per_tile - 1e-9)
    return {"tiles": needed, "area": floor, "per_tile": per_tile,
            "cost": needed * per_tile * float(v["price"])}


TILE = calc(
    slug="tile-quantity", name="Tile Quantity Calculator", cat="conversions",
    title="Tile Calculator — How Many Tiles Do I Need",
    desc="Calculate the number of tiles for a floor or wall from the area, tile size, waste "
         "allowance and price per square foot.",
    h1="Tile quantity calculator",
    lede="Work out how many tiles a floor or wall needs from its dimensions, your tile size and a "
         "waste allowance — plus the area and estimated tile cost.",
    fields=[num("length", "Area length", 12, unit="ft", mn=0.5, mx=500, step="0.5"),
            num("width", "Area width", 10, unit="ft", mn=0.5, mx=500, step="0.5"),
            num("tile_w", "Tile width", 12, unit="in", mn=1, mx=120, step="0.5"),
            num("tile_h", "Tile height", 12, unit="in", mn=1, mx=120, step="0.5"),
            num("waste", "Waste allowance", 10, unit="%", mn=0, mx=50, step=1),
            num("price", "Tile price", 3.5, unit="USD / sq ft", pre="$", mn=0, mx=200, step="0.25")],
    outs=[("tiles", "Tiles needed", "int"), ("area", "Area to cover", "num1"),
          ("per_tile", "Area per tile", "num2"), ("cost", "Estimated tile cost", "money0")],
    js="""
var area=v.length*v.width, per=(v.tile_w/12)*(v.tile_h/12);
var needed=Math.ceil(area*(1+v.waste/100)/per-1e-9);
return {tiles:needed, area:area, per_tile:per, cost:needed*per*v.price};
""",
    py=_tile_py,
    how="""<p>Tiling quantity is area divided by tile area, plus a waste allowance for cuts, breakages
and pattern matching. Straight-lay patterns need about 5–10% extra; diagonal, herringbone and
patterns with a border need 10–15%, because off-cut pieces cannot be reused. Large-format tiles
often need more waste than small ones for the same area.</p>
<p>Tiles are sold in boxes, and the box label states coverage — floor area is quoted in square feet
while tile dimensions are usually in inches, so convert carefully. It also matters which area you
are tiling: floor area is simple length × width, but wall area excludes doors and windows and can
require extra cuts around fittings. Add a spare box if your pattern needs a particular batch
number, since a later batch may not match the dye lot exactly. Grout, adhesive and trim are separate
purchases and are not included in this estimate.</p>""",
    formula="""<div class="fml"><code>area       = length × width
tile area  = (tile width in / 12) × (tile height in / 12)
tiles      = ceil( area × (1 + waste% / 100) / tile area )
cost       = tiles × tile area × price per sq ft</code></div>
<p>For a 12 × 10 ft floor with 12 × 12 in tiles and 10% waste: area 120 sq ft, tile area 1 sq ft,
so 120 × 1.10 = 132 tiles.</p>""",
    example="A {length} × {width} ft area is {area} sq ft. With {tile_w} × {tile_h} inch tiles and a "
            "{waste}% waste allowance you need {tiles} tiles. At {price} per sq ft the tiles cost "
            "about {cost}.",
    mistakes=[
        "<strong>No waste allowance.</strong> Cuts at edges, breakages and pattern matching all "
        "consume tiles. Buy 10% extra for straight lays and 15% for diagonal patterns.",
        "<strong>Mixing inches and feet.</strong> Tile sizes are normally in inches and room sizes in "
        "feet; convert tiles to feet by dividing by 12, or areas by 144.",
        "<strong>Forgetting the pattern.</strong> Herringbone and chevron patterns substantially "
        "increase waste because every piece is cut at an angle."
    ],
    faq=[
        ("How many tiles do I need for a 12x10 room?",
         "With 12 × 12 inch tiles and 10% waste, 132 tiles cover 120 sq ft. Larger or smaller tiles "
         "change the count, not the total area."),
        ("How much waste should I allow for tiles?",
         "Around 10% for a standard straight lay, 15% for diagonal or patterned layouts, and more "
         "for rooms with many corners or obstructions."),
        ("How do I calculate tile area per box?",
         "Look for the coverage printed on the box, usually in square feet or square metres. If it "
         "is not shown, multiply the number of tiles by the area of one tile."),
    ],
    related=["paint-quantity", "area-converter", "length-converter", "volume-converter"],
    note="Tiles only; adhesive, grout and trim are not included.",
)


CALCS = [LENGTH, WEIGHT, TEMPERATURE, SPEED, AREA, VOLUME, FUEL, ELEC, PAINT, TILE]
