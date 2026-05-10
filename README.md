# Wages vs Inflation — Team Dataset

Hey team — feel free to use **`data/wage_inflation.csv`** for the assignment. It's a single tidy long-format file that's ready to drop straight into Streamlit, Tableau, Power BI, pandas, or anything else. No further cleaning needed.

## How to run

```bash
git clone git@github.com:ngolethebach/DataVisual_Asm3.git
cd DataVisual_Asm3
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

- **File:** `data/wage_inflation.csv`
- **Shape:** 72 rows × 15 columns
- **Coverage:** 9 quarters (2023 Q4 → 2025 Q4) × 8 states/territories (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
- **Grain:** one row per `(quarter × state)` pair

## Source data (ABS)

All four source spreadsheets live in `data/` and come from the Australian Bureau of Statistics:

| File | What it contains | Used for |
|---|---|---|
| `634501.xlsx` | WPI Table 1 — national wage price index, sector breakdown | `wage_growth` (national QoQ %) |
| `634502b.xlsx` | WPI Table 2b — wage price index by state, all sectors | `wage_index` (per state) |
| `6401017.xlsx` | CPI Table 17 — All Groups CPI by capital city | (reference only — not used in final CSV) |
| `6401018.xlsx` | CPI Table 18 — CPI by group/sub-group, weighted 8-capital-city average | `inflation_rate`, `food`, `housing`, `transport` (national QoQ %) |

## Joining strategy

The key insight: **WPI is published per state, but CPI sub-categories are only published at the national level**. So we:

1. **Pulled WPI per state** from `634502b.xlsx` (NSW, VIC, QLD, SA, WA, TAS, NT, ACT) — this gives the spatial dimension.
2. **Pulled national CPI metrics** (All Groups, Food, Housing, Transport) from `6401018.xlsx` — single national series for each.
3. **Pulled national WPI QoQ % change** from `634501.xlsx`.
4. **Broadcast the national values across all 8 state rows for each quarter** — this is the "long format" pattern. Yes, the inflation/wage-growth values repeat across states within a quarter. That's correct — CPI/WPI national rates apply nationally, and long format is what mapping libraries (`st.map`, Tableau, Plotly) expect.
5. **Attached capital-city lat/long** to each state so maps work out-of-the-box.
6. **Took the most recent 9 quarters** (2023 Q4 → 2025 Q4) — enough for trend lines, and 9 × 8 = a clean 72 rows.

All percentage-change figures are **quarter-on-quarter (QoQ)**, taken directly from the ABS-published "Percentage Change from Previous Period" series — not recomputed. Mixing QoQ with YoY in the same column would make charts misleading, so we standardised on QoQ.

## Column dictionary

| Column | Type | Description | Source |
|---|---|---|---|
| `quarter_date` | date (ISO) | First day of the quarter, e.g. `2024-03-01`. Use this for time axes. | derived |
| `quarter` | string | Human-readable label, e.g. `2024 Q1`. Good for chart labels. | derived |
| `year` | int | Calendar year (2023–2025). | derived |
| `quarter_num` | int | Quarter number 1–4 (Q1 = March, Q2 = June, Q3 = Sep, Q4 = Dec — ABS convention). | derived |
| `state_code` | string | Short code: `NSW`, `VIC`, `QLD`, `SA`, `WA`, `TAS`, `NT`, `ACT`. | constant |
| `state_name` | string | Full state/territory name. | constant |
| `latitude` | float | Capital-city latitude (Sydney for NSW, Melbourne for VIC, etc.). Use for `st.map()`. | constant |
| `longitude` | float | Capital-city longitude. | constant |
| `wage_index` | float | **Wage Price Index** for that state — Original quarterly index, total hourly rates excl. bonuses, Private + Public, all industries. **This is the only column that varies by state.** | `634502b` |
| `inflation_rate` | float | National CPI **All Groups** quarter-on-quarter % change. | `6401018` col "All groups CPI" |
| `wage_growth` | float | National WPI quarter-on-quarter % change, Private + Public, all industries — **Original** (not seasonally adjusted). | `634501` |
| `real_wage_growth` | float | `wage_growth − inflation_rate`. Positive = real wages rising; negative = real wages falling. | computed |
| `food` | float | National CPI **Food and non-alcoholic beverages** QoQ % change. | `6401018` |
| `housing` | float | National CPI **Housing** QoQ % change. | `6401018` |
| `transport` | float | National CPI **Transport** QoQ % change. | `6401018` |

### Note on `wage_growth`

`wage_growth` uses the **Original** ABS series, not Seasonally Adjusted. This means:

- Pros: matches the headline numbers in ABS media releases and news articles — easier to explain to a general audience.
- Cons: contains seasonal noise (wage rises typically cluster in Q3 due to award decisions). If you build a time-series chart and notice a Q3 spike every year, that's the seasonality, not a data error.

If you need seasonally-adjusted values for a smoother trend, ask and we can swap the column.

## Quick-start examples

**Pandas:**
```python
import pandas as pd
df = pd.read_csv("data/wage_inflation.csv", parse_dates=["quarter_date"])
```

**Streamlit map (latest quarter):**
```python
latest = df[df["quarter_date"] == df["quarter_date"].max()]
st.map(latest[["latitude", "longitude"]])
```

**Time series of real wage growth:**
```python
nat = df.drop_duplicates("quarter_date")  # national values repeat per state
st.line_chart(nat.set_index("quarter_date")["real_wage_growth"])
```

**Wage index by state:**
```python
import plotly.express as px
fig = px.line(df, x="quarter_date", y="wage_index", color="state_code")
```

## How to regenerate

If the source xlsx files are updated (e.g. new ABS release), re-running the build is a single Python script. Ping me and I'll commit it to the repo.
