"""
Real Wages, Real Lives — Australia's Cost-of-Living Story (Q4 2023 → Q4 2025).

A data narrative built for the UTS Data Visualisation studio (Asm3).
Walks the audience through the gap between headline wage growth and
inflation, state by state, and asks: when do real wages actually recover?

Narrative arc: What -> So What -> What Next.
Stakeholder hat: Australian federal policymakers and the renter/working-
household audience whose real incomes the policy decisions land on.

Advanced features implemented (project brief requires >=3 of 4):
  1. Context-Aware Filtering  — sidebar quarter slider drives the map,
     the KPI tiles, and a highlighted marker on the national timeline.
  2. Visual Tooltips           — Plotly hover cards show wage index,
     inflation, and real-wage delta inline on every chart.
  3. Narrative Scrollytelling  — sectioned layout with hero, chapter
     headers, and consistent narrative-text -> visual rhythm.
  4. What-If Parameterization  — Section 4 sliders project an alternate
     wage-growth / inflation future and redraw the recovery line.

Data: data/wage_inflation.csv (see README.md for the data dictionary).
Run with:  streamlit run app.py

Visual identity:
  Design decisions (typography hierarchy, restrained colour use, WCAG AA
  contrast, calm public-sector tone) draw on the NSW Government Brand &
  Visual Identity guide:
      https://www.nsw.gov.au/nsw-government-brand
  See the PALETTE block and the global CSS section for where these
  principles are applied.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent / "data" / "wage_inflation.csv"

# LGA layer — 2011 ABS LGA boundaries paired with 2011 SEIFA (Index of
# Relative Socio-Economic Disadvantage). The pair is matched: both files
# share the same LGA_CODE11 / lga_id keys, so they merge 1:1 with no
# post-2016 amalgamation re-coding required. Vintage is called out in
# the chart subtitle and README data dictionary.
LGA_GEO_PATH   = Path(__file__).parent / "data" / "lga_boundaries_2011.json"
LGA_SEIFA_PATH = Path(__file__).parent / "data" / "lga_seifa_2011.json"

BANNER_PATH = Path(__file__).parent / "assets" / "banner.png"

# Editorial palette — wage = steel blue (calm/trust), inflation = alarm red,
# real-wage delta = green when positive / red when negative, amber for the
# selected-quarter highlight. Contrast pairs all hit WCAG AA on #fafaf7.
#
# Visual identity reference: tone, restraint, and accessibility decisions
# below are informed by the NSW Government Brand & Visual Identity guide
# (https://www.nsw.gov.au/nsw-government-brand) — specifically its guidance
# on accessible colour contrast, hierarchy, and a calm, trustworthy public-
# sector voice. Our hues differ (editorial story vs. NSW Govt master brand)
# but the contrast/legibility principles and the "clear, human, considered"
# tone are applied throughout.
PALETTE = {
    "ink": "#1f2937",
    "paper": "#fafaf7",
    "muted": "#6b7280",
    "rule": "#d1d5db",
    "wage": "#2563eb",
    "inflation": "#dc2626",
    "positive": "#059669",
    "negative": "#dc2626",
    "highlight": "#f59e0b",
    "food": "#ea580c",
    "housing": "#7c3aed",
    "transport": "#0891b2",
}

STATE_ORDER = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]


# ---------------------------------------------------------------------------
# Page config + global CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Real Wage Growth and Cost of Living Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A handful of overrides to give the page an editorial scrollytelling
# feel: narrower max-width for prose blocks, larger hero type, calmer
# section spacing. Streamlit's default container is full-bleed, which
# reads as dashboard-y; we want the page to feel like a long-read.
#
# Type hierarchy and spacing follow the NSW Government Brand & Visual
# Identity guide (https://www.nsw.gov.au/nsw-government-brand): generous
# whitespace, a single clear focal point per section, sentence-case
# headings, and a serif heading face paired with the system sans for
# body — chosen to read as considered, public-sector communication
# rather than dashboard chrome.
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.5rem; padding-bottom: 4rem; max-width: 1200px; }
      h1, h2, h3 { font-family: Georgia, "Times New Roman", serif; letter-spacing: -0.01em; }
      h1 { font-size: 3.0rem !important; line-height: 1.1; margin-bottom: 0.5rem; }
      h2 { font-size: 2.0rem !important; margin-top: 0.5rem; margin-bottom: 0.5rem; }
      h3 { font-size: 1.35rem !important; }
      a.chapter-anchor {
        display: block; position: relative; top: -90px; visibility: hidden;
      }
      /* Sticky chapter nav — scroll-spy without JS. Uses anchor links so
         the browser handles scroll. position:sticky keeps it visible while
         the reader works through long chapters. */
      .chapter-nav {
        position: sticky; top: 0; z-index: 99;
        background: rgba(250, 250, 247, 0.96);
        backdrop-filter: blur(6px);
        border-bottom: 1px solid #d1d5db;
        padding: 0.6rem 0; margin: 0 0 1.5rem 0;
        display: flex; flex-wrap: wrap; gap: 0.4rem;
        align-items: center; justify-content: flex-start;
      }
      .chapter-nav a {
        text-decoration: none; color: #374151;
        font-size: 0.78rem; font-weight: 600; letter-spacing: 0.04em;
        padding: 0.35rem 0.75rem; border-radius: 999px;
        border: 1px solid #d1d5db; background: #ffffff;
        white-space: nowrap; transition: all 0.15s ease;
      }
      .chapter-nav a:hover {
        background: #1f2937; color: #ffffff; border-color: #1f2937;
      }
      .chapter-nav .nav-label {
        font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.14em;
        color: #6b7280; margin-right: 0.5rem; font-weight: 600;
      }
      .hero-kicker {
        text-transform: uppercase; letter-spacing: 0.18em;
        color: #6b7280; font-size: 0.85rem; font-weight: 600;
        margin-bottom: 0.5rem;
      }
      .hero-stat {
        font-family: Georgia, serif; font-size: 5.5rem; line-height: 1;
        color: #dc2626; font-weight: 700; margin: 0.25rem 0 0.5rem 0;
      }
      .hero-stat .hero-stat-of {
        color: #6b7280; font-style: italic; font-weight: 500;
        font-size: 3.5rem;
      }
      .hero-stat-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
        padding: 1.6rem 1.8rem; margin-top: 0.75rem;
        border-top: 4px solid #dc2626;
      }
      .hero-stat-kicker {
        text-transform: uppercase; letter-spacing: 0.16em;
        color: #6b7280; font-size: 0.75rem; font-weight: 700;
        margin-bottom: 0.25rem;
      }
      .hero-stat-body {
        font-size: 1rem; line-height: 1.55; color: #374151;
        margin: 0 0 0.85rem 0;
      }
      .hero-stat-foot {
        font-size: 0.88rem; color: #4b5563;
        padding-top: 0.7rem; border-top: 1px dashed #e5e7eb;
      }
      .narrative {
        font-size: 1.1rem; line-height: 1.65; color: #374151;
        max-width: 65ch;
      }
      /* Report-metadata strip under the hero lede. Fills the visual gap
         between the (shorter) prose column and the (taller) hero stat
         card to its right, and gives the page a formal report-front-
         matter feel — period, coverage, sources up top. */
      .report-meta {
        margin-top: 1.6rem; padding-top: 1.1rem;
        border-top: 1px solid #e5e7eb;
        display: grid; grid-template-columns: max-content 1fr;
        gap: 0.55rem 1.5rem;
        max-width: 60ch;
      }
      .report-meta dt {
        margin: 0; align-self: center;
        text-transform: uppercase; letter-spacing: 0.12em;
        color: #6b7280; font-weight: 700; font-size: 0.7rem;
        font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
      }
      .report-meta dd {
        margin: 0; align-self: center;
        color: #1f2937; font-family: Georgia, serif;
        font-size: 0.95rem; line-height: 1.45;
      }
      .chapter-lede {
        font-size: 1.12rem; line-height: 1.7; color: #374151;
        margin: 0.4rem 0 1.25rem 0;
      }
      .chapter-lede em { color: #1f2937; }
      .pull-quote {
        border-left: 4px solid #f59e0b; padding-left: 1rem;
        font-style: italic; color: #1f2937; font-size: 1.15rem;
        margin: 1.5rem 0; max-width: 60ch;
      }
      /* TL;DR card — compact insight tile for the executive-summary row.
         Three across, equal height, with a coloured top stripe so the row
         scans in <5 seconds. */
      .tldr-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 1.1rem 1.2rem; height: 100%; position: relative;
        overflow: hidden;
      }
      .tldr-card::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0;
        height: 4px; background: var(--stripe, #1f2937);
      }
      .tldr-num {
        font-family: Georgia, serif; font-size: 0.78rem; font-weight: 600;
        color: #6b7280; letter-spacing: 0.14em; text-transform: uppercase;
      }
      .tldr-headline {
        font-family: Georgia, serif; font-size: 1.25rem; font-weight: 700;
        color: #1f2937; margin: 0.25rem 0 0.5rem 0; line-height: 1.3;
      }
      .tldr-body { font-size: 0.92rem; line-height: 1.5; color: #4b5563; }
      .kpi-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 1.1rem 1.2rem; height: 100%;
      }
      .kpi-label {
        text-transform: uppercase; letter-spacing: 0.1em;
        color: #6b7280; font-size: 0.72rem; font-weight: 600;
      }
      .kpi-value {
        font-family: Georgia, serif; font-size: 2.0rem; font-weight: 700;
        color: #1f2937; margin-top: 0.2rem;
      }
      .kpi-sub { color: #6b7280; font-size: 0.85rem; margin-top: 0.2rem; }
      /* Chapter header band — a quiet horizontal rule under the chapter
         title so each section gets a decisive visual break. */
      .chapter-band {
        margin: 2.75rem 0 0.75rem 0; padding-bottom: 0.55rem;
        border-bottom: 1px solid #d1d5db;
      }
      .chapter-band .chapter-title {
        display: block; margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2.1rem; font-weight: 700; color: #1f2937;
        letter-spacing: -0.015em; line-height: 1.15;
      }
      .section-divider {
        height: 1px; background: #d1d5db; margin: 3rem 0 2rem 0;
        border: none;
      }
      .policy-rec {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
        padding: 1.5rem 1.75rem; margin: 1rem 0;
      }
      .policy-rec .rec-label {
        font-family: Georgia, "Times New Roman", serif;
        color: #059669; font-size: 1.25rem; font-weight: 700;
        margin-bottom: 0.5rem; line-height: 1.3;
      }
      .policy-rec .rec-body {
        font-size: 0.95rem; line-height: 1.6; color: #374151;
      }
      /* LGA extremes tables — paired cards under the choropleth so the
         most/least-disadvantaged LGAs are immediately legible without
         hovering 500+ polygons. The faint coloured top border echoes
         the choropleth scale ends (red for low score, blue for high). */
      .lga-table-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 1rem 1.1rem 0.4rem 1.1rem; margin: 0.6rem 0 1rem 0;
      }
      .lga-table-card--low  { border-top: 4px solid #dc2626; }
      .lga-table-card--high { border-top: 4px solid #1e3a8a; }
      .lga-table-card .lga-table-title {
        text-transform: uppercase; letter-spacing: 0.12em;
        color: #6b7280; font-size: 0.72rem; font-weight: 700;
        margin-bottom: 0.55rem;
      }
      table.lga-table {
        width: 100%; border-collapse: collapse;
        font-family: Georgia, serif; font-size: 0.92rem;
      }
      table.lga-table th, table.lga-table td {
        padding: 0.32rem 0.4rem; border-bottom: 1px dashed #e5e7eb;
        color: #1f2937;
      }
      table.lga-table th {
        font-size: 0.7rem; text-transform: uppercase;
        letter-spacing: 0.08em; color: #6b7280; font-weight: 700;
      }
      table.lga-table tr:last-child td { border-bottom: none; }
      /* Polish: subtle hover-lift on the KPI/LGA cards so the page feels
         responsive without leaning on motion. Transform + shadow only —
         no colour shift, which would compete with the choropleth scale. */
      .kpi-card, .lga-table-card, .tldr-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .kpi-card:hover, .lga-table-card:hover, .tldr-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.07);
      }
      /* Entrance animation for the LGA section — a one-off fade-up so
         the chapter's third zoom-level reveals itself rather than just
         appearing under the state map. Runs once on page load / rerun. */
      @keyframes lgaFadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      .lga-section-enter {
        animation: lgaFadeUp 0.55s ease-out both;
      }
      .lga-section-enter--delay-1 { animation-delay: 0.10s; }
      .lga-section-enter--delay-2 { animation-delay: 0.20s; }
      .lga-section-enter--delay-3 { animation-delay: 0.30s; }
      /* Slider scope note — wraps the spotlight-quarter slider in
         Chapter 1 so its scope is explicit on the page. The amber-bar
         left border echoes the highlight colour used to mark the
         selected quarter on the timeline, visually linking the two. */
      .slider-scope-note {
        background: #fffbeb; border: 1px solid #fde68a;
        border-left: 4px solid #f59e0b; border-radius: 6px;
        padding: 0.9rem 1.1rem; margin: 0.5rem 0 0.75rem 0;
        display: flex; flex-direction: column; gap: 0.25rem;
      }
      .slider-scope-note .slider-scope-kicker {
        text-transform: uppercase; letter-spacing: 0.14em;
        color: #92400e; font-size: 0.7rem; font-weight: 700;
      }
      .slider-scope-note .slider-scope-body {
        font-size: 0.92rem; line-height: 1.55; color: #374151;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Read wage_inflation.csv and add the derived columns the charts need.

    The CSV is already long-format (one row per quarter x state). We add:
      - cum_real_wage:   running-sum of real_wage_growth from the start
                         of the series, for the cumulative-impact story.
      - real_sign:       'positive' / 'zero' / 'negative' label used to
                         colour bars in the national timeline.
    Both are derived from existing columns, so the underlying data is
    untouched.
    """
    df = pd.read_csv(DATA_PATH, parse_dates=["quarter_date"])
    # Display format: "Q4 2023" reads more naturally than "2023 Q4" for
    # the audience. Built from clean integer columns, not a string parse.
    df["quarter"] = "Q" + df["quarter_num"].astype(str) + " " + df["year"].astype(str)
    # National series is identical across the 8 state rows per quarter,
    # so drop_duplicates gives us a single national timeline.
    nat = (
        df.drop_duplicates("quarter_date")
        .sort_values("quarter_date")
        .reset_index(drop=True)
    )
    nat["cum_real_wage"] = nat["real_wage_growth"].cumsum()
    # Broadcast the cumulative back onto the per-state long frame.
    df = df.merge(nat[["quarter_date", "cum_real_wage"]], on="quarter_date", how="left")
    df["real_sign"] = np.select(
        [df["real_wage_growth"] > 0, df["real_wage_growth"] < 0],
        ["positive", "negative"],
        default="zero",
    )
    return df


