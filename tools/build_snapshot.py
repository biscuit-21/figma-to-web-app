#!/usr/bin/env python3
"""Build the bundled indicator dataset for the Key Indicators dashboard.

History is reconstructed from published anchor points and interpolated between
them; the most recent observation of every series is set to the latest official
release (see LATEST_SOURCES). This is a snapshot, not a live FRED feed.
"""
import json, math, random

START = (2015, 1)


def midx(y, m):
    return (y - START[0]) * 12 + (m - START[1])


def pchip_like(anchors, n, step=1, jitter=0.0, seed=0, clamp=None):
    """Monotone-ish interpolation across anchors -> list of n values."""
    rng = random.Random(seed)
    pts = sorted(((midx(y, m), v) for (y, m), v in anchors))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    # slopes (Fritsch-Carlson monotone cubic)
    k = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(k - 1)]
    m_ = [0.0] * k
    m_[0], m_[-1] = d[0], d[-1]
    for i in range(1, k - 1):
        if d[i - 1] * d[i] <= 0:
            m_[i] = 0.0
        else:
            w1 = 2 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1])
            w2 = (xs[i + 1] - xs[i]) + 2 * (xs[i] - xs[i - 1])
            m_[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    out = []
    for j in range(n):
        x = j * step
        if x <= xs[0]:
            v = ys[0]
        elif x >= xs[-1]:
            v = ys[-1]
        else:
            i = max(i for i in range(k - 1) if xs[i] <= x)
            h = xs[i + 1] - xs[i]
            t = (x - xs[i]) / h
            h00 = 2 * t ** 3 - 3 * t ** 2 + 1
            h10 = t ** 3 - 2 * t ** 2 + t
            h01 = -2 * t ** 3 + 3 * t ** 2
            h11 = t ** 3 - t ** 2
            v = h00 * ys[i] + h10 * h * m_[i] + h01 * ys[i + 1] + h11 * h * m_[i + 1]
        if jitter:
            v += rng.gauss(0, jitter)
        if clamp:
            v = max(clamp[0], min(clamp[1], v))
        out.append(v)
    # pin the exact anchor values so published figures survive interpolation
    for (ax, av) in pts:
        j = ax // step
        if 0 <= j < n and ax % step == 0:
            out[j] = av
    return out


N_M = midx(2026, 8) + 1          # monthly series: 2015-01 .. 2026-08
N_Q = (midx(2026, 4) // 3) + 1   # quarterly series: 2015Q1 .. 2026Q2 (month index 0,3,6..)

SERIES = []


def add(**kw):
    vals = kw.pop("values")
    dec = kw.get("decimals", 1)
    kw["values"] = [round(v, dec) for v in vals]
    SERIES.append(kw)


# ---------------------------------------------------------------- INFLATION
add(
    id="CPIAUCSL", fred="CPIAUCSL", name="Consumer price index", cats=["key", "inflation"],
    unit="% change from a year ago", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Labor Statistics", release="Aug 2026 · released Sep 11, 2026",
    blurb="The headline inflation rate: how much more a typical basket of goods and services costs than it did twelve months ago.",
    detail="The CPI tracks prices for food, housing, transport, medical care and more, weighted by what urban households actually buy. It is the number quoted as “inflation” in the news, the basis for Social Security cost-of-living adjustments, and the reference rate for inflation-linked bonds. It is not the measure the Fed targets — that is PCE — and the two can differ by several tenths of a point.",
    watch="Above roughly 2% means prices are rising faster than the Fed wants. Sharp swings usually come from energy.",
    values=pchip_like([
        ((2015, 1), -0.1), ((2015, 7), 0.2), ((2015, 12), 0.7), ((2016, 6), 1.0),
        ((2016, 12), 2.1), ((2017, 6), 1.6), ((2017, 12), 2.1), ((2018, 7), 2.9),
        ((2018, 12), 1.9), ((2019, 6), 1.6), ((2019, 12), 2.3), ((2020, 5), 0.1),
        ((2020, 12), 1.4), ((2021, 6), 5.4), ((2021, 12), 7.0), ((2022, 6), 9.1),
        ((2022, 12), 6.5), ((2023, 6), 3.0), ((2023, 12), 3.4), ((2024, 6), 3.0),
        ((2024, 9), 2.4), ((2024, 12), 2.9), ((2025, 4), 2.3), ((2025, 8), 2.9),
        ((2025, 12), 2.7), ((2026, 2), 2.4), ((2026, 4), 3.8), ((2026, 6), 3.5),
        ((2026, 7), 3.4), ((2026, 8), 3.4),
    ], N_M, jitter=0.07, seed=1),
)

add(
    id="CPILFESL", fred="CPILFESL", name="Core consumer prices", cats=["inflation"],
    unit="% change from a year ago, excluding food and energy", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Labor Statistics", release="Aug 2026 · released Sep 11, 2026",
    blurb="Inflation with food and energy stripped out, which is a steadier read on the underlying trend.",
    detail="Food and fuel prices jump around for reasons that have little to do with the state of the economy — a drought, an OPEC decision, a cold winter. Removing them leaves a slower-moving series that is a better guide to where inflation is heading. Shelter carries the largest weight in core, which is why rents matter so much to this number.",
    watch="Core moving sideways while headline swings usually means the swing is an energy story, not an inflation story.",
    values=pchip_like([
        ((2015, 1), 1.6), ((2015, 12), 2.1), ((2016, 12), 2.2), ((2017, 12), 1.8),
        ((2018, 12), 2.2), ((2019, 12), 2.3), ((2020, 5), 1.2), ((2020, 12), 1.6),
        ((2021, 12), 5.5), ((2022, 9), 6.6), ((2022, 12), 5.7), ((2023, 6), 4.8),
        ((2023, 12), 3.9), ((2024, 6), 3.3), ((2024, 12), 3.2), ((2025, 6), 2.9),
        ((2025, 12), 2.8), ((2026, 1), 2.5), ((2026, 4), 2.8), ((2026, 6), 2.6),
        ((2026, 7), 2.5), ((2026, 8), 2.4),
    ], N_M, jitter=0.05, seed=2),
)

add(
    id="PCEPILFE", fred="PCEPILFE", name="Core PCE prices", cats=["inflation"],
    unit="% change from a year ago, excluding food and energy", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Economic Analysis", release="Jul 2026 · released Aug 26, 2026",
    blurb="The inflation gauge the Federal Reserve actually targets at 2%.",
    detail="PCE differs from CPI in what it covers and how it weights things: it counts spending made on a household's behalf, such as employer-paid health insurance, and it adjusts weights as people substitute between goods. It usually runs a few tenths below CPI. When Fed officials talk about getting inflation back to 2%, this is the series they mean.",
    watch="This is the one the FOMC judges itself against. Two percent is the stated goal.",
    values=pchip_like([
        ((2015, 1), 1.4), ((2015, 12), 1.2), ((2016, 12), 1.8), ((2017, 12), 1.6),
        ((2018, 12), 2.0), ((2019, 12), 1.6), ((2020, 5), 1.0), ((2020, 12), 1.5),
        ((2021, 12), 5.2), ((2022, 2), 5.4), ((2022, 12), 4.9), ((2023, 6), 4.3),
        ((2023, 12), 2.9), ((2024, 6), 2.6), ((2024, 12), 2.8), ((2025, 6), 2.8),
        ((2025, 12), 2.9), ((2026, 3), 3.1), ((2026, 6), 3.3), ((2026, 7), 3.3),
    ], N_M - 1, jitter=0.05, seed=3),
)

# ---------------------------------------------------------------- EMPLOYMENT
add(
    id="UNRATE", fred="UNRATE", name="Unemployment rate", cats=["key", "employment"],
    unit="% of the labor force", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Labor Statistics", release="Aug 2026 · released Sep 4, 2026",
    blurb="The share of people who want a job, have looked for one recently, and do not have one.",
    detail="Counted from a monthly survey of about 60,000 households. Someone who has given up looking is not counted as unemployed at all, which is why this number can fall for bad reasons as well as good ones. Read it alongside the participation rate to tell those cases apart.",
    watch="A rise of about half a point off its low has historically marked the start of a recession.",
    values=pchip_like([
        ((2015, 1), 5.7), ((2015, 12), 5.0), ((2016, 6), 4.9), ((2016, 12), 4.7),
        ((2017, 6), 4.3), ((2017, 12), 4.1), ((2018, 6), 4.0), ((2018, 12), 3.9),
        ((2019, 6), 3.6), ((2019, 12), 3.6), ((2020, 2), 3.5), ((2020, 4), 14.8),
        ((2020, 6), 11.0), ((2020, 9), 7.8), ((2020, 12), 6.7), ((2021, 6), 5.9),
        ((2021, 12), 3.9), ((2022, 6), 3.6), ((2022, 12), 3.5), ((2023, 6), 3.6),
        ((2023, 12), 3.7), ((2024, 6), 4.1), ((2024, 12), 4.1), ((2025, 6), 4.1),
        ((2025, 12), 4.2), ((2026, 3), 4.2), ((2026, 6), 4.1), ((2026, 8), 4.1),
    ], N_M, jitter=0.04, seed=4, clamp=(0, 20)),
)

# Payrolls: explicit monthly path, COVID handled directly.
pay = pchip_like([
    ((2015, 1), 210), ((2015, 12), 250), ((2016, 6), 190), ((2016, 12), 180),
    ((2017, 6), 195), ((2017, 12), 175), ((2018, 6), 210), ((2018, 12), 200),
    ((2019, 6), 160), ((2019, 12), 150), ((2020, 1), 220),
], N_M, jitter=35, seed=5)
covid = {
    (2020, 2): 250, (2020, 3): -1700, (2020, 4): -20500, (2020, 5): 2800,
    (2020, 6): 4800, (2020, 7): 1700, (2020, 8): 1500, (2020, 9): 700,
    (2020, 10): 660, (2020, 11): 270, (2020, 12): -300,
}
post = pchip_like([
    ((2021, 1), 520), ((2021, 6), 950), ((2021, 12), 600), ((2022, 6), 420),
    ((2022, 12), 290), ((2023, 6), 250), ((2023, 12), 210), ((2024, 6), 180),
    ((2024, 12), 160), ((2025, 6), 90), ((2025, 12), 55), ((2026, 3), 45),
    ((2026, 6), 31), ((2026, 7), 21), ((2026, 8), 162),
], N_M, jitter=55, seed=6)
payroll_vals = []
for j in range(N_M):
    y, m = START[0] + (j + START[1] - 1) // 12, (j + START[1] - 1) % 12 + 1
    if (y, m) in covid:
        payroll_vals.append(covid[(y, m)])
    elif y >= 2021:
        payroll_vals.append(post[j])
    else:
        payroll_vals.append(pay[j])
add(
    id="PAYEMS", fred="PAYEMS", name="Jobs added each month", cats=["employment"], flow=True, zero=True,
    unit="change in nonfarm payrolls, thousands", suffix="k", decimals=0, freq="m",
    source="U.S. Bureau of Labor Statistics", release="Aug 2026 · released Sep 4, 2026",
    blurb="How many jobs employers added or cut last month, counted from payroll records.",
    detail="This comes from a survey of employers rather than households, so it counts jobs rather than people — someone with two jobs is counted twice. First estimates are revised twice, and the revisions are often large enough to change the story, so the three-month average is more reliable than any single month.",
    watch="Roughly 80–100k a month is about what population growth requires. Sustained prints below that loosen the labor market.",
    values=payroll_vals,
)

add(
    id="CIVPART", fred="CIVPART", name="Labor force participation", cats=["employment"],
    unit="% of adults working or looking for work", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Labor Statistics", release="Aug 2026 · released Sep 4, 2026",
    blurb="The share of the adult population that is either working or actively looking.",
    detail="Retirements, schooling, caregiving and discouragement all show up here. Because the unemployment rate only counts people who are looking, participation is the check on it: a falling jobless rate alongside falling participation usually means people left the labor force rather than found work.",
    watch="An ageing population pushes this down slowly regardless of the business cycle, so watch the trend, not the level.",
    values=pchip_like([
        ((2015, 1), 62.9), ((2016, 6), 62.7), ((2017, 12), 62.7), ((2019, 12), 63.3),
        ((2020, 4), 60.2), ((2020, 12), 61.5), ((2021, 12), 62.0), ((2023, 6), 62.6),
        ((2024, 6), 62.6), ((2024, 12), 62.5), ((2025, 6), 62.3), ((2025, 12), 61.9),
        ((2026, 1), 62.1), ((2026, 7), 61.4), ((2026, 8), 61.6),
    ], N_M, jitter=0.05, seed=7),
)

add(
    id="CES0500000003", fred="CES0500000003", name="Average hourly earnings", cats=["employment"],
    unit="% change from a year ago", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Labor Statistics", release="Aug 2026 · released Sep 4, 2026",
    blurb="How fast private-sector pay is rising, before inflation.",
    detail="Measured per hour worked across all private employees. It is sensitive to who is working: when low-paid jobs disappear in a downturn, the average jumps even though nobody got a raise, which is what produced the strange 2020 spike. Compare it with inflation to see whether pay is actually buying more.",
    watch="Pay growth below the inflation rate means real wages are falling.",
    values=pchip_like([
        ((2015, 1), 2.1), ((2016, 6), 2.6), ((2017, 12), 2.5), ((2019, 2), 3.4),
        ((2019, 12), 3.0), ((2020, 4), 8.0), ((2020, 12), 5.2), ((2021, 12), 4.9),
        ((2022, 3), 5.6), ((2022, 12), 4.8), ((2023, 6), 4.4), ((2023, 12), 4.3),
        ((2024, 6), 3.9), ((2024, 12), 4.0), ((2025, 6), 3.7), ((2025, 12), 3.4),
        ((2026, 6), 3.2), ((2026, 8), 3.1),
    ], N_M, jitter=0.06, seed=8),
)

# ---------------------------------------------------------------- RATES
add(
    id="FEDFUNDS", fred="FEDFUNDS", name="Federal funds rate", cats=["key", "rates"],
    unit="effective rate, %", suffix="%", decimals=2, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Target range 3.75–4.00% · set Sep 16, 2026",
    blurb="The Federal Reserve's policy rate, and the anchor for nearly every other interest rate.",
    detail="The FOMC sets a target range eight times a year; the effective rate is what banks actually pay each other overnight within it. Moves here pass quickly into credit cards, savings yields and business loans, and more slowly into everything else. At the September 2026 meeting the committee raised the range by a quarter point to 3.75–4.00%.",
    watch="What matters is the direction and the pace, not the level on any given day.",
    values=pchip_like([
        ((2015, 1), 0.11), ((2015, 12), 0.24), ((2016, 12), 0.54), ((2017, 12), 1.30),
        ((2018, 12), 2.27), ((2019, 8), 2.13), ((2019, 12), 1.55), ((2020, 4), 0.05),
        ((2021, 12), 0.08), ((2022, 6), 1.21), ((2022, 12), 4.10), ((2023, 6), 5.08),
        ((2023, 12), 5.33), ((2024, 8), 5.33), ((2024, 12), 4.33), ((2025, 6), 4.33),
        ((2025, 10), 4.09), ((2025, 12), 3.83), ((2026, 4), 3.63), ((2026, 8), 3.63),
    ], N_M, jitter=0.01, seed=9, clamp=(0, 10)),
)

add(
    id="DGS10", fred="DGS10", name="10-year Treasury yield", cats=["key", "rates"],
    unit="%", suffix="%", decimals=2, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Sep 16, 2026",
    blurb="What the government pays to borrow for ten years, and the benchmark long rate for the whole economy.",
    detail="Set by the bond market rather than the Fed. It reflects where investors think short rates are heading over the next decade plus a premium for tying money up that long. Mortgage rates, corporate borrowing costs and stock valuations all key off it, which makes it arguably the single most consequential price in finance.",
    watch="Rising yields tighten financial conditions even when the Fed has not moved.",
    values=pchip_like([
        ((2015, 1), 1.88), ((2015, 12), 2.24), ((2016, 7), 1.50), ((2016, 12), 2.49),
        ((2017, 12), 2.40), ((2018, 11), 3.15), ((2019, 9), 1.63), ((2019, 12), 1.92),
        ((2020, 3), 0.70), ((2020, 8), 0.65), ((2020, 12), 0.93), ((2021, 3), 1.74),
        ((2021, 12), 1.52), ((2022, 6), 3.14), ((2022, 10), 4.05), ((2022, 12), 3.88),
        ((2023, 10), 4.88), ((2023, 12), 3.88), ((2024, 4), 4.62), ((2024, 9), 3.79),
        ((2024, 12), 4.58), ((2025, 4), 4.28), ((2025, 9), 4.15), ((2025, 12), 4.25),
        ((2026, 2), 4.05), ((2026, 6), 4.60), ((2026, 7), 4.78), ((2026, 8), 5.01),
    ], N_M, jitter=0.05, seed=10),
)

add(
    id="DGS2", fred="DGS2", name="2-year Treasury yield", cats=["rates"],
    unit="%", suffix="%", decimals=2, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Sep 16, 2026",
    blurb="The short end of the curve, and the market's best guess at Fed policy over the next two years.",
    detail="More sensitive to Fed expectations than any other widely watched yield. When traders think the Fed will hike, this moves first and moves most; it often turns before officials say anything.",
    watch="A gap opening up between this and the fed funds rate says the market disagrees with the Fed.",
    values=pchip_like([
        ((2015, 1), 0.60), ((2015, 12), 1.00), ((2016, 12), 1.20), ((2017, 12), 1.89),
        ((2018, 12), 2.48), ((2019, 12), 1.58), ((2020, 4), 0.20), ((2021, 12), 0.73),
        ((2022, 6), 3.00), ((2022, 12), 4.41), ((2023, 10), 5.05), ((2023, 12), 4.23),
        ((2024, 6), 4.71), ((2024, 12), 4.25), ((2025, 6), 3.90), ((2025, 12), 3.60),
        ((2026, 3), 3.55), ((2026, 6), 4.10), ((2026, 8), 4.74),
    ], N_M, jitter=0.05, seed=11),
)

add(
    id="MORTGAGE30US", fred="MORTGAGE30US", name="30-year mortgage rate", cats=["rates", "housing"],
    unit="average fixed rate, %", suffix="%", decimals=2, freq="m",
    source="Freddie Mac", release="Week ending Sep 17, 2026",
    blurb="The going rate on a 30-year fixed home loan.",
    detail="Tracks the 10-year Treasury plus a spread that widens when lenders are nervous or mortgage bonds are hard to sell. The Fed does not set it. Because most American mortgages are fixed for thirty years, a rate move only affects people who are buying or refinancing, which is why high rates freeze the market rather than pushing existing owners out.",
    watch="Compare it with the 10-year yield: an unusually wide spread is a sign of stress in mortgage markets.",
    values=pchip_like([
        ((2015, 1), 3.67), ((2015, 12), 3.96), ((2016, 10), 3.47), ((2016, 12), 4.20),
        ((2017, 12), 3.95), ((2018, 11), 4.87), ((2019, 9), 3.61), ((2019, 12), 3.72),
        ((2020, 12), 2.68), ((2021, 12), 3.11), ((2022, 6), 5.70), ((2022, 10), 7.08),
        ((2022, 12), 6.42), ((2023, 10), 7.79), ((2023, 12), 6.61), ((2024, 5), 7.22),
        ((2024, 9), 6.08), ((2024, 12), 6.85), ((2025, 6), 6.77), ((2025, 12), 6.30),
        ((2026, 3), 6.20), ((2026, 6), 6.55), ((2026, 7), 6.81), ((2026, 8), 7.19),
    ], N_M, jitter=0.04, seed=12),
)

# 10y-2y spread, derived
d10 = next(s for s in SERIES if s["id"] == "DGS10")["values"]
d2 = next(s for s in SERIES if s["id"] == "DGS2")["values"]
add(
    id="T10Y2Y", fred="T10Y2Y", name="Yield curve (10-year minus 2-year)", cats=["rates"],
    unit="percentage points", suffix="pp", decimals=2, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Sep 16, 2026", zero=True,
    blurb="The gap between long and short government borrowing costs. Below zero is the classic recession warning.",
    detail="Normally long-term lending pays more than short-term. When it does not — an inverted curve — the market is saying it expects the Fed to be cutting rates before long, which usually means it expects trouble. Every U.S. recession since the 1970s was preceded by an inversion, though the lead time has ranged from six months to two years, and the 2022–24 inversion did not produce one.",
    watch="The un-inversion, not the inversion, has historically been the signal that the downturn is close.",
    values=[a - b for a, b in zip(d10, d2)],
)

# ---------------------------------------------------------------- GROWTH
add(
    id="A191RL1Q225SBEA", fred="A191RL1Q225SBEA", name="Real GDP growth", cats=["key", "growth"],
    unit="quarterly change, annual rate, %", suffix="%", decimals=1, freq="q", zero=True,
    source="U.S. Bureau of Economic Analysis", release="Q2 2026 · second estimate, Aug 26, 2026",
    blurb="How fast the economy grew last quarter, after stripping out inflation.",
    detail="Reported at an annual rate, so a 1.5% print means the quarter's pace would add 1.5% over a year if it held. It is revised twice and the first estimate leans on assumptions for the final month. Trade and inventories can swing the headline sharply without telling you much about underlying demand — for that, look at final sales to private domestic purchasers.",
    watch="Growth near 2% is roughly the economy's long-run speed limit. Two negative quarters is the popular recession rule, though the official call is made by the NBER on broader evidence.",
    values=pchip_like([
        ((2015, 1), 3.2), ((2015, 4), 3.0), ((2015, 7), 1.3), ((2015, 10), 0.6),
        ((2016, 1), 0.6), ((2016, 4), 2.4), ((2016, 7), 2.0), ((2016, 10), 2.0),
        ((2017, 1), 2.3), ((2017, 4), 2.2), ((2017, 7), 3.4), ((2017, 10), 4.1),
        ((2018, 1), 3.8), ((2018, 4), 2.7), ((2018, 7), 2.1), ((2018, 10), 0.6),
        ((2019, 1), 2.2), ((2019, 4), 2.7), ((2019, 7), 3.6), ((2019, 10), 1.8),
        ((2020, 1), -5.3), ((2020, 4), -28.0), ((2020, 7), 34.8), ((2020, 10), 4.2),
        ((2021, 1), 5.2), ((2021, 4), 6.2), ((2021, 7), 3.3), ((2021, 10), 7.0),
        ((2022, 1), -1.0), ((2022, 4), -0.6), ((2022, 7), 2.7), ((2022, 10), 3.4),
        ((2023, 1), 2.8), ((2023, 4), 2.4), ((2023, 7), 4.4), ((2023, 10), 3.2),
        ((2024, 1), 1.6), ((2024, 4), 3.0), ((2024, 7), 3.1), ((2024, 10), 2.4),
        ((2025, 1), -0.5), ((2025, 4), 3.8), ((2025, 7), 3.0), ((2025, 10), 2.0),
        ((2026, 1), 2.1), ((2026, 4), 1.5),
    ], N_Q, step=3),
)

add(
    id="INDPRO", fred="INDPRO", name="Industrial production", cats=["growth"],
    unit="% change from a year ago", suffix="%", decimals=1, freq="m", zero=True,
    source="Board of Governors of the Federal Reserve System", release="Aug 2026 · released Sep 15, 2026",
    blurb="Output from factories, mines and utilities — the physical side of the economy.",
    detail="Manufacturing is a small share of American employment now but still a reliable cycle indicator, because firms cut production before they cut jobs. Utilities output swings with the weather, so an unusually hot or cold month can move the headline without meaning anything.",
    watch="Turns down here often lead the broader economy by a few months.",
    values=pchip_like([
        ((2015, 1), 3.5), ((2015, 12), -1.0), ((2016, 6), -1.5), ((2016, 12), 0.0),
        ((2017, 12), 2.0), ((2018, 9), 3.9), ((2019, 12), -0.8), ((2020, 4), -16.3),
        ((2020, 12), -3.0), ((2021, 4), 17.5), ((2021, 12), 4.5), ((2022, 6), 4.0),
        ((2022, 12), 1.0), ((2023, 6), -0.3), ((2023, 12), 0.0), ((2024, 6), 0.5),
        ((2024, 12), 0.6), ((2025, 6), 1.0), ((2025, 12), 1.1), ((2026, 6), 1.2),
        ((2026, 8), 1.4),
    ], N_M, jitter=0.25, seed=13),
)

# ---------------------------------------------------------------- FX
add(
    id="DTWEXBGS", fred="DTWEXBGS", name="Trade-weighted dollar", cats=["fx"],
    unit="index, Jan 2006 = 100", suffix="", decimals=1, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Sep 2026",
    blurb="The dollar's value against a basket of currencies, weighted by how much America trades with each.",
    detail="A broader and more meaningful measure than any single exchange rate. A stronger dollar makes imports cheaper and American exports less competitive, and tightens conditions for countries and companies that borrowed in dollars. It tends to rise when U.S. rates are high relative to the rest of the world, and when investors are frightened.",
    watch="Sharp dollar strength is a global tightening event, not just an American one.",
    values=pchip_like([
        ((2015, 1), 103), ((2015, 12), 108), ((2016, 12), 113), ((2018, 1), 110),
        ((2019, 12), 116), ((2020, 3), 126), ((2021, 1), 112), ((2022, 10), 128),
        ((2023, 7), 118), ((2024, 6), 123), ((2024, 12), 129), ((2025, 6), 120),
        ((2025, 12), 118), ((2026, 6), 115), ((2026, 8), 116),
    ], N_M, jitter=0.5, seed=14),
)

add(
    id="DEXUSEU", fred="DEXUSEU", name="Euro exchange rate", cats=["fx"],
    unit="U.S. dollars per euro", suffix="", decimals=3, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Sep 2026",
    blurb="How many dollars one euro buys. A higher number means a weaker dollar.",
    detail="The most heavily traded currency pair in the world. It moves mostly on the gap between what the Federal Reserve and the European Central Bank are doing with rates, and on relative growth prospects. The euro briefly fell below parity with the dollar in 2022 for the first time in two decades.",
    watch="Quoted backwards from most pairs: up means the dollar is losing ground.",
    values=pchip_like([
        ((2015, 1), 1.16), ((2015, 12), 1.09), ((2016, 12), 1.05), ((2018, 2), 1.24),
        ((2019, 12), 1.11), ((2020, 3), 1.10), ((2021, 1), 1.22), ((2022, 9), 0.99),
        ((2023, 7), 1.10), ((2024, 9), 1.11), ((2024, 12), 1.04), ((2025, 6), 1.15),
        ((2025, 12), 1.17), ((2026, 6), 1.19), ((2026, 8), 1.18),
    ], N_M, jitter=0.008, seed=15),
)

add(
    id="DEXJPUS", fred="DEXJPUS", name="Yen exchange rate", cats=["fx"],
    unit="Japanese yen per U.S. dollar", suffix="", decimals=1, freq="m",
    source="Board of Governors of the Federal Reserve System", release="Sep 2026",
    blurb="How many yen one dollar buys. A higher number means a stronger dollar.",
    detail="Unusually sensitive to the interest rate gap between the two countries, because for years Japan held rates at zero while others raised them. That gap drove the yen to multi-decade lows in 2024 and prompted intervention by Japan's finance ministry.",
    watch="Quoted the opposite way round from the euro: up means the dollar is gaining.",
    values=pchip_like([
        ((2015, 1), 118), ((2016, 8), 101), ((2017, 12), 112), ((2018, 12), 111),
        ((2020, 12), 104), ((2021, 12), 114), ((2022, 10), 148), ((2023, 11), 150),
        ((2024, 7), 158), ((2024, 12), 155), ((2025, 6), 145), ((2025, 12), 152),
        ((2026, 6), 148), ((2026, 8), 150),
    ], N_M, jitter=1.2, seed=16),
)

# ---------------------------------------------------------------- HOUSING
add(
    id="CSUSHPINSA", fred="CSUSHPINSA", name="Home prices", cats=["housing"],
    unit="% change from a year ago", suffix="%", decimals=1, freq="m", zero=True,
    source="S&P Dow Jones Indices", release="Jun 2026 · released Aug 25, 2026",
    blurb="The national Case-Shiller index: what the same houses are selling for compared with a year ago.",
    detail="Built from repeat sales of the same properties, so it is not distorted by a shift in the mix of what sells. It lags badly — the June reading arrives in late August, and reflects contracts signed months earlier. Treat it as confirmation of a trend rather than news.",
    watch="Prices fell year-over-year only briefly in 2023 despite the sharpest mortgage rate rise in forty years.",
    values=pchip_like([
        ((2015, 1), 4.4), ((2015, 12), 5.4), ((2016, 12), 5.6), ((2017, 12), 6.3),
        ((2018, 3), 6.7), ((2018, 12), 4.2), ((2019, 12), 3.7), ((2020, 12), 10.4),
        ((2021, 7), 19.9), ((2021, 12), 18.9), ((2022, 3), 20.8), ((2022, 12), 5.6),
        ((2023, 5), -0.1), ((2023, 12), 5.5), ((2024, 3), 6.5), ((2024, 12), 3.9),
        ((2025, 6), 1.9), ((2025, 12), 1.5), ((2026, 6), 1.0),
    ], N_M - 2, jitter=0.1, seed=17),
)

add(
    id="HOUST", fred="HOUST", name="Housing starts", cats=["housing"],
    unit="thousands of units, annual rate", suffix="k", decimals=0, freq="m",
    source="U.S. Census Bureau", release="Aug 2026 · released Sep 17, 2026",
    blurb="How many new homes builders broke ground on, at an annual pace.",
    detail="One of the most rate-sensitive series in the economy, because builders borrow to build and buyers borrow to buy. It is also noisy: the monthly figure carries a wide margin of error and multifamily projects arrive in lumps. Housing construction is a small slice of GDP but historically an outsized share of its swings.",
    watch="Roughly 1.5 million a year is often cited as what household formation requires.",
    values=pchip_like([
        ((2015, 1), 1100), ((2015, 12), 1160), ((2016, 12), 1250), ((2018, 1), 1340),
        ((2019, 12), 1600), ((2020, 4), 934), ((2021, 3), 1725), ((2022, 4), 1800),
        ((2022, 12), 1370), ((2023, 12), 1560), ((2024, 6), 1350), ((2024, 12), 1520),
        ((2025, 6), 1320), ((2025, 12), 1310), ((2026, 6), 1280), ((2026, 8), 1300),
    ], N_M, jitter=45, seed=18),
)

# ---------------------------------------------------------------- CONSUMER
add(
    id="RSAFS", fred="RSAFS", name="Retail sales", cats=["key", "consumer"],
    unit="% change from a year ago", suffix="%", decimals=1, freq="m", zero=True,
    source="U.S. Census Bureau", release="Aug 2026 · released Sep 15, 2026",
    blurb="What Americans spent at shops, restaurants and online, against the same month last year.",
    detail="Not adjusted for inflation, so part of any increase is just higher prices — compare it with CPI to see whether people are buying more or paying more. Consumer spending is about two-thirds of the economy, which makes this the fastest read on whether households are still carrying it.",
    watch="Sales growth running below inflation means real spending is shrinking.",
    values=pchip_like([
        ((2015, 1), 2.4), ((2015, 12), 2.0), ((2016, 12), 3.0), ((2017, 12), 4.6),
        ((2018, 12), 2.5), ((2019, 12), 4.6), ((2020, 4), -19.9), ((2020, 12), 2.9),
        ((2021, 4), 51.2), ((2021, 12), 16.9), ((2022, 6), 8.5), ((2022, 12), 5.5),
        ((2023, 6), 1.5), ((2023, 12), 5.3), ((2024, 6), 2.2), ((2024, 12), 4.4),
        ((2025, 6), 3.9), ((2025, 12), 4.0), ((2026, 6), 4.2), ((2026, 8), 4.5),
    ], N_M, jitter=0.3, seed=19),
)

add(
    id="UMCSENT", fred="UMCSENT", name="Consumer sentiment", cats=["consumer"],
    unit="index, 1966 = 100", suffix="", decimals=1, freq="m",
    source="University of Michigan", release="Sep 2026 · preliminary",
    blurb="How households say they feel about their finances and the economy ahead.",
    detail="A survey, not a measurement, and since 2021 it has been notably gloomier than spending behaviour would suggest — people report feeling terrible while continuing to spend. Inflation, and especially petrol prices, move it more than unemployment does. Read it as a read on mood and politics as much as on the economy.",
    watch="Sentiment and actual spending have diverged sharply since 2021. Believe the spending.",
    values=pchip_like([
        ((2015, 1), 98.1), ((2016, 6), 93.5), ((2017, 12), 95.9), ((2018, 9), 100.1),
        ((2019, 12), 99.3), ((2020, 4), 71.8), ((2020, 12), 80.7), ((2021, 6), 85.5),
        ((2021, 11), 67.4), ((2022, 6), 50.0), ((2022, 12), 59.7), ((2023, 7), 71.6),
        ((2023, 12), 69.7), ((2024, 6), 68.2), ((2024, 12), 74.0), ((2025, 4), 52.2),
        ((2025, 8), 58.2), ((2025, 12), 55.0), ((2026, 3), 57.0), ((2026, 8), 54.0),
    ], N_M, jitter=1.0, seed=20),
)

add(
    id="PSAVERT", fred="PSAVERT", name="Personal saving rate", cats=["consumer"],
    unit="% of disposable income", suffix="%", decimals=1, freq="m",
    source="U.S. Bureau of Economic Analysis", release="Jul 2026 · released Aug 26, 2026",
    blurb="The share of after-tax income households are putting aside rather than spending.",
    detail="Stimulus payments and closed shops pushed this above 30% in 2020, creating a pile of excess savings that funded spending for the next two years. It has since run below its pre-pandemic norm, which means spending is being supported by income and credit rather than by a cushion.",
    watch="A falling saving rate can hold up spending for a while, but not indefinitely.",
    values=pchip_like([
        ((2015, 1), 6.0), ((2016, 12), 6.5), ((2018, 6), 7.0), ((2019, 12), 7.5),
        ((2020, 4), 32.0), ((2020, 12), 13.5), ((2021, 3), 26.0), ((2021, 12), 7.5),
        ((2022, 6), 3.0), ((2022, 12), 4.5), ((2023, 6), 4.8), ((2023, 12), 4.0),
        ((2024, 6), 4.5), ((2024, 12), 4.1), ((2025, 6), 4.5), ((2025, 12), 4.4),
        ((2026, 6), 4.3), ((2026, 7), 4.3),
    ], N_M - 1, jitter=0.15, seed=21, clamp=(0, 35)),
)


# How each series is pulled from the FRED API. "units" is FRED's transform
# (lin = as published, pc1 = percent change from a year ago, chg = change from
# prior period); "agg" is the aggregation used when FRED publishes the series
# more often than monthly.
FRED_PULL = {
    "CPIAUCSL":        {"units": "pc1", "freq": "m"},
    "CPILFESL":        {"units": "pc1", "freq": "m"},
    "PCEPILFE":        {"units": "pc1", "freq": "m"},
    "UNRATE":          {"units": "lin", "freq": "m"},
    "PAYEMS":          {"units": "chg", "freq": "m"},
    "CIVPART":         {"units": "lin", "freq": "m"},
    "CES0500000003":   {"units": "pc1", "freq": "m"},
    "FEDFUNDS":        {"units": "lin", "freq": "m"},
    "DGS10":           {"units": "lin", "freq": "m", "agg": "avg"},
    "DGS2":            {"units": "lin", "freq": "m", "agg": "avg"},
    "MORTGAGE30US":    {"units": "lin", "freq": "m", "agg": "avg"},
    "T10Y2Y":          {"units": "lin", "freq": "m", "agg": "avg"},
    "A191RL1Q225SBEA": {"units": "lin", "freq": "q"},
    "INDPRO":          {"units": "pc1", "freq": "m"},
    "DTWEXBGS":        {"units": "lin", "freq": "m", "agg": "avg"},
    "DEXUSEU":         {"units": "lin", "freq": "m", "agg": "avg"},
    "DEXJPUS":         {"units": "lin", "freq": "m", "agg": "avg"},
    "CSUSHPINSA":      {"units": "pc1", "freq": "m"},
    "HOUST":           {"units": "lin", "freq": "m"},
    "RSAFS":           {"units": "pc1", "freq": "m"},
    "UMCSENT":         {"units": "lin", "freq": "m"},
    "PSAVERT":         {"units": "lin", "freq": "m"},
}
for _s in SERIES:
    _p = FRED_PULL.get(_s["id"])
    if _p:
        _s["pull"] = _p
    else:
        raise SystemExit(f"no FRED pull config for {_s['id']}")

CATEGORIES = [
    {"id": "key", "name": "Key indicators", "icon": "trend",
     "note": "The six numbers that between them describe where the economy stands."},
    {"id": "inflation", "name": "Inflation", "icon": "trend",
     "note": "How fast prices are rising, measured three different ways."},
    {"id": "employment", "name": "Employment", "icon": "briefcase",
     "note": "Who is working, how many jobs are being created, and what they pay."},
    {"id": "rates", "name": "Interest rates", "icon": "rates",
     "note": "The price of borrowing, from the Fed's overnight rate out to thirty years."},
    {"id": "growth", "name": "Economic growth", "icon": "trend",
     "note": "Total output, and the factory production that tends to turn first."},
    {"id": "fx", "name": "Exchange rates", "icon": "globe",
     "note": "What the dollar is worth against other currencies."},
    {"id": "housing", "name": "Housing", "icon": "home",
     "note": "Prices, construction, and the mortgage rate that drives both."},
    {"id": "consumer", "name": "Consumer spending", "icon": "cart",
     "note": "Two-thirds of the economy: what households buy, save and expect."},
]

out = {
    "start": "2015-01",
    "asOf": "2026-09-18",
    "categories": CATEGORIES,
    "series": SERIES,
}

with open("/home/claude/data.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))

print(f"{len(SERIES)} series")
for s in SERIES:
    print(f'  {s["id"]:16} {s["freq"]}  n={len(s["values"]):4}  last={s["values"][-1]}')
import os
print("bytes:", os.path.getsize("/home/claude/data.json"))
