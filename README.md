# Real Wages, Real Lives — Australia's Cost-of-Living Story

> **Group Final Portfolio — UTS 36104 Data Visualisation & Narrative, Assignment 3 (2026)**
>
> *"Between late 2023 and the end of 2025, the headline number said wages were growing. The lived reality said otherwise."*

[![Streamlit App](https://img.shields.io/badge/Live%20App-Streamlit%20Cloud-FF4B4B?logo=streamlit&logoColor=white)](https://group10datavisualisation.streamlit.app/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![ABS Data](https://img.shields.io/badge/Data-Australian%20Bureau%20of%20Statistics-003087)](https://www.abs.gov.au/)

---

## About this Portfolio

This repository is our **Group Final Portfolio** for UTS 36104 — *not a written report*. It is a polished, public-facing deliverable: a live Streamlit dashboard plus the documentation required to operate, audit, and extend it. Everything here is designed so that **another team could clone the repo, read this README, and continue the work with confidence**.

| Deliverable | Where to find it |
|---|---|
| **Live dashboard** | Streamlit Cloud — link at top of repo |
| **Video walkthrough (3 min)** | Submitted as a separate attachment (`Video_Walkthrough.mov`) · narrated tour of the **three advanced features**, framed so the tutor can score on **technical prowess, accuracy, and relevance** |
| **Technical documentation** | This README (sections 1–8) + Data Dictionary in §4 |
| **Slide deck (Persuasion Pitch)** | `docs/` directory · pitched live in class 13-May-2026 |
| **EDA notebook** | `eda/` and `wage_inflation_rebuild.ipynb` |
| **Source data + provenance** | `data/` + §8 Credits & Data Provenance |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Narrative Arc & Stakeholder Design](#2-narrative-arc--stakeholder-design)
3. [Project Structure](#3-project-structure)
4. [Data Dictionary](#4-data-dictionary)
5. [Advanced Features (≥ 3 Required)](#5-advanced-features--3-required)
6. [Visual & Design Principles](#6-visual--design-principles)
7. [Running Locally](#7-running-locally)
8. [Credits & Data Provenance](#8-credits--data-provenance)

---

## 1. Project Overview

This project transforms four raw ABS spreadsheets into a single persuasive scrollytelling narrative about Australia's cost-of-living crisis. It is **not a status dashboard** — every visual choice is subordinated to a human-centred argument directed at a specific persona.

| Item | Detail |
|---|---|
| **Subject** | Wage growth vs. inflation in Australia, 2023 Q4 → 2025 Q4 |
| **Narrative arc** | **What → So What → What Next** (executive efficiency arc) |
| **Stakeholder hat** | Australian federal Treasury / cost-of-living policy desk |
| **Tool** | Streamlit (Python) |
| **Dimensions** | Temporal (`quarter_date`) + Spatial — state (`state_code`, `latitude`, `longitude`) and LGA (`LGA_CODE11`) |
| **Visuals** | 6 interactive Plotly charts + dynamic KPI tiles (the 6th is the LGA SEIFA choropleth added after Asm3 marker feedback) |
| **Dataset grain** | Quarterly: one row per quarter × state (72 rows). Sub-state: one row per LGA (565 LGAs, ABS 2011) for the structural-disadvantage layer. |

### SILOs Addressed

| SILO | Where it is demonstrated |
|---|---|
| **SILO 1** — Justify data selection | [Section 2 (Narrative Arc)](#2-narrative-arc--stakeholder-design) & [Section 8 (Provenance)](#8-credits--data-provenance) |
| **SILO 2** — Range of visualisation techniques | [Section 5 (Advanced Features)](#5-advanced-features--3-required) & [Section 6 (Visual Principles)](#6-visual--design-principles) |
| **SILO 3** — Justify narrative tools | [Section 2 (Narrative Arc)](#2-narrative-arc--stakeholder-design) |
| **SILO 4** — Communicate to stakeholders | [Section 2 (Persona & Stories)](#2-narrative-arc--stakeholder-design) |

---

## 2. Narrative Arc & Stakeholder Design

### Chosen Arc — *What → So What → What Next*

We chose the **executive efficiency arc** because our primary stakeholder (Treasury analyst) needs to reach a conclusion quickly and defend it under Q&A. The arc is implemented as five sequential chapters, each gated behind a consistent chapter-band element that encodes the arc stage in a colour-coded pill:

| Chapter | Arc stage | Title | Key insight delivered |
|---|---|---|---|
| Hero + TL;DR | All three | *Real Wages, Real Lives* | Single striking stat + 30-second card summary |
| 1 | **What** | The Headline Number Lies | Wage growth ≠ real wage growth; the gap has a shape |
| 2 | **What** | Eight Australias, Eight Pay Stories — *plus the LGA picture* | Spatial WPI divergence at state level; sub-state LGA disadvantage map (SEIFA IRSD) added in response to marker feedback so the cost-of-living pressure layer is visible at the resolution decisions actually land on |
| 3 | **So What** | Where the Money Actually Went | Housing CPI is the dominant driver of lived-cost pain |
| 4 | **What Next** | When Do Real Wages Recover? | Parametric projection — reader sets the recovery conditions |
| 5 | **What Next** | Findings and Next Steps for Treasury | Five dataset-anchored briefing points, each pairing a number from Chapters 1–4 with an analyst-framed suggested next step |

### User Persona

**Persona: Alex, Senior Policy Analyst, Treasury Cost-of-Living Desk**

- **Goals:** Understand the real income trajectory of Australian workers to brief the Minister; identify which states need targeted support; model scenarios against RBA forecasts.
- **Pain points:** Headline WPI/CPI releases tell an incomplete story; sub-category data is buried in ABS spreadsheets; no single view connects wage, inflation, and geography.
- **Behaviour:** Skims for the "so what" in under 60 seconds; drills into supporting charts when challenged; exports data for internal slide decks.

### User Stories & Acceptance Criteria

| # | User Story | Acceptance Criteria | Definition of Done |
|---|---|---|---|
| US-1 | As Alex, I want to see the gap between wage growth and inflation on one axis, so I can brief the Minister on the real income trajectory. | Chart shows WPI QoQ, CPI QoQ, and real-wage-delta simultaneously with clear legend. | Chapter 1 national timeline renders with three traces and a highlighted selected quarter. |
| US-2 | As Alex, I want to compare WPI across all states for any given quarter, so I can identify where targeted support is most needed. | Map and ranked bar update when I change the quarter slider. | Sidebar slider drives both the geo-bubble map and the horizontal bar in Chapter 2. |
| US-3 | As Alex, I want to understand *which* CPI sub-categories drove inflation, so I can tie policy levers to specific line items. | Housing, food, and transport CPI are separated and compared to the headline CPI. | Chapter 3 multi-line chart renders with at least 3 sub-category traces and a pull-quote citing cumulative impacts. |
| US-4 | As Alex, I want to model alternative wage/inflation scenarios for the next 2 years, so I can stress-test RBA forecasts. | Sliders produce a projected cumulative real-wage line and compute when (if ever) the recovery target is crossed. | Chapter 4 what-if chart updates on every slider interaction; verdict text is dynamically generated. |
| US-5 | As a general reader, I want to navigate directly to any chapter, so I don't have to scroll through content I've already read. | Sticky chapter navigation pills visible at all times. | Nav bar remains fixed to the top of the viewport and anchor links jump to correct chapters. |

---

## 3. Project Structure

```
DataVisual_Asm3/
│
├── app.py                    # Main Streamlit application
│   ├── Constants & Palette   # WCAG AA-compliant editorial colour tokens
│   ├── Page config & CSS     # Scrollytelling overrides, typography, component styles
│   ├── Data loading          # @st.cache_data loader + derived column computation
│   ├── Chart helpers         # _apply_chart_theme(), kpi_card(), tldr_card(), chapter_header()
│   └── Sections (chapters)   # One function per chapter — main() calls them top-to-bottom
│       ├── section_hero()
│       ├── section_tldr()
│       ├── section_what_national()   ← Chapter 1 · Context-Aware Filtering
│       ├── section_what_state()      ← Chapter 2 · Visual Tooltips + Spatial
│       ├── section_so_what_drivers() ← Chapter 3 · Narrative Scrollytelling
│       ├── section_what_next_whatif()← Chapter 4 · What-If Parameterization
│       └── section_call_to_action()  ← Chapter 5 · CTA
│
├── data/
│   ├── wage_inflation.csv          # Final enriched dataset (72 rows × 15 cols) — ready to use
│   ├── lga_boundaries_2011.json    # ABS 2011 LGA GeoJSON — 565 features, drives Ch2 LGA choropleth
│   ├── lga_seifa_2011.json         # ABS 2011 SEIFA IRSD scores by LGA — matched 1:1 to boundary file
│   ├── 634501.xlsx                 # ABS WPI Table 1 — national, sector breakdown
│   ├── 634502b.xlsx                # ABS WPI Table 2b — by state, all sectors
│   ├── 6401017.xlsx                # ABS CPI Table 17 — by capital city (reference)
│   └── 6401018.xlsx                # ABS CPI Table 18 — by sub-group, 8-city average
│
├── eda/                      # EDA outputs & exploratory notebooks
├── docs/                     # Slide deck + supporting strategy artefacts
├── assets/                   # Static images / icons used by the app
│
├── .streamlit/
│   └── config.toml           # Custom design system (palette, font, server settings)
│
├── notebook.ipynb            # Light-weight EDA notebook
├── wage_inflation_rebuild.ipynb  # Build script — regenerates wage_inflation.csv from raw xlsx
├── requirements.txt          # Python dependencies (pinned minimum versions)
├── .gitignore
└── README.md                 # This file
```

### Key Architectural Decisions

- **One `app.py`, one file.** The entire narrative is a single Python module so the Streamlit Cloud deployment is a one-click operation with zero additional config.
- **Section functions = chapters.** `main()` reads top-to-bottom like a story outline, not a dashboard router. Adding a new chapter is adding one function call.
- **`@st.cache_data` on load.** The CSV is read and transformed once; all interactive reruns (slider changes) skip I/O entirely.
- **Long-format CSV.** The final dataset uses long format (one row per quarter × state) so Plotly, `st.map`, and Pandas work without reshaping at render time.

---

## 4. Data Dictionary

**File:** `data/wage_inflation.csv` · **Shape:** 72 rows × 15 columns · **Coverage:** 2023 Q4 → 2025 Q4

| Column | Type | Description | Source |
|---|---|---|---|
| `quarter_date` | `date` (ISO 8601) | First day of the quarter, e.g. `2024-03-01`. Use as the time axis. | Derived |
| `quarter` | `str` | Human-readable label, e.g. `2024 Q1`. Good for chart tick labels. | Derived |
| `year` | `int` | Calendar year (2023–2025). | Derived |
| `quarter_num` | `int` | ABS quarter convention: Q1 = March, Q2 = June, Q3 = Sep, Q4 = Dec. | Derived |
| `state_code` | `str` | Short code: `NSW`, `VIC`, `QLD`, `SA`, `WA`, `TAS`, `NT`, `ACT`. | Constant |
| `state_name` | `str` | Full state/territory name. | Constant |
| `latitude` | `float` | Capital-city latitude for mapping (e.g. Sydney = −33.87 for NSW). | Constant |
| `longitude` | `float` | Capital-city longitude. | Constant |
| `wage_index` | `float` | **Wage Price Index** for that state — Original series, total hourly rates excl. bonuses, Private + Public, all industries. Re-based Sep 2008 = 100. **The only column that varies by state.** | `634502b.xlsx` |
| `inflation_rate` | `float` | National CPI **All Groups** QoQ % change, weighted 8-capital-city average. | `6401018.xlsx` |
| `wage_growth` | `float` | National WPI QoQ % change, Private + Public, all industries — Original (not seasonally adjusted). | `634501.xlsx` |
| `real_wage_growth` | `float` | `wage_growth − inflation_rate`. Positive = real purchasing power increasing; negative = declining. | Computed |
| `food` | `float` | National CPI **Food and non-alcoholic beverages** QoQ % change. | `6401018.xlsx` |
| `housing` | `float` | National CPI **Housing** QoQ % change. | `6401018.xlsx` |
| `transport` | `float` | National CPI **Transport** QoQ % change. | `6401018.xlsx` |
| `cum_real_wage` | `float` | Running cumulative sum of `real_wage_growth` from series start. Added at load time. | Computed in `app.py` |
| `real_sign` | `str` | `"positive"` / `"negative"` / `"zero"` — used for conditional bar colouring. | Computed in `app.py` |

> **Note on `wage_growth` (Original vs Seasonally Adjusted):** The Original ABS series is used because it matches the headline numbers in ABS media releases and is easier to explain to a general audience. Seasonal noise — a Q3 spike due to annual award-rate decisions — is real and expected, not a data error. If a smoother trend line is needed, swap to the Seasonally Adjusted series from `634501.xlsx`.

### LGA layer — `lga_boundaries_2011.json` + `lga_seifa_2011.json`

A second, sub-state dataset drives the LGA choropleth in Chapter 2. The two files are a **matched pair** — both originate from ABS Census 2011, both key on `LGA_CODE11` / `lga_id`, and they merge 1:1 with 564 of 565 LGAs aligning (one geo-only "no usual address" placeholder is intentionally unmatched).

| File | Records | What it contains |
|---|---|---|
| `lga_boundaries_2011.json` | 565 GeoJSON features | Polygon geometry per LGA + properties `STATE_CODE`, `LGA_CODE11`, `LGA_NAME11`. ABS 2011 ASGS boundaries. |
| `lga_seifa_2011.json` | 565 records | SEIFA **IRSD** (Index of Relative Socio-Economic Disadvantage) by LGA. Fields: `lga_id`, `lga_name`, `state`, `score`, `national_decile`, `national_percentile`, `state_decile`, `state_percentile`, `state_rank`, `national_rank`, `population`. Lower IRSD score = more disadvantaged. |

**Why 2011 vintage?** The two files are a matched pair from a single Census; using a newer 2021 SEIFA against 2011 boundaries (or vice versa) would break the join because of post-2016 NSW LGA amalgamations. The IRSD is treated as a *structural* indicator — the relative disadvantage ranking of LGAs is comparatively stable across vintages, even if the absolute score moves. The chart subtitle and on-page caption call out the vintage so a careful reader can weigh that tradeoff.

### Joining Strategy — The Enrichment Layer (DI/HD)

The key insight driving the dataset design: **WPI is published per state, but CPI sub-categories are only available at the national level.**

1. **WPI per state** pulled from `634502b.xlsx` (NSW, VIC, QLD, SA, WA, TAS, NT, ACT) → spatial dimension.
2. **National CPI metrics** (All Groups, Food, Housing, Transport) pulled from `6401018.xlsx` → single national series per quarter.
3. **National WPI QoQ %** pulled from `634501.xlsx`.
4. **Broadcast** national CPI/WPI values across all 8 state rows for each quarter (long-format pattern). Values repeat per state within a quarter — this is correct and expected.
5. **Capital-city lat/long** attached to each state so map libraries work without additional joins.
6. **9 most recent quarters** selected (2023 Q4 → 2025 Q4) for a clean 72-row dataset with sufficient trend length.

---

## 5. Advanced Features (≥ 3 Required)

All four brief-required advanced features are implemented. The **video walkthrough (`Video_Walkthrough.mov`, submitted as a separate attachment)** tours each one in turn — narrated to direct the tutor's scoring across the three official rubric dimensions: **technical prowess**, **accuracy**, and **relevance** to the narrative.

### ✅ 1. Context-Aware Filtering
**Where:** In-chapter `st.select_slider` rendered at the top of Chapter 1 ("Spotlight quarter — drives Chapters 1–3"). A scope note above the slider names every downstream chart it touches: the highlighted band on the timeline (Chapter 1), the geo-bubble map and ranked bar chart (Chapter 2), and the cost-driver pull-quote (Chapter 3). Earlier marker feedback flagged a sidebar version of this slider as confusing because the global placement implied document-wide scope; we kept the single-source-of-truth pattern but moved the control out of the sidebar and labelled its scope on the page.

**How:** `section_what_national()` now renders the slider as its first widget and returns the selected quarter; `main()` threads the returned value into `section_what_state()` and `section_so_what_drivers()`. Streamlit's reactive model still reruns every downstream section on slider movement — there is no global state container or manual callback wiring.

**Scoring lens (per video):**
- *Technical prowess* — single source of truth (`selected_quarter`) is returned from one chapter and threaded into two more; reactive propagation, no callbacks, and the explicit scope note resolves the marker's earlier confusion finding.
- *Accuracy* — slider values are pinned to the actual `quarter_date` values in the dataset, so no off-by-one or interpolated quarters are possible.
- *Relevance* — Alex (Treasury) flips quarters to brief the Treasurer on the "most recent print"; the in-chapter placement mirrors how the briefing actually happens (the analyst flips the quarter on the slide they're looking at, not in a side panel).

### ✅ 2. Visual Tooltips / Hover Cards
**Where:** Every Plotly chart (6 charts total — includes the LGA SEIFA choropleth added in Chapter 2).

**How:** Custom `hovertemplate` strings on every trace expose multi-field hover cards: e.g. the geo-bubble map shows state name, WPI, QoQ wage growth, QoQ inflation, and real-wage delta in a single hover card. No default Plotly tooltip is used.

**Scoring lens (per video):**
- *Technical prowess* — bespoke `hovertemplate` strings with HTML/format specifiers; no library defaults retained.
- *Accuracy* — every value displayed in hover is the same value used to draw the mark — no separate hover lookups that could drift.
- *Relevance* — hover surfaces the *cross-metric context* (WPI, CPI, real delta) the persona needs on demand, without cluttering the canvas.

### ✅ 3. Narrative Scrollytelling
**Where:** The entire page layout.

**How:** Sticky chapter-navigation pills (pure CSS `position: sticky`) anchor-link to five named chapters. Each chapter uses a consistent `chapter_header()` component that renders an arc-stage pill (colour-coded by What/So What/What Next), a chapter number, and an opening paragraph before the visual. The page reads top-to-bottom like a long-form article, not a tabbed dashboard.

**Scoring lens (per video):**
- *Technical prowess* — sticky CSS nav, ID-anchored chapter headers, and a reusable `chapter_header()` component — implemented inside Streamlit's restricted DOM with raw CSS injection.
- *Accuracy* — chapter ordering enforces the *What → So What → What Next* arc; the user can't accidentally consume Chapter 4's call-to-action before Chapter 1's evidence.
- *Relevance* — the arc is the *persuasion vehicle*: the layout is the argument, not just decoration.

### ✅ 4. What-If Parameterization
**Where:** Chapter 4 — "When Do Real Wages Recover?"

**How:** Three `st.slider` / `st.number_input` controls (hypothetical quarterly wage growth, hypothetical inflation, recovery target %) project a cumulative real-wage line 8 quarters beyond the last actual data point. Three preset scenario buttons (RBA-aligned, Optimistic, Pessimistic) write to `st.session_state` and trigger a `st.rerun()` so sliders and chart stay in sync. A dynamically generated verdict sentence computes the exact quarter the recovery target is crossed (or declares it unreachable).

**Scoring lens (per video):**
- *Technical prowess* — `st.session_state` + preset buttons + `st.rerun()` keep sliders, chart, and verdict text in lock-step; no stale UI.
- *Accuracy* — projection is computed from the *actual* last cumulative real-wage value, not a hard-coded baseline, so the forward line continues the history seamlessly.
- *Relevance* — Alex's exact ask: "stress-test the RBA forecast." The preset buttons make the RBA scenario a one-click comparison.

---

## 6. Visual & Design Principles

### Brand & Visual Identity

The dashboard adopts the **NSW Government masterbrand** and visual identity system — used for the header banner, logo, and overall colour/typography treatment — to align the presentation with the intended audience of NSW Treasury and to reflect established government communication standards. The use of official branding, colour palettes and accessible design principles supports consistency, credibility and recognisability, in line with NSW Government branding and digital design guidelines.

Visual identity assets and guidance obtained from: <https://www.nsw.gov.au/branding>.

### Gestalt Principles Applied

| Principle | Implementation |
|---|---|
| **Similarity** | All KPI tiles share the same `.kpi-card` component; all chapter bands share the same layout. |
| **Proximity** | Pull-quote always immediately follows its parent chart, not separated by whitespace. |
| **Figure/Ground** | Warm off-white `#fafaf7` paper background gives charts a clear foreground plane. |
| **Continuation** | The what-if projection line visually bridges from the last actual data point so the two series read as one continuous story. |

### Pre-Attentive Attributes

- **Colour** — Wage = steel blue `#2563eb`; Inflation = alarm red `#dc2626`; Real wage positive = green `#059669`; negative = red. Amber `#f59e0b` highlights the selected quarter.
- **Size** — Geo-bubble map uses bubble size AND colour to encode WPI (redundant encoding for colour-blind accessibility).
- **Position** — Horizontal bar chart in Chapter 2 ranks states by WPI so the ordering is immediately legible without reading labels.

### Accessibility

- All foreground/background colour pairs satisfy **WCAG AA contrast** (minimum 4.5:1 for body text). Verified against the `#fafaf7` paper background.
- Redundant encoding (size + colour on the map) preserves meaning for colour-blind readers.
- Hover tooltips are keyboard-accessible via Plotly's built-in focus handling.
- Typography uses Georgia (serif) at minimum 13px with 1.65× line-height for readability.

### Design System (`config.toml`)

```toml
[theme]
primaryColor        = "#dc2626"   # Alarm red — inflation signal
backgroundColor     = "#fafaf7"   # Warm off-white — editorial "paper"
secondaryBackgroundColor = "#f1ede4"  # Slightly warmer for sidebar / cards
textColor           = "#1f2937"   # Near-black charcoal
font                = "serif"     # Georgia — long-read editorial feel
```

---

## 7. Running Locally

**Prerequisites:** Python 3.11+ and `pip`.

```bash
# 1. Clone the repository
git clone https://github.com/ngolethebach/DataVisual_Asm3.git
cd DataVisual_Asm3

# 2. (Recommended) Create a virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**.

### Dependencies

| Package | Min version | Purpose |
|---|---|---|
| `streamlit` | 1.30 | App framework, layout, widgets |
| `pandas` | 2.0 | Data loading and transformation |
| `numpy` | 1.24 | Cumulative sum, `np.select` |
| `plotly` | 5.18 | All interactive charts |
| `pyarrow` | 15.0 | Streamlit data caching backend |

---

## 8. Credits & Data Provenance

### Data Sources

All data is sourced from the **Australian Bureau of Statistics (ABS)** and was last retrieved / verified in **2026**.

| File | ABS Catalogue | Table | What it contains |
|---|---|---|---|
| `634501.xlsx` | **6345.0** — Wage Price Index | Table 1 | National WPI, sector breakdown, Original + Seasonally Adjusted |
| `634502b.xlsx` | **6345.0** — Wage Price Index | Table 2b | WPI by state/territory, all sectors |
| `6401017.xlsx` | **6401.0** — Consumer Price Index | Table 17 | All Groups CPI by capital city (reference only) |
| `6401018.xlsx` | **6401.0** — Consumer Price Index | Table 18 | CPI by group/sub-group, weighted 8-capital-city average |

- **ABS WPI landing page:** https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/wage-price-index-australia/latest-release
- **ABS CPI landing page:** https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release

All percentage-change figures are **quarter-on-quarter (QoQ)**, taken directly from the ABS-published "Percentage Change from Previous Period" series — not recomputed. Mixing QoQ with YoY in the same column would introduce misleading comparisons; QoQ is used throughout for consistency.

### Team Credits

Our group operated as an **Integrated Studio** — a Code Track on GitHub and a Design & Strategy Track on SharePoint/Teams — with shared accountability for the final portfolio. Roles below are drawn from the OCEAN Persona framework defined in the Miro board (Frame 3 — OCEAN Persona Roles Assignment).

#### Code Track

| # | Member | Role | OCEAN Trait | Key Contributions |
|---|---|---|---|---|
| 1 | **Le The Bach (Jason) Ngo** | The Developer | High Conscientiousness | Owner of the Streamlit application end-to-end — `app.py`, deployment to Streamlit Cloud, scrollytelling CSS, and the wiring of all four advanced feature implementations; established the GitHub repository and project folder structure; authored the design system v1 (palette, typography, accessibility baseline); ran design reviews with the Code Track to iterate on feasibility; **post-marker-feedback iteration** — implemented the Chapter 2 sub-state LGA SEIFA choropleth (565 LGAs, ABS 2011 boundaries) with jurisdiction filter, view-mode toggle, population-by-decile bar, and the paired most/least-disadvantaged extremes tables; reworked Chapter 5 recommendations to be dataset-driven; final bug fixes and polish before submission. |
| 2 | **Avanish** | The Architect — Technical Documentation Lead | High Conscientiousness | **Built the technical document** (this README) so the portfolio reads as a polished, public-facing artefact that another team could pick up with confidence; sourced and validated the 2024+ ABS dataset with temporal and spatial dimensions; built the data cleaning pipeline in Python/Pandas; engineered the `real_wage_growth` column and validated outputs; finalised the Data Dictionary and provenance tables; uploaded the enriched clean dataset to GitHub and handed off to the visual team. |
| 3 | **Ha Anh (Hayden) Nguyen** | Quant Analyst — EDA Lead | Conscientiousness, Openness | **Built the EDA** (`eda/`, `notebook.ipynb`) that helped the team understand the dataset's shape and the story it was telling: statistical outliers, distribution checks, category drivers (which CPI sub-categories drive headline inflation), state-level wage divergence, and the relationship between wage growth and inflation; wrote the insight summaries that seed each chapter's pull-quote; validated the merged dataset; ran an accessibility audit on the draft visuals; **post-marker-feedback iteration** — added the new **LGA (sub-state) feature** in Chapter 2: sourced and validated the matched-pair ABS 2011 SEIFA IRSD + LGA boundary datasets (`data/lga_seifa_2011.json`, `data/lga_boundaries_2011.json`), specified the IRSD-by-LGA narrative and the most/least-disadvantaged framing, and co-produced (with Robin) a dedicated **video walkthrough** of the LGA layer explaining how the sub-state disadvantage view complements the national WPI/CPI story. |

#### Strategy Track

| # | Member | Role | OCEAN Trait | Key Contributions |
|---|---|---|---|---|
| 4 | **Robin (Ngoc) Nguyen** | UI/UX Artist — Slides & Presentation | Agreeableness, Extraversion | **Prepared the slide deck and presentation** alongside Lynette; produced SharePoint wireframes and the WCAG-compliant colour palette that informed the design system; built high-fidelity wireframes for all four key visuals; authored the storyboard mapping the narrative arc to the screen sequence; ran design reviews with the Code Track on feasibility; wrote the design spec for each of the three advanced features; **post-marker-feedback iteration** — co-produced (with Hayden) the updated **video walkthrough** for the new Chapter 2 LGA feature, narrating the sub-state SEIFA disadvantage view and how it slots into the broader wage/inflation story. |
| 5 | **Ishita Chettri** | The Orator — Video Walkthrough Lead | Extraversion, Openness | **Built the 3-minute video walkthrough** with Luke — narrated tour of the three advanced features, written and timed so the tutor scores cleanly on **technical prowess, accuracy, and relevance** per the rubric; authored the detective-style script and acceptance criteria; defined the user persona and user stories; integrated script, visuals, and pitch assets; presented to the audience on 13-May-2026. |
| 6 | **Lynette Heaney** | The Strategist — Slides & Presentation | Extraversion, Agreeableness | **Prepared the slide deck and presentation** alongside Robin; owned the final stakeholder pitch — making edits to arrive at the final draft of the PowerPoint slides, exporting visuals into the deck and adding the narrative text, rehearsing, and delivering the live pitch; contributed to the final edit of the dashboard visualisations and defined the narrative arc and story content. |
| 7 | **Ngoc Quang (Luke) Pham** | The Creator — Video Walkthrough Co-Lead | Conscientiousness | **Co-built the 3-minute video walkthrough** with Ishita — owner and creator of the on-screen visual narrative captured in the video; built Visual 1 (Real Wage Growth Timeline), Visual 2 (Category Breakdown — food/housing/transport), Visual 3 (State Comparison), and Visual 4 (What-If Scenario Slider — parameterisation); set up the spatial dimensions and the initial repository structure; collaborated to combine raw datasets into the final joined model. |


### Regenerating the Dataset

If new ABS releases become available (e.g. 2026 Q1 WPI/CPI published), the four source `.xlsx` files in `data/` can be replaced with the updated downloads. The columns, sheet structures, and series names in ABS tables are stable across releases. The `wage_inflation_rebuild.ipynb` notebook re-derives `wage_inflation.csv` from the raw files end-to-end — run it after dropping in the new xlsx files.

---

*UTS 36104 Data Visualisation & Narrative — Assignment 3 (Group Final Portfolio) · Semester 1, 2026*