@st.cache_data(show_spinner=False)
def national_series(df: pd.DataFrame) -> pd.DataFrame:
    """Single-row-per-quarter view for charts that don't vary by state."""
    return (
        df.drop_duplicates("quarter_date")
        .sort_values("quarter_date")
        .reset_index(drop=True)
    )


@st.cache_data(show_spinner=False)
def load_lga_data() -> tuple[dict, pd.DataFrame]:
    """Load 2011 LGA boundaries and matched 2011 SEIFA scores.

    Returns a tuple of (geojson dict, dataframe). The geojson features
    expose ``LGA_CODE11`` in their properties; the dataframe carries the
    same code as ``lga_id`` so Plotly's ``featureidkey`` lookup joins
    cleanly. Both files originate from ABS Census 2011; we keep the
    matched pair rather than mixing vintages (post-2016 NSW LGA
    amalgamations would break the lookup against 2011 boundaries).
    """
    with open(LGA_GEO_PATH) as f:
        geo = json.load(f)

    with open(LGA_SEIFA_PATH) as f:
        seifa_raw = json.load(f)

    # The upstream SEIFA dump contains one empty record. Drop anything
    # that's missing the join key or the score we colour on.
    records = [
        r for r in seifa_raw
        if r.get("lga_id") and r.get("score")
    ]
    df = pd.DataFrame(records)
    df["lga_id"] = df["lga_id"].astype(str)
    numeric_cols = [
        "score",
        "national_decile",
        "national_percentile",
        "state_rank",
        "state_decile",
        "population",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return geo, df


# ---------------------------------------------------------------------------
# Reusable chart helpers
# ---------------------------------------------------------------------------


def _apply_chart_theme(fig: go.Figure, *, height: int = 420) -> go.Figure:
    """Common Plotly styling so every chart inherits the editorial look.

    Title and legend both want to live in the top margin, so we expand
    that margin (~100px) and pin the title to the very top while the
    horizontal legend sits just below it. Without this they collide on
    multi-series charts.
    """
    fig.update_layout(
        height=height,
        paper_bgcolor=PALETTE["paper"],
        plot_bgcolor=PALETTE["paper"],
        font=dict(family="Georgia, serif", color=PALETTE["ink"], size=13),
        margin=dict(l=20, r=20, t=100, b=50),
        title=dict(y=0.97, yanchor="top", pad=dict(t=0, b=0)),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor=PALETTE["rule"],
            font=dict(family="Georgia, serif", size=13, color=PALETTE["ink"]),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor=PALETTE["rule"],
        ticks="outside",
        tickcolor=PALETTE["rule"],
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=PALETTE["rule"],
        gridwidth=0.5,
        zeroline=True,
        zerolinecolor=PALETTE["muted"],
        zerolinewidth=1,
    )
    return fig


def kpi_card(label: str, value: str, sub: str = "") -> str:
    """Return an HTML KPI tile. Used inside st.markdown so a row of
    columns can each render one card."""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f"{sub_html}"
        f"</div>"
    )


def tldr_card(num: str, headline: str, body: str, stripe: str) -> str:
    """One tile in the TL;DR strip. The coloured top stripe lets the
    three cards scan as a unit — wage / cost-of-living / recovery."""
    return (
        f'<div class="tldr-card" style="--stripe: {stripe};">'
        f'<div class="tldr-num">{num}</div>'
        f'<div class="tldr-headline">{headline}</div>'
        f'<div class="tldr-body">{body}</div>'
        f"</div>"
    )


def chapter_header(anchor: str, title: str, lede: str) -> None:
    """Render a consistent chapter band: anchor target for the sticky nav,
    the title, and the opening paragraph.

    The invisible <a> sits 90px above the visible heading so anchor jumps
    don't bury the title under the sticky nav bar.
    """
    st.markdown(
        f'<a class="chapter-anchor" id="{anchor}"></a>'
        f'<div class="chapter-band">'
        f'<h2 class="chapter-title">{title}</h2>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="chapter-lede">{lede}</p>', unsafe_allow_html=True)


def chapter_nav() -> None:
    """Sticky pill nav linking to each chapter anchor. Browsers handle
    the scroll natively — no JS required, no Streamlit reruns."""
    items = [
        ("ch1", "1 · Real Wage Performance"),
        ("ch2", "2 · State & Territory Outcomes"),
        ("ch3", "3 · Cost Drivers"),
        ("ch4", "4 · Forecast Scenarios"),
        ("ch5", "5 · Findings & Next Steps"),
    ]
    pills = "".join(f'<a href="#{anchor}">{label}</a>' for anchor, label in items)
    st.markdown(
        f'<div class="chapter-nav"><span class="nav-label">Contents</span>{pills}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sections — one function per chapter so the narrative flow in main()
# reads top-to-bottom like an outline.
# ---------------------------------------------------------------------------


def section_hero(df: pd.DataFrame) -> None:
    """Opening: kicker, headline, lede on the left; the single most
    striking stat on the right so the row reads in a balanced sweep
    instead of leaving the right half empty."""
    nat = national_series(df)
    n_negative = int((nat["real_wage_growth"] < 0).sum())
    n_total = len(nat)
    cum_real = nat["real_wage_growth"].sum()
    period_start = nat["quarter"].iloc[0]
    period_end = nat["quarter"].iloc[-1]
    n_states = df["state_code"].nunique()

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown("# Real Wage Growth and Cost of Living Analysis")
        st.markdown(
            '<p class="narrative">'
            "Between late 2023 and the end of 2025, nominal wages continued "
            "to increase, reflecting ongoing growth in headline earnings."
            " However, this growth was outpaced by rising prices."
            f" Over {n_total} consecutive quarters, the divergence between wage growth "
            f"and inflation resulted in only a {cum_real:+.1f}% increase in real wages. "
            "This highlights a persistent gap between reported income growth "
            "and actual purchasing power — the distinction between wages "
            "as measured on paper and wages in practical, real-world terms."
            "</p>"
            '<dl class="report-meta">'
            f"<dt>Period covered</dt><dd>{period_start} — {period_end}</dd>"
            f"<dt>Coverage</dt><dd>{n_states} states &amp; territories</dd>"
            "<dt>Approach</dt><dd>Time-series analysis, jurisdiction comparison, "
            "and forward scenario projection</dd>"
            "</dl>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div class="hero-stat-card">'
            '<div class="hero-stat-kicker">Real Wage Contraction Across the Period</div>'
            f'<div class="hero-stat">{n_negative} <span class="hero-stat-of">of</span> {n_total}</div>'
            '<p class="hero-stat-body">'
            "quarters recorded real wage contraction, with wage growth failing to keep pace with inflation. "
            "During these periods, nominal income growth did not translate into improved purchasing power. "
            "This has direct policy implications. Indexation mechanisms for government payments, including "
            "rent assistance and income support, are primarily linked to headline measures. Where these "
            "measures understate cost pressures, particularly in essential categories, real payment values "
            "may erode over time."
            "</p>"
            '<div class="hero-stat-foot">'
            "Cumulative real wage growth across the period: "
            f"<strong>{cum_real:+.1f}%</strong>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )


def section_tldr(df: pd.DataFrame) -> None:
    """Three-card executive summary directly under the hero. A reader who
    only has 30 seconds gets the entire What → So What → What Next here;
    the chapters that follow are the evidence."""
    nat = national_series(df)
    cum_real = nat["real_wage_growth"].sum()
    cum_housing = nat["housing"].sum()
    last_q = nat.iloc[-1]
    leader_state_q = (
        df[df["quarter"] == last_q["quarter"]]
        .sort_values("wage_index", ascending=False)
        .iloc[0]
    )
    laggard_state_q = (
        df[df["quarter"] == last_q["quarter"]]
        .sort_values("wage_index", ascending=True)
        .iloc[0]
    )
    state_spread = leader_state_q["wage_index"] - laggard_state_q["wage_index"]

    st.markdown(
        '<p class="hero-kicker" style="margin-top:2rem;">Executive Summary</p>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(
            tldr_card(
                "The Gap",
                "Inflation constrained growth in real wage.",
                f"Over the {len(nat)}-quarter period, real wage growth totalled "
                f"<strong>{cum_real:+.1f}%</strong>. Elevated inflation "
                "substantially offset nominal wage gains, limiting improvements"
                " in household purchasing power. Thus overall improvement in "
                "real wages is yet again minimal.",
                stripe=PALETTE["wage"],
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            tldr_card(
                "The Driver",
                "Housing costs were a primary source of inflationary pressure.",
                f"Housing prices increased by <strong>{cum_housing:+.1f}%</strong> "
                "over the period, significantly exceeding the overall average. "
                "Government payments indexed to broader inflation measures "
                "did not fully keep pace with housing-related cost increases.",
                stripe=PALETTE["housing"],
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            tldr_card(
                "The Uneven Recovery",
                "Wage outcomes varied across states and territories",
                f"In {last_q['quarter']}, there was a "
                f"<strong>{state_spread:.1f}-point</strong> difference between "
                f"{leader_state_q['state_name']} and "
                f"{laggard_state_q['state_name']} on the wage index. "
                "This highlights differing labour market conditions across jurisdictions "
                "and the limitations of uniform national policy settings.",
                stripe=PALETTE["positive"],
            ),
            unsafe_allow_html=True,
        )


def section_what_national(df: pd.DataFrame) -> str:
    """What — the national picture. Wage growth vs inflation timeline,
    with a highlighted marker at the user-selected quarter.

    Renders the *spotlight-quarter* control inline at the top of the
    chapter — earlier marker feedback flagged the previous global
    sidebar slider as confusing (it implied document-wide scope when in
    fact it only drove Chapters 1–3). Returning the selected quarter
    lets Chapters 2 and 3 stay in lock-step without bringing back a
    global state container.
    """
    nat = national_series(df)
    quarters = nat["quarter"].tolist()

    chapter_header(
        anchor="ch1",
        title="1. Assessing Real Wage Performance: The National Timeline",
        lede=(
            "The Australian Bureau of Statistics (ABS) releases quarterly "
            "data on both wage growth and consumer price inflation. "
            "Together, these measures provide an indication of changes in "
            "real wages and household purchasing power. Where inflation "
            "exceeds wage growth, the purchasing power of households "
            "declines despite increases in nominal earnings."
        ),
    )

    # The story control is co-located with the chapter it lives in. The
    # callout below the slider names every downstream chapter the slider
    # touches, so its scope is explicit on the page rather than implied
    # by sidebar placement.
    st.markdown(
        '<div class="slider-scope-note">'
        '<span class="slider-scope-kicker">Story control · Chapters 1 & 2 only</span>'
        '<span class="slider-scope-body">'
        'The <strong>spotlight quarter</strong> below drives two views: '
        'the highlighted band on the national timeline (Chapter 1) and '
        'the state-level WPI snapshot (Chapter 2). Chapter 3 (cost '
        'drivers), Chapter 4 (Forecast Scenarios), and Chapter 5 '
        '(Findings) all read across the full series and are independent '
        'of this control — earlier marker feedback flagged a single-'
        'quarter snapshot as a poor fit for cumulative-driver analysis, '
        'so Chapter 3 no longer responds to this slider.'
        '</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    selected_quarter = st.select_slider(
        "Spotlight quarter (Chapters 1 & 2 only)",
        options=quarters,
        value=quarters[-1],
        key="spotlight_quarter",
    )
    sel_row = nat[nat["quarter"] == selected_quarter].iloc[0]

    # Three-line chart: wage_growth, inflation_rate, real_wage_growth.
    # The vertical band marks the quarter the reader has selected so the
    # KPIs below the chart make geographic sense at a glance.
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=nat["quarter"],
            y=nat["wage_growth"],
            mode="lines+markers",
            name="Wage growth (QoQ %)",
            line=dict(color=PALETTE["wage"], width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Wage growth: %{y:+.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=nat["quarter"],
            y=nat["inflation_rate"],
            mode="lines+markers",
            name="Inflation (QoQ %)",
            line=dict(color=PALETTE["inflation"], width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Inflation: %{y:+.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=nat["quarter"],
            y=nat["real_wage_growth"],
            name="Real wage growth (gap)",
            marker_color=[
                PALETTE["positive"]
                if v > 0
                else PALETTE["negative"]
                if v < 0
                else PALETTE["muted"]
                for v in nat["real_wage_growth"]
            ],
            opacity=0.55,
            hovertemplate=("<b>%{x}</b><br>Real wage Δ: %{y:+.1f}%<extra></extra>"),
        )
    )
    # Selected-quarter highlight: a vertical band the reader can scan to.
    fig.add_vrect(
        x0=selected_quarter,
        x1=selected_quarter,
        line=dict(color=PALETTE["highlight"], width=2, dash="dot"),
    )
    fig.update_layout(
        title=dict(
            text="Wages vs inflation — quarter-on-quarter, Australia",
            x=0,
            font=dict(size=16),
        ),
        bargap=0.45,
        yaxis_title="Per-quarter change (%)",
    )
    _apply_chart_theme(fig, height=460)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # KPI strip — these update as the reader changes the quarter.
    real_delta = sel_row["real_wage_growth"]
    delta_word = (
        "ahead of" if real_delta > 0 else "behind" if real_delta < 0 else "level with"
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            kpi_card(
                "Selected quarter",
                selected_quarter,
                "Adjust using the slider above.",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card(
                "Wage growth (QoQ)",
                f"{sel_row['wage_growth']:+.1f}%",
                "ABS Wage Price Index, all sectors.",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            kpi_card(
                "Inflation (QoQ)",
                f"{sel_row['inflation_rate']:+.1f}%",
                "ABS CPI, All Groups, weighted 8-cap-city avg.",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            kpi_card(
                "Real wage change",
                f"{real_delta:+.1f}%",
                f"Workers were {delta_word} the cost of living.",
            ),
            unsafe_allow_html=True,
        )

    return selected_quarter


def section_what_state(df: pd.DataFrame, selected_quarter: str) -> None:
    """What — the spatial picture. Map of wage index by state for the
    selected quarter, plus a horizontal-bar comparison."""
    snapshot = df[df["quarter"] == selected_quarter].copy()
    snapshot = snapshot.set_index("state_code").loc[STATE_ORDER].reset_index()

    chapter_header(
        anchor="ch2",
        title="2. State and Territory Wage Index Outcomes",
        lede=(
            "Wage Price Index outcomes vary across states and territories, "
            "reflecting differences in labour market conditions, industry composition "
            "and regional economic performance. While national averages provide a useful "
            "headline measure, jurisdiction-level results show the extent of variation "
            "across the federation. This variation is relevant for policy design, as "
            "nationally uniform settings may have different real-world effects across "
            "states and territories."
        ),
    )

    map_col, bar_col = st.columns([3, 2])

    with map_col:
        # Geo bubble map. Bubble size and colour both encode wage_index
        # — redundant encoding is intentional: it survives colour-blind
        # readers and prints in greyscale.
        fig = px.scatter_geo(
            snapshot,
            lat="latitude",
            lon="longitude",
            size="wage_index",
            color="wage_index",
            color_continuous_scale=[
                [0.0, "#dbeafe"],
                [0.5, "#3b82f6"],
                [1.0, "#1e3a8a"],
            ],
            size_max=42,
            hover_name="state_name",
            custom_data=[
                "state_code",
                "wage_index",
                "wage_growth",
                "inflation_rate",
                "real_wage_growth",
            ],
            projection="mercator",
        )
        fig.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b> (%{customdata[0]})<br>"
                "Wage Price Index: <b>%{customdata[1]:.1f}</b><br>"
                "Wage growth: %{customdata[2]:+.1f}%<br>"
                "Inflation: %{customdata[3]:+.1f}%<br>"
                "Real wage Δ: %{customdata[4]:+.1f}%<extra></extra>"
            )
        )
        fig.update_geos(
            visible=True,
            resolution=50,
            showcountries=True,
            countrycolor=PALETTE["rule"],
            showland=True,
            landcolor="#f1ede4",
            showocean=True,
            oceancolor="#e7e2d5",
            lataxis_range=[-44, -10],
            lonaxis_range=[112, 155],
        )
        fig.update_layout(
            title=dict(
                text=f"Wage Price Index by state — {selected_quarter}",
                x=0,
                y=0.97,
                yanchor="top",
                font=dict(size=16),
            ),
            coloraxis_colorbar=dict(title="WPI"),
            margin=dict(l=0, r=0, t=70, b=0),
            height=460,
            paper_bgcolor=PALETTE["paper"],
            font=dict(family="Georgia, serif", color=PALETTE["ink"]),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with bar_col:
        # Horizontal bar — same data as the map, but ranked. Maps show
        # geography; bars show ordering. Both views together is a Gestalt
        # similarity-by-position trick.
        sorted_snap = snapshot.sort_values("wage_index", ascending=True)
        fig2 = go.Figure(
            go.Bar(
                x=sorted_snap["wage_index"],
                y=sorted_snap["state_code"],
                orientation="h",
                marker=dict(
                    color=sorted_snap["wage_index"],
                    colorscale=[[0.0, "#dbeafe"], [0.5, "#60a5fa"], [1.0, "#1e3a8a"]],
                    showscale=False,
                ),
                customdata=sorted_snap[["state_name", "wage_growth"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "WPI: %{x:.1f}<br>QoQ wage growth: %{customdata[1]:+.1f}%"
                    "<extra></extra>"
                ),
                text=sorted_snap["wage_index"].map(lambda v: f"{v:.1f}"),
                textposition="outside",
            )
        )
        fig2.update_layout(
            title=dict(text="Ranked WPI", x=0, font=dict(size=16)),
            xaxis_title="Wage Price Index (Sep 2008 = 100)",
            yaxis_title="",
        )
        _apply_chart_theme(fig2, height=460)
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

    # One-line takeaway that updates with the quarter.
    leader = snapshot.loc[snapshot["wage_index"].idxmax()]
    laggard = snapshot.loc[snapshot["wage_index"].idxmin()]
    spread = leader["wage_index"] - laggard["wage_index"]
    st.markdown(
        f'<div class="pull-quote">In {selected_quarter}, '
        f"{leader['state_name']} led with a WPI of "
        f"{leader['wage_index']:.1f}, while {laggard['state_name']} "
        f"sat at {laggard['wage_index']:.1f} — a spread of "
        f"{spread:.1f} index points across the federation.</div>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Below the state line — LGA-level structural disadvantage.
    #
    # The state-level WPI numbers above tell a relatively flat story
    # (six-point spread across the federation). The LGA layer adds a
    # third zoom level: where the cost-of-living pressure actually lands.
    # SEIFA's IRSD is the ABS composite score most analysts reach for to
    # answer that question — lower score, less headroom in the household
    # budget when housing or essentials run above the average.
    # ------------------------------------------------------------------
    _render_lga_layer()


def _render_lga_layer() -> None:
    """LGA choropleth + ranked-extremes panel.

    Split out from ``section_what_state`` so the spatial scaffolding for
    the chapter reads top-to-bottom (national → state → LGA). The LGA
    layer is intentionally *not* tied to the spotlight-quarter slider:
    SEIFA is a structural snapshot (Census 2011), not a quarterly series,
    and conflating it with the slider would imply the IRSD score changes
    quarter to quarter — which it does not.

    Reader controls (jurisdiction filter, colour-encoding mode) sit
    above the map so the dense national choropleth is drillable — a
    Treasury reader looking at NSW housing pressure can isolate NSW
    without losing the national context line at the bottom.
    """
    geo_lga, df_lga = load_lga_data()

    st.markdown(
        '<div class="lga-section-enter">'
        '<h3 style="margin-top:2rem;">Below the State Line: The LGA Picture</h3>'
        '<p class="narrative">'
        "State-level WPI varies modestly — the spread across the eight "
        "jurisdictions is a few index points. The structural pressure "
        "households actually face varies far more dramatically below the "
        "state line. The choropleth below renders every Local Government "
        "Area in Australia (565 LGAs, ABS 2011 boundaries) coloured by "
        "the <strong>Index of Relative Socio-Economic Disadvantage</strong> "
        "(IRSD): lower scores indicate less headroom in the household "
        "budget — exactly the LGAs where a +7.8% cumulative housing CPI "
        "print (Chapter 3) lands hardest."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Reader controls — jurisdiction radio + view-mode radio. A radio
    # row reads faster than a dropdown for ≤9 options and keeps state
    # selection one click away from the rest of the page. The view-mode
    # radio collapses what was previously two toggles (colour encoding +
    # optional animated reveal) into one mutually-exclusive choice.
    state_order = ["All Australia", "NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
    ctrl_left, ctrl_right = st.columns([3, 2])
    with ctrl_left:
        selected_state = st.radio(
            "Jurisdiction",
            options=state_order,
            index=0,
            horizontal=True,
            key="lga_state_filter",
            help=(
                "Filter the LGA map to a single state or territory. "
                "The KPI strip, population-by-decile bar, and reveal "
                "animation all update with the selection."
            ),
        )
    with ctrl_right:
        view_mode = st.radio(
            "View mode",
            options=[
                "National decile (banded)",
                "IRSD score (continuous)",
                "▶ Animated decile reveal",
            ],
            index=0,
            horizontal=True,
            key="lga_view_mode",
            help=(
                "Banded: discrete national-decile bins (1 = most "
                "disadvantaged) — clearest policy-band reading. "
                "Continuous: raw IRSD gradient. "
                "Animated reveal: builds the map decile-by-decile so "
                "the spatial concentration of disadvantage reveals "
                "itself before the full federation is in view."
            ),
        )

    if selected_state == "All Australia":
        view_df = df_lga
    else:
        view_df = df_lga[df_lga["state"] == selected_state].copy()

    # KPI strip — dataset-derived headline numbers that update with the
    # state filter. Total LGAs / total population frame the view; the
    # bottom-3-decile pair is the policy-relevant lead (this is the
    # population that bears the cost-of-living print disproportionately).
    n_lgas       = len(view_df)
    total_pop    = int(view_df["population"].sum())
    bottom3_mask = view_df["national_decile"].between(1, 3)
    pop_bottom3  = int(view_df.loc[bottom3_mask, "population"].sum())
    share_bottom3 = (pop_bottom3 / total_pop * 100) if total_pop else 0.0
    score_min    = float(view_df["score"].min())
    score_max    = float(view_df["score"].max())
    iqr_spread   = score_max - score_min

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            '<div class="lga-section-enter lga-section-enter--delay-1">'
            + kpi_card("LGAs in view", f"{n_lgas:,}",
                       "Census 2011 boundaries")
            + "</div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            '<div class="lga-section-enter lga-section-enter--delay-1">'
            + kpi_card("Population covered", f"{total_pop/1_000_000:.2f}M",
                       "2011 usual residents")
            + "</div>",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            '<div class="lga-section-enter lga-section-enter--delay-2">'
            + kpi_card("In bottom-3 IRSD deciles", f"{share_bottom3:.1f}%",
                       f"{pop_bottom3/1_000_000:.2f}M people")
            + "</div>",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            '<div class="lga-section-enter lga-section-enter--delay-2">'
            + kpi_card("IRSD spread", f"{int(iqr_spread)} pts",
                       f"{int(score_min)} → {int(score_max)}")
            + "</div>",
            unsafe_allow_html=True,
        )

    # ----- Map -----------------------------------------------------------
    # Three view modes:
    #   * banded:     discrete national-decile bins (1..10) — easiest
    #                 read as policy bands, removes visual dominance of
    #                 outliers.
    #   * continuous: raw IRSD score, range-pinned to the *national*
    #                 min/max so a state filter doesn't rescale colours
    #                 and mislead cross-state comparison.
    #   * animated:   the same banded view but progressively reveals
    #                 deciles 1 → 10 across frames, with a play button.
    #                 Tells the "where does disadvantage cluster first?"
    #                 story without forcing a reader to read 564 polygons.
    nat_score_min = float(df_lga["score"].min())
    nat_score_max = float(df_lga["score"].max())

    # Single decile palette used by both banded and animated modes — keeps
    # the visual language identical across views so switching modes feels
    # like a lens change, not a redesign.
    decile_palette = [
        "#7f1d1d", "#b91c1c", "#dc2626", "#f87171", "#fde68a",
        "#bfdbfe", "#60a5fa", "#3b82f6", "#1d4ed8", "#1e3a8a",
    ]
    decile_colour_map = {str(i + 1): c for i, c in enumerate(decile_palette)}
    title_suffix = "Australia" if selected_state == "All Australia" else selected_state

    if view_mode.startswith("National decile"):
        view_df_banded = view_df.assign(
            decile_label=view_df["national_decile"].astype("Int64").astype(str)
        )
        fig = px.choropleth(
            view_df_banded,
            geojson=geo_lga,
            locations="lga_id",
            featureidkey="properties.LGA_CODE11",
            color="decile_label",
            category_orders={"decile_label": [str(i) for i in range(1, 11)]},
            color_discrete_map=decile_colour_map,
            hover_name="lga_name",
            custom_data=["state", "score", "national_decile", "population"],
        )
        fig.update_layout(
            legend=dict(
                title=dict(text="National IRSD decile<br>(1 = most disadvantaged)"),
                orientation="v",
                yanchor="middle", y=0.5,
                xanchor="left", x=1.02,
                font=dict(size=11),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
    elif view_mode.startswith("IRSD score"):
        fig = px.choropleth(
            view_df,
            geojson=geo_lga,
            locations="lga_id",
            featureidkey="properties.LGA_CODE11",
            color="score",
            color_continuous_scale=[
                [0.00, "#7f1d1d"],
                [0.25, "#dc2626"],
                [0.50, "#fde68a"],
                [0.75, "#60a5fa"],
                [1.00, "#1e3a8a"],
            ],
            range_color=(nat_score_min, nat_score_max),
            hover_name="lga_name",
            custom_data=["state", "score", "national_decile", "population"],
        )
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="IRSD score",
                thickness=14,
                len=0.7,
            ),
        )
    else:
        # ----- Animated decile reveal -----------------------------------
        # Build a long frame: for each k in 1..10, include every LGA in
        # view with national_decile <= k. Plotly's animation_frame then
        # gives us a play button + slider that morphs the map decile by
        # decile. Visually: red dots scatter first (the bottom decile),
        # then fill outwards through amber to deep blue.
        frames = []
        for k in range(1, 11):
            sub = view_df[view_df["national_decile"] <= k].copy()
            sub["frame"] = f"Up to decile {k}"
            sub["decile_label"] = sub["national_decile"].astype("Int64").astype(str)
            frames.append(sub)
        anim_df = pd.concat(frames, ignore_index=True)
        frame_order = [f"Up to decile {k}" for k in range(1, 11)]

        fig = px.choropleth(
            anim_df,
            geojson=geo_lga,
            locations="lga_id",
            featureidkey="properties.LGA_CODE11",
            color="decile_label",
            category_orders={
                "decile_label": [str(i) for i in range(1, 11)],
                "frame": frame_order,
            },
            color_discrete_map=decile_colour_map,
            hover_name="lga_name",
            custom_data=["state", "score", "national_decile", "population"],
            animation_frame="frame",
        )
        # On-brand play/pause controls + slider. Defaults from Plotly are
        # styled like a Jupyter widget — we restyle to match the editorial
        # voice of the rest of the page (serif label, muted track).
        fig.update_layout(
            legend=dict(
                title=dict(text="National IRSD decile<br>(1 = most disadvantaged)"),
                orientation="v",
                yanchor="middle", y=0.5,
                xanchor="left", x=1.02,
                font=dict(size=11),
                bgcolor="rgba(0,0,0,0)",
            ),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                x=0.02, y=-0.12,
                xanchor="left", yanchor="top",
                pad=dict(t=0, r=10),
                bgcolor="#ffffff",
                bordercolor=PALETTE["rule"],
                font=dict(family="Georgia, serif", size=12, color=PALETTE["ink"]),
                buttons=[
                    dict(
                        label="▶ Play reveal",
                        method="animate",
                        args=[None, dict(
                            frame=dict(duration=700, redraw=True),
                            transition=dict(duration=350, easing="cubic-in-out"),
                            fromcurrent=True,
                            mode="immediate",
                        )],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            transition=dict(duration=0),
                            mode="immediate",
                        )],
                    ),
                ],
            )],
            sliders=[dict(
                active=0,
                x=0.15, y=-0.12, len=0.8,
                xanchor="left", yanchor="top",
                pad=dict(t=4, b=0),
                currentvalue=dict(
                    prefix="Showing: ",
                    font=dict(family="Georgia, serif", size=12, color=PALETTE["ink"]),
                ),
                transition=dict(duration=350, easing="cubic-in-out"),
                bgcolor=PALETTE["rule"],
                activebgcolor=PALETTE["highlight"],
                bordercolor=PALETTE["rule"],
                font=dict(family="Georgia, serif", size=11, color=PALETTE["muted"]),
                steps=[
                    dict(
                        label=str(k),
                        method="animate",
                        args=[[f"Up to decile {k}"], dict(
                            frame=dict(duration=350, redraw=True),
                            transition=dict(duration=350, easing="cubic-in-out"),
                            mode="immediate",
                        )],
                    )
                    for k in range(1, 11)
                ],
            )],
        )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "State: %{customdata[0]}<br>"
            "IRSD score: <b>%{customdata[1]:.0f}</b> "
            "(national decile %{customdata[2]:.0f} / 10)<br>"
            "Population (2011): %{customdata[3]:,.0f}"
            "<extra></extra>"
        ),
        marker_line_width=0.3,
        marker_line_color="#ffffff",
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor=PALETTE["paper"],
    )
    is_animated = view_mode.startswith("▶")
    fig.update_layout(
        title=dict(
            text=(
                f"IRSD by LGA — {title_suffix} "
                "<span style='color:#6b7280;font-size:12px;'>"
                "(SEIFA, ABS Census 2011 — lower = more disadvantage)</span>"
            ),
            x=0, y=0.97, yanchor="top",
            font=dict(size=14),
        ),
        # Smooth transitions on layout updates: the morph applies when the
        # animation steps between frames, and provides a subtle ease on
        # mode/state switches too.
        transition=dict(duration=350, easing="cubic-in-out"),
        margin=dict(l=0, r=0, t=70, b=80 if is_animated else 0),
        height=660 if is_animated else 620,
        paper_bgcolor=PALETTE["paper"],
        font=dict(family="Georgia, serif", color=PALETTE["ink"]),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # ----- Population-by-decile bar --------------------------------------
    # The map answers "where?"; this bar answers "how many?". A national
    # average obscures that the bottom 3 deciles aren't a thin tail —
    # millions of Australians live there, and they're the cohort with
    # the least headroom against the housing CPI print in Chapter 3.
    decile_pop = (
        view_df.dropna(subset=["national_decile"])
        .groupby("national_decile", as_index=False)["population"]
        .sum()
        .sort_values("national_decile")
    )
    decile_pop["national_decile"] = decile_pop["national_decile"].astype(int)
    decile_pop["pop_m"] = decile_pop["population"] / 1_000_000
    decile_pop["band_colour"] = decile_pop["national_decile"].map(
        lambda d: ("#dc2626" if d <= 3 else ("#fde68a" if d <= 7 else "#1e3a8a"))
    )

    # Bar chart spans full width — easier to read 10 decile bars across the
    # page than squeezed into 3/5 of it, and avoids the awkward vertical
    # mismatch that arose from pairing a 380px chart with two stacked
    # extreme-LGA tables.
    fig_bar = go.Figure(
        go.Bar(
            x=decile_pop["national_decile"],
            y=decile_pop["pop_m"],
            marker=dict(color=decile_pop["band_colour"]),
            customdata=decile_pop[["population"]].values,
            hovertemplate=(
                "National decile <b>%{x}</b><br>"
                "Population (2011): %{customdata[0]:,.0f}<br>"
                "(%{y:.2f}M)<extra></extra>"
            ),
            text=decile_pop["pop_m"].map(lambda v: f"{v:.2f}M"),
            textposition="outside",
            textfont=dict(size=11),
        )
    )
    fig_bar.update_layout(
        title=dict(
            text=(
                f"Population by national IRSD decile — {title_suffix} "
                "<span style='color:#6b7280;font-size:11px;'>"
                "(red = bottom 3 deciles)</span>"
            ),
            x=0, font=dict(size=14),
        ),
        xaxis_title="National IRSD decile (1 = most disadvantaged)",
        yaxis_title="Population (millions, 2011)",
        xaxis=dict(tickmode="array", tickvals=list(range(1, 11))),
        showlegend=False,
        bargap=0.25,
        # Smooth bar-height morph when the state filter changes.
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    _apply_chart_theme(fig_bar, height=360)
    st.plotly_chart(fig_bar, width="stretch", config={"displayModeBar": False})

    # ----- Extremes tables — five most + least disadvantaged -------------
    # Sit side-by-side below the bar chart. "Most" and "least" are
    # parallel concepts (mirror image of the same distribution), so the
    # two cards belong on the same row, not stacked.
    most_disadv  = view_df.nsmallest(5, "score")
    least_disadv = view_df.nlargest(5, "score")

    low_col, high_col = st.columns(2)
    with low_col:
        rows_low = "".join(
            f"<tr><td>{r.lga_name}</td><td>{r.state}</td>"
            f"<td style='text-align:right;color:#7f1d1d;'><strong>{int(r.score)}</strong></td></tr>"
            for r in most_disadv.itertuples()
        )
        st.markdown(
            '<div class="lga-table-card lga-table-card--low">'
            '<div class="lga-table-title">Five most disadvantaged LGAs (in view)</div>'
            f'<table class="lga-table"><thead><tr>'
            '<th>LGA</th><th>State</th><th style="text-align:right;">IRSD</th>'
            '</tr></thead>'
            f'<tbody>{rows_low}</tbody></table></div>',
            unsafe_allow_html=True,
        )
    with high_col:
        rows_high = "".join(
            f"<tr><td>{r.lga_name}</td><td>{r.state}</td>"
            f"<td style='text-align:right;color:#1e3a8a;'><strong>{int(r.score)}</strong></td></tr>"
            for r in least_disadv.itertuples()
        )
        st.markdown(
            '<div class="lga-table-card lga-table-card--high">'
            '<div class="lga-table-title">Five least disadvantaged LGAs (in view)</div>'
            f'<table class="lga-table"><thead><tr>'
            '<th>LGA</th><th>State</th><th style="text-align:right;">IRSD</th>'
            '</tr></thead>'
            f'<tbody>{rows_high}</tbody></table></div>',
            unsafe_allow_html=True,
        )

    # ----- Dataset-driven pull quote -------------------------------------
    # All numbers below are derived from the current view_df, not hard-
    # coded. The national-context line in the "All Australia" branch
    # uses the full df_lga so the comparison always has a denominator.
    if selected_state == "All Australia":
        quote = (
            f"<strong>{share_bottom3:.1f}%</strong> of the Australian population "
            f"({pop_bottom3/1_000_000:.2f}M of {total_pop/1_000_000:.2f}M) lives in "
            f"an LGA in the bottom three national IRSD deciles. The IRSD spread "
            f"across the federation is <strong>{int(iqr_spread)} points</strong> "
            f"({int(score_min)} → {int(score_max)}). A uniform CPI deflator applied "
            f"to every LGA mis-states the lived pressure by orders of magnitude — "
            f"the LGA layer should accompany any national cost-of-living parameter "
            f"in a Treasury brief."
        )
    else:
        nat_bottom3_mask = df_lga["national_decile"].between(1, 3)
        nat_share = df_lga.loc[nat_bottom3_mask, "population"].sum() / df_lga["population"].sum() * 100
        delta_vs_nat = share_bottom3 - nat_share
        direction = "above" if delta_vs_nat >= 0 else "below"
        quote = (
            f"In <strong>{selected_state}</strong>, "
            f"<strong>{share_bottom3:.1f}%</strong> of residents "
            f"({pop_bottom3/1_000_000:.2f}M of {total_pop/1_000_000:.2f}M) live in "
            f"an LGA in the bottom three national IRSD deciles — "
            f"<strong>{abs(delta_vs_nat):.1f} pts {direction}</strong> the national "
            f"share ({nat_share:.1f}%). State-internal IRSD spread is "
            f"<strong>{int(iqr_spread)} points</strong> "
            f"({int(score_min)} → {int(score_max)})."
        )

    st.markdown(
        '<div class="lga-section-enter lga-section-enter--delay-3">'
        f'<div class="pull-quote">{quote}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def section_so_what_drivers(df: pd.DataFrame) -> None:
    """So What — what's actually driving inflation? Food, housing,
    transport CPI sub-indices over time.

    Note on scope: this chapter previously took a ``selected_quarter``
    argument and rendered a single-quarter KPI strip driven by the
    global slider. Marker feedback flagged that as confusing — Chapter
    3 is a cumulative-drivers story, not a quarter snapshot — so the
    slider dependency is removed and the KPI strip below now reports
    cumulative gaps against the All-Groups average across the whole
    window. The slider in Chapter 1 is scoped to Chapters 1–2 only.
    """
    nat = national_series(df)

    chapter_header(
        anchor="ch3",
        title="3. Cost Drivers: Components of Inflationary Pressure",
        lede=(
            "Quarterly inflation outcomes reflect aggregate price movements across "
            "multiple expenditure categories. While some categories recorded "
            "relatively modest increases, others experienced substantially stronger "
            "price growth. For many households, particularly those facing rising "
            "housing and living costs, the headline inflation rate may not fully "
            "reflect experienced cost pressures. The charts below compare selected "
            "CPI categories with the overall inflation average."
        ),
    )

    # --- Category toggles ---
    st.markdown(
        '<p style="color:#6b7280; font-size:0.85rem; margin-bottom:0.25rem;">'
        "Toggle categories to compare against the All Groups average:"
        "</p>",
        unsafe_allow_html=True,
    )

    toggle_cols = st.columns(3)
    with toggle_cols[0]:
        show_housing = st.checkbox(
            "\U0001f3e0 Housing", value=False, key="toggle_housing",
        )
    with toggle_cols[1]:
        show_food = st.checkbox(
            "\U0001f6d2 Food", value=False, key="toggle_food",
        )
    with toggle_cols[2]:
        show_transport = st.checkbox(
            "\U0001f697 Transport", value=False, key="toggle_transport",
        )

    # --- Build chart ---
    fig = go.Figure()
    # Always show the All Groups CPI baseline as a dotted reference line
    fig.add_trace(
        go.Scatter(
            x=nat["quarter"],
            y=nat["inflation_rate"],
            mode="lines+markers",
            name="All Groups CPI (average)",
            line=dict(color=PALETTE["muted"], width=2, dash="dot"),
            marker=dict(size=5, symbol="circle-open"),
            hovertemplate="<b>%{x}</b><br>All Groups CPI: %{y:+.1f}%<extra></extra>",
        )
    )
    categories_config = [
        ("housing", "Housing", PALETTE["housing"], show_housing),
        ("food", "Food & non-alcoholic beverages", PALETTE["food"], show_food),
        ("transport", "Transport", PALETTE["transport"], show_transport),
    ]

    any_selected = show_housing or show_food or show_transport

    for col, name, color, is_visible in categories_config:
        if is_visible:
            fig.add_trace(
                go.Scatter(
                    x=nat["quarter"],
                    y=nat[col],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=color, width=4),
                    marker=dict(size=9),
                    hovertemplate=(
                        f"<b>%{{x}}</b><br>{name}: %{{y:+.1f}}%<extra></extra>"
                    ),
                )
            )

    # If nothing is toggled, show all categories as a preview. Solid +
    # heavier than the previous dotted/0.35-opacity pass — the old version
    # read as pastel and was hard to follow against the All-Groups baseline.
    if not any_selected:
        for col, name, color, _ in categories_config:
            fig.add_trace(
                go.Scatter(
                    x=nat["quarter"],
                    y=nat[col],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=color, width=3),
                    marker=dict(size=7),
                    opacity=0.9,
                    hovertemplate=(
                        f"<b>%{{x}}</b><br>{name}: %{{y:+.1f}}%<extra></extra>"
                    ),
                )
            )

    chart_title = "CPI by category — quarter-on-quarter change"
    if any_selected:
        selected_names = []
        if show_housing:
            selected_names.append("Housing")
        if show_food:
            selected_names.append("Food")
        if show_transport:
            selected_names.append("Transport")
        chart_title = f"{', '.join(selected_names)} vs All Groups average"

    fig.update_layout(
        title=dict(text=chart_title, x=0, font=dict(size=16)),
        yaxis_title="Quarter-on-quarter change (%)",
    )
    _apply_chart_theme(fig, height=440)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # --- KPI cards: cumulative across the full window -------------------
    # Each tile shows the category's cumulative QoQ change and the gap
    # against the cumulative All-Groups CPI for the same window. This
    # is the right unit for a cost-drivers chapter — a single quarter
    # tile would re-import the snapshot framing the slider used to
    # impose, which the marker flagged as confusing.
    cum_cpi_all   = nat["inflation_rate"].sum()
    cum_housing   = nat["housing"].sum()
    cum_food      = nat["food"].sum()
    cum_transport = nat["transport"].sum()
    period_label  = f"{nat['quarter'].iloc[0]} → {nat['quarter'].iloc[-1]}"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card(
            "Period covered", period_label,
            f"{len(nat)} quarters · All Groups CPI {cum_cpi_all:+.1f}%",
        ), unsafe_allow_html=True)
    with k2:
        gap = cum_housing - cum_cpi_all
        st.markdown(kpi_card(
            "🏠 Housing (cumulative)", f"{cum_housing:+.1f}%",
            f"{gap:+.1f} ppt vs All Groups average.",
        ), unsafe_allow_html=True)
    with k3:
        gap = cum_food - cum_cpi_all
        st.markdown(kpi_card(
            "🛒 Food (cumulative)", f"{cum_food:+.1f}%",
            f"{gap:+.1f} ppt vs All Groups average.",
        ), unsafe_allow_html=True)
    with k4:
        gap = cum_transport - cum_cpi_all
        st.markdown(kpi_card(
            "🚗 Transport (cumulative)", f"{cum_transport:+.1f}%",
            f"{gap:+.1f} ppt vs All Groups average.",
        ), unsafe_allow_html=True)

    # --- Cumulative summary ---
    cum_food = nat["food"].sum()
    cum_housing = nat["housing"].sum()
    cum_transport = nat["transport"].sum()
    cum_all = nat["inflation_rate"].sum()
    housing_gap = abs(cum_housing - cum_all)

    st.markdown(
        f'<div style="background:#fffbeb; border-left:4px solid #f59e0b; '
        f'border-radius:8px; padding:1.5rem 1.5rem; margin:1.5rem 0;">'
        f'<p style="font-family:Georgia,serif; font-size:1.35rem; '
        f'font-weight:700; color:#1f2937; margin:0 0 0.75rem 0; line-height:1.3;">'
        f"Real wage gains were offset by rising living costs."
        f"</p>"
        f'<p style="font-size:1rem; line-height:1.7; color:#374151; margin:0;">'
        f"Over {len(nat)} quarters — Housing surged <strong>{cum_housing:+.1f}%</strong> · "
        f"Food climbed <strong>{cum_food:+.1f}%</strong> · "
        f"Transport jumped <strong>{cum_transport:+.1f}%</strong>"
        f"</p>"
        f'<p style="font-size:1rem; line-height:1.7; color:#374151; margin:0.5rem 0 0 0;">'
        f"Yet the indexation rate used to adjust rent assistance, "
        f"JobSeeker, and the Age Pension was just "
        f"<strong>{cum_all:+.1f}%</strong>. "
        f"That leaves a <strong>{housing_gap:.1f}-point blind spot</strong> "
        f"on housing alone — the single largest expense for the people "
        f"these payments are designed to protect."
        f"</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

def section_what_next_whatif(df: pd.DataFrame) -> None:
    """What Next — a what-if projector. Reader sets a hypothetical
    quarterly wage-growth and inflation rate; we project the cumulative
    real-wage line forward eight quarters."""
    nat = national_series(df)
    last = nat.iloc[-1]
    cum_so_far = nat["real_wage_growth"].sum()

    chapter_header(
        anchor="ch4",
        title="4. Forecast Scenarios: Projecting Real Wage Outcomes",
        lede=(
            "Use the sliders below to set a hypothetical wage growth "
            "rate and inflation rate for the next two years. The dashed "
            "line shows where cumulative real wages would end up under "
            "your scenario — starting from where the actual data "
            "leaves off."
        ),
    )

    # Preset scenarios — saves the busy reader from picking three numbers.
    # Each preset writes the same session_state keys the sliders use, so
    # the next rerun shows the preset values in the controls. We use one
    # key namespace (no `value=` on the widgets) because mixing `value=`
    # and `key=` on a Streamlit widget makes preset clicks silently fail.
    PRESETS = {
        "RBA-aligned": dict(scen_wage=0.9, scen_inflation=0.6, scen_target=3.0),
        "Optimistic": dict(scen_wage=1.2, scen_inflation=0.5, scen_target=3.0),
        "Pessimistic": dict(scen_wage=0.6, scen_inflation=1.1, scen_target=3.0),
    }
    for k, v in PRESETS["RBA-aligned"].items():
        st.session_state.setdefault(k, v)

    p1, p2, p3, p4 = st.columns([1, 1, 1, 1])
    with p1:
        if st.button("RBA-aligned", width="stretch", help="Centre-of-fan scenario"):
            st.session_state.update(PRESETS["RBA-aligned"])
            st.rerun()
    with p2:
        if st.button("Optimistic", width="stretch", help="Strong WPI, easing CPI"):
            st.session_state.update(PRESETS["Optimistic"])
            st.rerun()
    with p3:
        if st.button("Pessimistic", width="stretch", help="Soft WPI, sticky CPI"):
            st.session_state.update(PRESETS["Pessimistic"])
            st.rerun()
    with p4:
        if st.button("Reset", width="stretch"):
            st.session_state.update(PRESETS["RBA-aligned"])
            st.rerun()

    avg_wage = nat["wage_growth"].mean()
    avg_inflation = nat["inflation_rate"].mean()

    cw, ci, ct = st.columns([1, 1, 1])
    with cw:
        scen_wage = st.slider(
            "Hypothetical quarterly wage growth (%)",
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            help=f"Average QoQ wage growth across the period was about {avg_wage:.2f}%.",
            key="scen_wage",
        )
    with ci:
        scen_inflation = st.slider(
            "Hypothetical quarterly inflation (%)",
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            help=f"Average QoQ inflation across the period was about {avg_inflation:.2f}%.",
            key="scen_inflation",
        )
    with ct:
        target = st.number_input(
            "Recovery target — cumulative real-wage gain (%)",
            min_value=-5.0,
            max_value=10.0,
            step=0.5,
            help="How much cumulative real-wage growth counts as 'recovered'?",
            key="scen_target",
        )

    # Project 8 quarters forward from the last actual quarter. The
    # cumulative line continues from where the historical line ends so
    # the visual transition reads as one continuous story.
    horizon = 8
    future_quarters = []
    last_year = int(last["year"])
    last_qn = int(last["quarter_num"])
    for _ in range(horizon):
        last_qn += 1
        if last_qn > 4:
            last_qn = 1
            last_year += 1
        future_quarters.append(f"Q{last_qn} {last_year}")

    scen_real = round(scen_wage - scen_inflation, 2)
    cum_so_far_r = round(cum_so_far, 2)
    proj_cum = [round(cum_so_far_r + scen_real * (i + 1), 2) for i in range(horizon)]
    actual_cum = nat["real_wage_growth"].cumsum().round(2)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=nat["quarter"],
            y=actual_cum,
            mode="lines+markers",
            name="Actual cumulative real wage",
            line=dict(color=PALETTE["wage"], width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Cumulative: %{y:+.1f}%<extra></extra>",
        )
    )
    # Bridge the last actual point to the first projected point so the
    # line is visually unbroken.
    fig.add_trace(
        go.Scatter(
            x=[nat["quarter"].iloc[-1]] + future_quarters,
            y=[cum_so_far_r] + proj_cum,
            mode="lines+markers",
            name="Your scenario",
            line=dict(color=PALETTE["highlight"], width=3, dash="dash"),
            marker=dict(size=8, symbol="diamond"),
            hovertemplate="<b>%{x}</b><br>Projected cumulative: %{y:+.1f}%<extra></extra>",
        )
    )
    fig.add_hline(
        y=target,
        line=dict(color=PALETTE["positive"], width=1.5, dash="dot"),
        annotation_text=f"Recovery target: {target:+.1f}%",
        annotation_position="top right",
        annotation_font_color=PALETTE["positive"],
    )
    fig.update_layout(
        title=dict(
            text="Cumulative real-wage growth — actual + your scenario",
            x=0,
            font=dict(size=16),
        ),
        yaxis_title="Cumulative real wage Δ since Q4 2023 (%)",
    )
    _apply_chart_theme(fig, height=460)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # Compute when (if ever) the projection crosses the target.
    if scen_real <= 0 and cum_so_far < target:
        verdict = (
            f"At a real-wage rate of {scen_real:+.2f}% per quarter, the "
            f"recovery target of {target:+.1f}% is never reached."
        )
    else:
        for i, val in enumerate(proj_cum):
            if val >= target:
                verdict = (
                    f"Your scenario reaches the {target:+.1f}% target "
                    f"in <strong>{future_quarters[i]}</strong> — "
                    f"{i + 1} quarter(s) from the end of the actual data."
                )
                break
        else:
            verdict = (
                f"Eight quarters of projection isn't enough — at this "
                f"rate the target would land beyond {future_quarters[-1]}."
            )

    st.markdown(
        f'<div class="pull-quote">{verdict}</div>',
        unsafe_allow_html=True,
    )


def section_call_to_action(df: pd.DataFrame) -> None:
    """Closing — five dataset-grounded briefing points for Treasury.

    Each point opens with a finding computed from this dataset (specific
    number, specific quarter) and follows with an analyst-framed
    "suggested next step". The chapter deliberately avoids policy-maker
    imperatives ("Treasury should reform X") — a Treasury policy analyst
    informs decisions; the Minister makes them.
    """
    nat = national_series(df)

    # Everything below is computed once and inlined into the prose so the
    # briefing points stay explicitly anchored to the data — if the CSV
    # is refreshed with a new ABS release, the headline numbers update
    # without us hand-editing the copy.
    cum_wage      = nat["wage_growth"].sum()
    cum_cpi       = nat["inflation_rate"].sum()
    cum_real      = nat["real_wage_growth"].sum()
    cum_housing   = nat["housing"].sum()
    cum_transport = nat["transport"].sum()
    housing_gap   = cum_housing - cum_cpi
    transport_gap = cum_transport - cum_cpi
    neg_quarters   = int((nat["real_wage_growth"] < 0).sum())
    total_quarters = len(nat)

    # Per-state WPI growth across the full series — the spread is the
    # evidence that jurisdictional disaggregation matters.
    first_q  = nat["quarter"].iloc[0]
    last_q   = nat["quarter"].iloc[-1]
    s_first  = df[df["quarter"] == first_q].set_index("state_code")["wage_index"]
    s_last   = df[df["quarter"] == last_q].set_index("state_code")["wage_index"]
    s_growth = ((s_last - s_first) / s_first * 100).sort_values(ascending=False)
    leader_code, laggard_code = s_growth.index[0], s_growth.index[-1]
    state_spread = s_growth.iloc[0] - s_growth.iloc[-1]

    # LGA-layer evidence for the geographic-disaggregation finding.
    # Pulled live from the same SEIFA dataframe the choropleth uses so
    # the briefing point stays in lock-step with the LGA visualisation.
    _, df_lga = load_lga_data()
    nat_total_pop  = float(df_lga["population"].sum())
    nat_b3_pop     = float(df_lga.loc[df_lga["national_decile"].between(1, 3), "population"].sum())
    nat_b3_share   = nat_b3_pop / nat_total_pop * 100
    # Worst-affected state by bottom-3 share — the dataset-derived
    # outlier that makes the "national-uniform parameter misstates the
    # lived pressure" point concrete.
    state_b3 = (
        df_lga.dropna(subset=["national_decile"])
        .assign(in_b3=lambda d: d["national_decile"].between(1, 3))
        .groupby("state")
        .apply(lambda g: g.loc[g["in_b3"], "population"].sum() / g["population"].sum() * 100)
        .sort_values(ascending=False)
    )
    worst_state      = str(state_b3.index[0])
    worst_state_pct  = float(state_b3.iloc[0])
    irsd_spread      = int(df_lga["score"].max() - df_lga["score"].min())

    # Transport reverted sharply: pull the worst two QoQ Transport prints
    # straight from the data rather than hard-coding the values, so the
    # briefing copy stays correct if the CSV is refreshed.
    transport_lows = nat.nsmallest(2, "transport")[["quarter", "transport"]].values
    t_low1_q, t_low1_v = transport_lows[0]
    t_low2_q, t_low2_v = transport_lows[1]

    # Housing 2024 reversion + 2025 quarterly trajectory: also pulled
    # from the data rather than hard-coded, so the line "+1.7%, +1.2%..."
    # never desyncs from the CSV.
    def _housing(quarter_label: str) -> float:
        return float(nat.loc[nat["quarter"] == quarter_label, "housing"].iloc[0])

    h_2024_q3    = _housing("Q3 2024")
    h_2024_q4    = _housing("Q4 2024")
    housing_2025 = float(nat.loc[nat["year"] == 2025, "housing"].sum())
    h_2025_q     = (
        nat[nat["year"] == 2025]
        .sort_values("quarter_date")["housing"]
        .map(lambda v: f"{v:+.1f}%")
        .tolist()
    )
    h_2025_trail = ", ".join(h_2025_q)

    chapter_header(
        anchor="ch5",
        title="5. Findings and Next Steps for Treasury",
        lede=(
            "The five points below are written from a Treasury policy "
            "analyst's vantage point: each one starts with a number "
            "this dataset has already produced in Chapters 1–4, and "
            "ends with a <em>suggested next step</em> for the cost-of-"
            "living desk's next round of modelling or briefing. The "
            "framing is deliberate — a policy analyst can influence "
            "decisions and shape the briefing pack, but the call sits "
            "with the Treasurer."
        ),
    )

    briefing_points = [
        (
            f"Finding 1 — Real wages spent {neg_quarters} of {total_quarters} quarters underwater.",
            (
                f"Real wage growth was negative in <strong>{neg_quarters} "
                f"of {total_quarters}</strong> quarters from {first_q} to "
                f"{last_q} (see Chapter 1). Across the full window, "
                f"nominal wage growth of <strong>{cum_wage:+.1f}%</strong> "
                f"ran only <strong>{cum_real:+.1f} ppt</strong> ahead of "
                f"CPI — a margin small enough to invert on a single "
                f"quarterly print."
                "<br><br>"
                "<em>Suggested next step.</em> The WPI-minus-CPI gap is "
                "not currently a routinely reported aggregate. Treasury "
                "may wish to publish it as a standing quarterly indicator "
                "in the post-ABS-release brief so the Treasurer's office "
                "reads purchasing-power trajectory at a glance, rather "
                "than reconciling the two series by hand."
            ),
        ),
        (
            f"Finding 2 — Housing CPI ran {housing_gap:+.1f} ppt above the All-Groups average.",
            (
                f"Housing cumulatively rose <strong>{cum_housing:+.1f}%</strong> "
                f"against an All-Groups CPI of <strong>{cum_cpi:+.1f}%</strong> "
                f"over the period — a <strong>{housing_gap:+.1f} ppt</strong> "
                f"divergence (Chapter 3). Income-support payments indexed "
                f"to All-Groups therefore trail the cost component most "
                f"concentrated in lower-income household budgets."
                "<br><br>"
                "<em>Suggested next step.</em> Treasury may wish to model "
                "an indexation variant that gives Housing a heavier weight "
                "than its All-Groups share, and present the option for "
                "the Treasurer's consideration alongside the next "
                "scheduled biannual indexation review. The What-If tool "
                "in Chapter 4 already accepts a parameterised inflation "
                "input — the same machinery can be re-pointed at a "
                "Housing-weighted deflator."
            ),
        ),
        (
            f"Finding 3 — Transport CPI ran {transport_gap:+.1f} ppt below the All-Groups basket.",
            (
                f"Transport contributed only <strong>{cum_transport:+.1f}%</strong> "
                f"over the nine-quarter window — <strong>{transport_gap:+.1f} ppt</strong> "
                f"below the All-Groups average (Chapter 3), driven by "
                f"negative prints in {t_low1_q} (<strong>{t_low1_v:+.1f}%</strong>) "
                f"and {t_low2_q} (<strong>{t_low2_v:+.1f}%</strong>). "
                f"Without that drag, both headline CPI and the real-wage "
                f"gap would have read materially worse."
                "<br><br>"
                "<em>Suggested next step.</em> Treasury may wish to "
                "stress-test the forward real-wage projection in Chapter "
                "4 against a scenario where Transport reverts to the "
                "broader basket. The what-if controls already accept a "
                "hypothetical inflation rate; flipping them to a "
                "normalised-Transport case surfaces the sensitivity for "
                "the Treasurer in a single chart."
            ),
        ),
        (
            f"Finding 4 — Geographic disaggregation: {state_spread:.2f} ppt WPI spread, {irsd_spread}-point IRSD spread.",
            (
                f"Two pieces of evidence in this dataset point the same "
                f"direction. <strong>(a)</strong> WPI growth from {first_q} "
                f"to {last_q} ranged from "
                f"<strong>{s_growth.iloc[0]:+.1f}% in {leader_code}</strong> "
                f"to <strong>{s_growth.iloc[-1]:+.1f}% in {laggard_code}</strong> "
                f"— a <strong>{state_spread:.2f} ppt</strong> jurisdictional "
                f"spread (Chapter 2). <strong>(b)</strong> Below the state "
                f"line, <strong>{nat_b3_share:.1f}%</strong> of Australians "
                f"(<strong>{nat_b3_pop/1_000_000:.2f}M</strong> of "
                f"{nat_total_pop/1_000_000:.2f}M) live in an LGA in the "
                f"bottom three national IRSD deciles — and the share is "
                f"not evenly distributed: in <strong>{worst_state}</strong> "
                f"it reaches <strong>{worst_state_pct:.1f}%</strong>. The "
                f"national IRSD spread is <strong>{irsd_spread} points</strong>, "
                f"orders of magnitude wider than the cumulative real-wage "
                f"gain of {cum_real:+.1f}%."
                "<br><br>"
                "<em>Suggested next step.</em> For any cost-of-living "
                "measure with regional take-up patterns (Energy Bill "
                "Relief, rent assistance settings, place-based "
                "supplements), Treasury may wish to disaggregate the "
                "real-wage projection by state — and, where the "
                "instrument permits, by SEIFA decile — before settling "
                "on a national parameter. The LGA layer in Chapter 2 is "
                "ready to be re-pointed at any sub-state target group."
            ),
        ),
        (
            "Finding 5 — Housing CPI reverted sharply after two negative prints.",
            (
                f"Housing printed negative in 2024 Q3 (<strong>{h_2024_q3:+.1f}%</strong>) "
                f"and 2024 Q4 (<strong>{h_2024_q4:+.1f}%</strong>) before "
                f"rebounding to a cumulative <strong>{housing_2025:+.1f}%</strong> "
                f"across 2025 ({h_2025_trail} Q1–Q4). The "
                f"shape is consistent with administered-price interventions "
                f"temporarily suppressing the index, with the level effect "
                f"recovered once the supports rolled off."
                "<br><br>"
                "<em>Suggested next step.</em> Treasury may wish to "
                "report an <em>underlying</em> Housing CPI alongside the "
                "headline series in cost-of-living briefings, so the "
                "Treasurer can separate policy-induced moves from "
                "structural pressure when the next round of relief "
                "measures is being calibrated."
            ),
        ),
    ]
    for label, body in briefing_points:
        st.markdown(
            '<div class="policy-rec">'
            f'<div class="rec-label">{label}</div>'
            f'<div class="rec-body">{body}</div>'
            "</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    df = load_data()

    # --- Top banner ---
    st.image(str(BANNER_PATH))

    # Sidebar = reference material only (glossary + sources).
    # The spotlight-quarter slider used to live here, but the global
    # placement implied it drove the whole document; marker feedback
    # asked us to scope it explicitly. The slider now renders inside
    # Chapter 1, co-located with the chart it primarily drives.
    with st.sidebar:
        st.markdown("### Reference")
        st.markdown(
            '<p style="color:#6b7280;font-size:0.9rem;">'
            "Definitions and source links for the figures used throughout "
            "the story. The interactive controls (spotlight quarter and "
            "what-if scenarios) live in-chapter where they take effect."
            "</p>",
            unsafe_allow_html=True,
        )

        with st.expander("Glossary", expanded=False):
            st.markdown(
                "**WPI** — Wage Price Index. ABS series tracking the price "
                "of labour, holding job mix constant.\n\n"
                "**CPI** — Consumer Price Index. ABS series tracking the "
                "price of a representative basket of household goods.\n\n"
                "**Nominal wage** — the dollar number on your payslip.\n\n"
                "**Real wage** — nominal wage adjusted for CPI. The "
                "purchasing-power view of pay.\n\n"
                "**QoQ** — quarter-on-quarter percentage change. All rates "
                "in this story are QoQ unless stated otherwise."
            )

        with st.expander("Data & sources", expanded=False):
            st.markdown(
                "- ABS Cat. **6345.0** — Wage Price Index (Tables 1, 2b)\n"
                "- ABS Cat. **6401.0** — Consumer Price Index (Table 18)\n"
                "- Coverage: **Q4 2023 → Q4 2025**, 8 states/territories\n"
                "- Joining: WPI per state + national CPI broadcast across "
                "states in long format. See README for full data dictionary."
            )

    chapter_nav()
    section_hero(df)
    section_tldr(df)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    # section_what_national renders the spotlight-quarter slider as its
    # first widget and returns the selected value so Chapters 2 and 3
    # stay in sync without us re-introducing global state.
    selected_quarter = section_what_national(df)
    section_what_state(df, selected_quarter)
    # Chapter 3 deliberately does not take the spotlight quarter —
    # cumulative-driver KPIs read the full window, not a snapshot.
    section_so_what_drivers(df)
    section_what_next_whatif(df)
    section_call_to_action(df)


if __name__ == "__main__":
    main()
