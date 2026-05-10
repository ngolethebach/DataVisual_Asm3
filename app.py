"""
Real Wages, Real Lives — Australia's Cost-of-Living Story (2023 Q4 → 2025 Q4).

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
"""

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

# Editorial palette — wage = steel blue (calm/trust), inflation = alarm red,
# real-wage delta = green when positive / red when negative, amber for the
# selected-quarter highlight. Contrast pairs all hit WCAG AA on #fafaf7.
PALETTE = {
    "ink":          "#1f2937",
    "paper":        "#fafaf7",
    "muted":        "#6b7280",
    "rule":         "#d1d5db",
    "wage":         "#2563eb",
    "inflation":    "#dc2626",
    "positive":     "#059669",
    "negative":     "#dc2626",
    "highlight":    "#f59e0b",
    "food":         "#ea580c",
    "housing":      "#7c3aed",
    "transport":    "#0891b2",
}

STATE_ORDER = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]


# ---------------------------------------------------------------------------
# Page config + global CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Real Wages, Real Lives",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A handful of overrides to give the page an editorial scrollytelling
# feel: narrower max-width for prose blocks, larger hero type, calmer
# section spacing. Streamlit's default container is full-bleed, which
# reads as dashboard-y; we want the page to feel like a long-read.
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
        font-family: Georgia, serif; font-size: 4.5rem; line-height: 1;
        color: #dc2626; font-weight: 700; margin: 0.25rem 0;
      }
      .persona-badge {
        display: inline-block; margin-top: 0.75rem;
        padding: 0.35rem 0.85rem; border-radius: 999px;
        background: #1f2937; color: #fafaf7;
        font-size: 0.78rem; letter-spacing: 0.06em; font-weight: 600;
      }
      .persona-badge .persona-label {
        color: #f59e0b; text-transform: uppercase; letter-spacing: 0.14em;
        font-size: 0.68rem; margin-right: 0.5rem;
      }
      .narrative {
        font-size: 1.1rem; line-height: 1.65; color: #374151;
        max-width: 65ch;
      }
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
      /* Chapter header band — replaces the thin <hr> divider with a more
         decisive break that also encodes the narrative-arc stage and a
         chapter number for the navigation pills to point at. */
      .chapter-band {
        margin: 2.75rem 0 0.5rem 0; padding-bottom: 0.5rem;
        border-bottom: 1px solid #d1d5db;
      }
      .chapter-band .arc-pill {
        display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
        font-size: 0.7rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: #ffffff; margin-right: 0.6rem;
        vertical-align: middle;
      }
      .chapter-band .arc-what       { background: #2563eb; }
      .chapter-band .arc-so-what    { background: #7c3aed; }
      .chapter-band .arc-what-next  { background: #059669; }
      .chapter-band .chapter-num {
        font-family: Georgia, serif; color: #6b7280; font-size: 0.92rem;
        font-weight: 600; letter-spacing: 0.06em; vertical-align: middle;
      }
      .section-divider {
        height: 1px; background: #d1d5db; margin: 3rem 0 2rem 0;
        border: none;
      }.policy-rec {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
        padding: 1.5rem; margin: 1.5rem 0; max-width: 65ch;
      }
      .policy-rec .rec-label {
        font-family: Georgia, "Times New Roman", serif;
        color: #059669; font-size: 1.25rem; font-weight: 700;
        margin-bottom: 0.5rem; line-height: 1.3;
      }
      .policy-rec .rec-body {
        font-size: 0.95rem; line-height: 1.6; color: #374151;
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
    # National series is identical across the 8 state rows per quarter,
    # so drop_duplicates gives us a single national timeline.
    nat = (
        df.drop_duplicates("quarter_date")
        .sort_values("quarter_date")
        .reset_index(drop=True)
    )
    nat["cum_real_wage"] = nat["real_wage_growth"].cumsum()
    # Broadcast the cumulative back onto the per-state long frame.
    df = df.merge(
        nat[["quarter_date", "cum_real_wage"]], on="quarter_date", how="left"
    )
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
            bgcolor="#ffffff", bordercolor=PALETTE["rule"],
            font=dict(family="Georgia, serif", size=13, color=PALETTE["ink"]),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0, font=dict(size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor=PALETTE["rule"],
        ticks="outside", tickcolor=PALETTE["rule"],
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=PALETTE["rule"], gridwidth=0.5,
        zeroline=True, zerolinecolor=PALETTE["muted"], zerolinewidth=1,
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


# Narrative-arc pill colours — chapter_header looks these up by stage label.
ARC_CLASSES = {
    "What":       "arc-what",
    "So What":    "arc-so-what",
    "What Next":  "arc-what-next",
}


def chapter_header(num: int, arc: str, anchor: str, title: str,
                   lede: str) -> None:
    """Render a consistent chapter band: arc pill, chapter number, anchor
    target for the sticky nav, the title, and the opening paragraph.

    The invisible <a> sits 90px above the visible heading so anchor jumps
    don't bury the title under the sticky nav bar.
    """
    arc_class = ARC_CLASSES.get(arc, "arc-what")
    st.markdown(
        f'<a class="chapter-anchor" id="{anchor}"></a>'
        f'<div class="chapter-band">'
        f'<span class="arc-pill {arc_class}">{arc}</span>'
        f'<span class="chapter-num">Chapter {num}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"## {title}")
    st.markdown(f'<p class="narrative">{lede}</p>', unsafe_allow_html=True)


def chapter_nav() -> None:
    """Sticky pill nav linking to each chapter anchor. Browsers handle
    the scroll natively — no JS required, no Streamlit reruns."""
    items = [
        ("ch1", "1 · The gap"),
        ("ch2", "2 · State by state"),
        ("ch3", "3 · What\u2019s getting expensive"),
        ("ch4", "4 · What if"),
        ("ch5", "5 · What should change?"),
    ]
    pills = "".join(
        f'<a href="#{anchor}">{label}</a>' for anchor, label in items
    )
    st.markdown(
        f'<div class="chapter-nav">'
        f'<span class="nav-label">Jump to</span>{pills}'
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sections — one function per chapter so the narrative flow in main()
# reads top-to-bottom like an outline.
# ---------------------------------------------------------------------------


def section_hero(df: pd.DataFrame) -> None:
    """Opening: kicker, headline, lede, and the single most striking stat."""
    nat = national_series(df)
    n_negative = int((nat["real_wage_growth"] < 0).sum())
    n_total = len(nat)
    cum_real = nat["real_wage_growth"].sum()

    st.markdown('<div class="hero-kicker">A Data Narrative · UTS Asm3</div>',
                unsafe_allow_html=True)
    st.markdown("# Real Wages, Real Lives")
    st.markdown(
        '<p class="narrative">'
        "Between late 2023 and the end of 2025, wages were growing. "
        "The number on the payslip was getting bigger. But prices were "
        "rising faster \u2014 and over nine quarters, the gap between what "
        "Australians earned and what they could actually buy with it "
        f"adds up to just <strong>{cum_real:+.1f}%</strong> in real terms. "
        "That\u2019s the difference between the wage on paper and the wage "
        "in practice."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="hero-stat">{n_negative} of {n_total}</div> </p>'
        '<p class="narrative" style="margin-top:-0.5rem;">'
        "quarters where wage growth didn\u2019t keep up with inflation. "
        "In those quarters, every dollar earned bought less than the "
        "quarter before. This matters for policy because government "
        "payments like rent assistance and pensions are adjusted based "
        "on these numbers \u2014 and if the adjustment formula doesn\u2019t "
        "reflect reality, the payments fall behind too."
        "</p>"
        '<div class="persona-badge">'
        '<span class="persona-label">Prepared for</span>'
        "Treasury Policy Analyst"
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
    leader_state_q = df[df["quarter"] == last_q["quarter"]] \
        .sort_values("wage_index", ascending=False).iloc[0]
    laggard_state_q = df[df["quarter"] == last_q["quarter"]] \
        .sort_values("wage_index", ascending=True).iloc[0]
    state_spread = leader_state_q["wage_index"] - laggard_state_q["wage_index"]

    st.markdown(
        '<p class="hero-kicker" style="margin-top:2rem;">The 30-second version</p>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(tldr_card(
            "The Gap",
            "Wages grew. Real wages barely moved.",
            f"Over nine quarters, real wage growth totalled just "
            f"<strong>{cum_real:+.1f}%</strong>. Inflation clawed back "
            "almost everything that wage growth delivered.",
            stripe=PALETTE["wage"],
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(tldr_card(
            "The Driver",
            "Housing costs did most of the damage.",
            f"Housing prices rose <strong>{cum_housing:+.1f}%</strong> "
            "over the period \u2014 well above the overall average. "
            "Government payments adjusted to the average rate have "
            "fallen behind the cost that matters most.",
            stripe=PALETTE["housing"],
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(tldr_card(
            "The Uneven Recovery",
            "Not every state is in the same position.",
            f"In {last_q['quarter']}, there\u2019s a "
            f"<strong>{state_spread:.1f}-point</strong> gap between "
            f"{leader_state_q['state_name']} and "
            f"{laggard_state_q['state_name']} on the wage index. "
            "A one-size-fits-all national policy can\u2019t address that.",
            stripe=PALETTE["positive"],
        ), unsafe_allow_html=True)


def section_what_national(df: pd.DataFrame, selected_quarter: str) -> None:
    """What — the national picture. Wage growth vs inflation timeline,
    with a highlighted marker at the user-selected quarter."""
    nat = national_series(df)
    sel_row = nat[nat["quarter"] == selected_quarter].iloc[0]

    chapter_header(
        num=1, arc="What", anchor="ch1",
        title="The Headline Number Lies",
        lede=(
            "Every quarter, the ABS releases two key numbers: how fast "
            "wages are growing, and how fast prices are rising. Most "
            "reporting covers them separately. The real story only "
            "appears when you put them on the same chart \u2014 because "
            "it\u2019s the gap between the two that determines whether "
            "workers are getting ahead or falling behind."
        ),
    )

    # Three-line chart: wage_growth, inflation_rate, real_wage_growth.
    # The vertical band marks the quarter the reader has selected so the
    # KPIs below the chart make geographic sense at a glance.
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nat["quarter"], y=nat["wage_growth"],
        mode="lines+markers", name="Wage growth (QoQ %)",
        line=dict(color=PALETTE["wage"], width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Wage growth: %{y:+.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=nat["quarter"], y=nat["inflation_rate"],
        mode="lines+markers", name="Inflation (QoQ %)",
        line=dict(color=PALETTE["inflation"], width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Inflation: %{y:+.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=nat["quarter"], y=nat["real_wage_growth"],
        name="Real wage growth (gap)",
        marker_color=[
            PALETTE["positive"] if v > 0 else
            PALETTE["negative"] if v < 0 else PALETTE["muted"]
            for v in nat["real_wage_growth"]
        ],
        opacity=0.55,
        hovertemplate=("<b>%{x}</b><br>Real wage Δ: %{y:+.1f}%"
                       "<extra></extra>"),
    ))
    # Selected-quarter highlight: a vertical band the reader can scan to.
    fig.add_vrect(
        x0=selected_quarter, x1=selected_quarter,
        line=dict(color=PALETTE["highlight"], width=2, dash="dot"),
    )
    fig.update_layout(
        title=dict(
            text="Wages vs inflation — quarter-on-quarter, Australia",
            x=0, font=dict(size=16),
        ),
        bargap=0.45, yaxis_title="Per-quarter change (%)",
    )
    _apply_chart_theme(fig, height=460)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # KPI strip — these update as the reader changes the quarter.
    real_delta = sel_row["real_wage_growth"]
    delta_word = ("ahead of" if real_delta > 0
                  else "behind" if real_delta < 0
                  else "level with")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card(
            "Selected quarter", selected_quarter,
            "Adjust using the sidebar slider.",
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card(
            "Wage growth (QoQ)", f"{sel_row['wage_growth']:+.1f}%",
            "ABS Wage Price Index, all sectors.",
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card(
            "Inflation (QoQ)", f"{sel_row['inflation_rate']:+.1f}%",
            "ABS CPI, All Groups, weighted 8-cap-city avg.",
        ), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card(
            "Real wage change", f"{real_delta:+.1f}%",
            f"Workers were {delta_word} the cost of living.",
        ), unsafe_allow_html=True)


def section_what_state(df: pd.DataFrame, selected_quarter: str) -> None:
    """What — the spatial picture. Map of wage index by state for the
    selected quarter, plus a horizontal-bar comparison."""
    snapshot = df[df["quarter"] == selected_quarter].copy()
    snapshot = snapshot.set_index("state_code").loc[STATE_ORDER].reset_index()

    chapter_header(
        num=2, arc="What", anchor="ch2",
        title="Eight Australias, Eight Pay Stories",
        lede=(
            "National averages flatten everything. Tasmania pays "
            "differently from the ACT; Queensland tracks differently "
            "from Western Australia. The Wage Price Index "
            "by state shows where each jurisdiction has landed \u2014 and "
            "the spread between the highest and lowest matters, because "
            "national policy settings (minimum wage, pension rates, "
            "rent assistance) apply the same rate everywhere."
        ),
    )

    map_col, bar_col = st.columns([3, 2])

    with map_col:
        # Geo bubble map. Bubble size and colour both encode wage_index
        # — redundant encoding is intentional: it survives colour-blind
        # readers and prints in greyscale.
        fig = px.scatter_geo(
            snapshot,
            lat="latitude", lon="longitude",
            size="wage_index",
            color="wage_index",
            color_continuous_scale=[
                [0.0, "#fde68a"], [0.5, "#f59e0b"], [1.0, "#9a3412"],
            ],
            size_max=42,
            hover_name="state_name",
            custom_data=["state_code", "wage_index", "wage_growth",
                         "inflation_rate", "real_wage_growth"],
            projection="mercator",
        )
        fig.update_traces(hovertemplate=(
            "<b>%{hovertext}</b> (%{customdata[0]})<br>"
            "Wage Price Index: <b>%{customdata[1]:.1f}</b><br>"
            "Wage growth: %{customdata[2]:+.1f}%<br>"
            "Inflation: %{customdata[3]:+.1f}%<br>"
            "Real wage Δ: %{customdata[4]:+.1f}%<extra></extra>"
        ))
        fig.update_geos(
            visible=True, resolution=50,
            showcountries=True, countrycolor=PALETTE["rule"],
            showland=True, landcolor="#f1ede4",
            showocean=True, oceancolor="#e7e2d5",
            lataxis_range=[-44, -10], lonaxis_range=[112, 155],
        )
        fig.update_layout(
            title=dict(
                text=f"Wage Price Index by state — {selected_quarter}",
                x=0, y=0.97, yanchor="top", font=dict(size=16),
            ),
            coloraxis_colorbar=dict(title="WPI"),
            margin=dict(l=0, r=0, t=70, b=0), height=460,
            paper_bgcolor=PALETTE["paper"],
            font=dict(family="Georgia, serif", color=PALETTE["ink"]),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with bar_col:
        # Horizontal bar — same data as the map, but ranked. Maps show
        # geography; bars show ordering. Both views together is a Gestalt
        # similarity-by-position trick.
        sorted_snap = snapshot.sort_values("wage_index", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=sorted_snap["wage_index"], y=sorted_snap["state_code"],
            orientation="h",
            marker=dict(
                color=sorted_snap["wage_index"],
                colorscale=[[0.0, "#fde68a"], [1.0, "#9a3412"]],
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
        ))
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


def section_so_what_drivers(df: pd.DataFrame) -> None:
    """So What — what's actually driving inflation? Food, housing,
    transport CPI sub-indices over time. Stacked area shows shape;
    final-quarter horizontal bars show levels."""
    nat = national_series(df)

    chapter_header(
        num=3, arc="So What", anchor="ch3",
        title="Where the Money Actually Went",
        lede=(
            "When the news says \u201Cinflation was 0.6% this quarter,\u201D "
            "that\u2019s an average across hundreds of things. Some barely "
            "moved. Others spiked. For anyone paying rent, buying "
            "groceries, or commuting to work, the headline average "
            "understates what they\u2019re actually experiencing. Use the "
            "toggles below to see how each category compares to the "
            "overall average."
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
    fig.add_trace(go.Scatter(
        x=nat["quarter"], y=nat["inflation_rate"],
        mode="lines+markers", name="All Groups CPI (average)",
        line=dict(color=PALETTE["muted"], width=2, dash="dot"),
        marker=dict(size=5, symbol="circle-open"),
        hovertemplate="<b>%{x}</b><br>All Groups CPI: %{y:+.1f}%<extra></extra>",
    ))
    categories_config = [
        ("housing", "Housing", PALETTE["housing"], show_housing),
        ("food", "Food & non-alcoholic beverages", PALETTE["food"], show_food),
        ("transport", "Transport", PALETTE["transport"], show_transport),
    ]

    any_selected = show_housing or show_food or show_transport

    for col, name, color, is_visible in categories_config:
        if is_visible:
            fig.add_trace(go.Scatter(
                x=nat["quarter"], y=nat[col],
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=3),
                marker=dict(size=8),
                hovertemplate=(
                    f"<b>%{{x}}</b><br>{name}: %{{y:+.1f}}%<extra></extra>"
                ),
            ))

    # If nothing is toggled, show all categories faintly as a preview
    if not any_selected:
        for col, name, color, _ in categories_config:
            fig.add_trace(go.Scatter(
                x=nat["quarter"], y=nat[col],
                mode="lines",
                name=name,
                line=dict(color=color, width=1.5, dash="dot"),
                opacity=0.35,
                hovertemplate=(
                    f"<b>%{{x}}</b><br>{name}: %{{y:+.1f}}%<extra></extra>"
                ),
            ))

    chart_title = "CPI by category \u2014 quarter-on-quarter change"
    if any_selected:
        selected_names = []
        if show_housing:
            selected_names.append("Housing")
        if show_food:
            selected_names.append("Food")
        if show_transport:
            selected_names.append("Transport")
        chart_title = (
            f"{', '.join(selected_names)} vs All Groups average"
        )

    fig.update_layout(
        title=dict(text=chart_title, x=0, font=dict(size=16)),
        yaxis_title="Quarter-on-quarter change (%)",
    )
    _apply_chart_theme(fig, height=440)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # --- KPI cards for selected quarter ---
    sel_row = nat[nat["quarter"] == selected_quarter].iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card(
            "Selected quarter", selected_quarter,
            "Adjust using the sidebar slider.",
        ), unsafe_allow_html=True)
    with k2:
        housing_vs_avg = sel_row["housing"] - sel_row["inflation_rate"]
        st.markdown(kpi_card(
            "🏠 Housing", f"{sel_row['housing']:+.1f}%",
            f"{housing_vs_avg:+.1f}% vs All Groups average.",
        ), unsafe_allow_html=True)
    with k3:
        food_vs_avg = sel_row["food"] - sel_row["inflation_rate"]
        st.markdown(kpi_card(
            "🛒 Food", f"{sel_row['food']:+.1f}%",
            f"{food_vs_avg:+.1f}% vs All Groups average.",
        ), unsafe_allow_html=True)
    with k4:
        transport_vs_avg = sel_row["transport"] - sel_row["inflation_rate"]
        st.markdown(kpi_card(
            "🚗 Transport", f"{sel_row['transport']:+.1f}%",
            f"{transport_vs_avg:+.1f}% vs All Groups average.",
        ), unsafe_allow_html=True)

    # --- Cumulative summary ---
    cum_food = nat["food"].sum()
    cum_housing = nat["housing"].sum()
    cum_transport = nat["transport"].sum()
    cum_all = nat["inflation_rate"].sum()
    housing_gap = abs(cum_housing - cum_all)

    st.markdown(
        f'<div class="pull-quote">Over nine quarters, housing costs rose '
        f"a total of <strong>{cum_housing:+.1f}%</strong>, food "
        f"<strong>{cum_food:+.1f}%</strong>, and transport "
        f"<strong>{cum_transport:+.1f}%</strong> \u2014 but the overall "
        f"average used to adjust government payments was only "
        f"<strong>{cum_all:+.1f}%</strong>. That means rent assistance "
        f"adjustments have lagged actual housing costs by roughly "
        f"<strong>{housing_gap:.1f} percentage points</strong> "
        f"over this period.</div>",
        unsafe_allow_html=True,
    )

    # --- So What transition moment ---
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    st.markdown(
        '<p class="narrative" style="font-size:1.25rem; font-weight:600; '
        'color:#1f2937; max-width:60ch; margin: 1rem 0;">'
        f"Real wage growth over nine quarters: "
        f"<strong>{nat['real_wage_growth'].sum():+.1f}%</strong>. "
        f"Housing costs over the same period: "
        f"<strong>{cum_housing:+.1f}%</strong>. "
        "The payslip grew. What it buys \u2014 especially for anyone "
        "paying rent \u2014 didn\u2019t keep up. The question isn\u2019t whether "
        "the gap exists. It\u2019s when and how it closes."
        "</p>",
        unsafe_allow_html=True,
    )

    # Cumulative impact sentence — strongest single line in the section.
    cum_food = nat["food"].sum()
    cum_housing = nat["housing"].sum()
    cum_transport = nat["transport"].sum()
    cum_all = nat["inflation_rate"].sum()
    st.markdown(
        f'<div class="pull-quote">Over nine quarters, housing prices '
        f"climbed a cumulative <strong>{cum_housing:+.1f}%</strong>, food "
        f"<strong>{cum_food:+.1f}%</strong>, and transport "
        f"<strong>{cum_transport:+.1f}%</strong> — against a headline CPI "
        f"of <strong>{cum_all:+.1f}%</strong>. The averages hide the "
        f"categories that hurt most.</div>",
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
        num=4, arc="What Next", anchor="ch4",
        title="When Do Real Wages Recover?",
        lede=(
            "Use the sliders below to set a hypothetical wage growth "
            "rate and inflation rate for the next two years. The dashed "
            "line shows where cumulative real wages would end up under "
            "your scenario \u2014 starting from where the actual data "
            "leaves off."
        ),
    )

    # Preset scenarios — saves the busy reader from picking three numbers.
    # Each preset writes the same session_state keys the sliders use, so
    # the next rerun shows the preset values in the controls. We use one
    # key namespace (no `value=` on the widgets) because mixing `value=`
    # and `key=` on a Streamlit widget makes preset clicks silently fail.
    PRESETS = {
        "RBA-aligned":  dict(scen_wage=0.9, scen_inflation=0.6, scen_target=3.0),
        "Optimistic":   dict(scen_wage=1.2, scen_inflation=0.5, scen_target=3.0),
        "Pessimistic":  dict(scen_wage=0.6, scen_inflation=1.1, scen_target=3.0),
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

    cw, ci, ct = st.columns([1, 1, 1])
    with cw:
        scen_wage = st.slider(
            "Hypothetical quarterly wage growth (%)",
            min_value=0.0, max_value=2.0, step=0.1,
            help="Average QoQ wage growth across the period was about 0.85%.",
            key="scen_wage",
        )
    with ci:
        scen_inflation = st.slider(
            "Hypothetical quarterly inflation (%)",
            min_value=0.0, max_value=2.0, step=0.1,
            help="Average QoQ inflation across the period was about 0.7%.",
            key="scen_inflation",
        )
    with ct:
        target = st.number_input(
            "Recovery target — cumulative real-wage gain (%)",
            min_value=-5.0, max_value=10.0, step=0.5,
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
        future_quarters.append(f"{last_year} Q{last_qn}")

    scen_real = scen_wage - scen_inflation
    proj_cum = [cum_so_far + scen_real * (i + 1) for i in range(horizon)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nat["quarter"], y=nat["real_wage_growth"].cumsum(),
        mode="lines+markers", name="Actual cumulative real wage",
        line=dict(color=PALETTE["wage"], width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Cumulative: %{y:+.1f}%<extra></extra>",
    ))
    # Bridge the last actual point to the first projected point so the
    # line is visually unbroken.
    fig.add_trace(go.Scatter(
        x=[nat["quarter"].iloc[-1]] + future_quarters,
        y=[cum_so_far] + proj_cum,
        mode="lines+markers", name="Your scenario",
        line=dict(color=PALETTE["highlight"], width=3, dash="dash"),
        marker=dict(size=8, symbol="diamond"),
        hovertemplate="<b>%{x}</b><br>Projected cumulative: %{y:+.1f}%<extra></extra>",
    ))
    fig.add_hline(
        y=target, line=dict(color=PALETTE["positive"], width=1.5, dash="dot"),
        annotation_text=f"Recovery target: {target:+.1f}%",
        annotation_position="top right",
        annotation_font_color=PALETTE["positive"],
    )
    fig.update_layout(
        title=dict(
            text="Cumulative real-wage growth — actual + your scenario",
            x=0, font=dict(size=16),
        ),
        yaxis_title="Cumulative real wage Δ since 2023 Q4 (%)",
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
        f'<div class="pull-quote">{verdict}</div>', unsafe_allow_html=True,
    )


def section_call_to_action() -> None:
    """Closing — 3 recomendations for the Treasury analyst."""
    nat = national_series(df)
    cum_housing = nat["housing"].sum()
    cum_all = nat["inflation_rate"].sum()
    housing_gap = abs(cum_housing - cum_all)

    chapter_header(
        num=5, arc="What Next", anchor="ch5",
        title="What Should Change?",
        lede=(
            "The data across the previous four chapters points to a "
            "clear mismatch: the way government payments are adjusted "
            "for inflation doesn\u2019t reflect the actual cost pressures "
            "households face \u2014 especially on housing."
        ),
    )

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        st.markdown(
            '<div class="policy-rec">'
            '<div class="rec-label">Recommendation 1: Fix the adjustment formula</div>'
            '<div class="rec-body">'
            "Government payments like rent assistance, JobSeeker, and the "
            "Age Pension are currently adjusted based on the overall "
            "inflation average. But housing costs have risen "
            f"<strong>{cum_housing:+.1f}%</strong> over this period — "
            f"<strong>{housing_gap:.1f} percentage points</strong> above "
            "that average. <br><br> The adjustment formula should be reviewed to "
            "account for the specific costs that hit hardest, not just "
            "the average across everything."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown(
            '<div class="policy-rec">'
            '<div class="rec-label">Recommendation 2: Account for state differences</div>'
            '<div class="rec-body">'
            "The wage index varies significantly across states — as shown "
            "in Chapter 2. But the minimum wage and payment rates are set "
            "nationally. <br><br> Treasury should model what it would look like to "
            "adjust payment rates by state, so that the same dollar amount "
            "doesn't mean very different things in Tasmania versus the ACT."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with r3:
        st.markdown(
            '<div class="policy-rec">'
            '<div class="rec-label">Recommendation 3: Track the gap, not just the number</div>'
            '<div class="rec-body">'
            "Currently, the Cost-of-Living desk tracks wage growth and "
            "inflation separately. The gap between them — real wage growth "
            "— should be a standing metric in every quarterly report. <br><br> The "
            "scenario tool in Chapter 4 shows how this could work in "
            "practice: set a recovery target, model different paths, "
            "and track whether policy is closing the gap or widening it."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    df = load_data()
    nat = national_series(df)
    quarters = nat["quarter"].tolist()

    # Sidebar = global story controls. Kept narrow on purpose — it's a
    # nudge, not a dashboard panel. The quarter slider is the single
    # control that drives the map + KPI tiles in Chapter 2.
    with st.sidebar:
        st.markdown("### Story controls")
        st.markdown(
            '<p style="color:#6b7280;font-size:0.9rem;">'
            "Move the slider to change the spotlight quarter on the "
            "national timeline and the state map."
            "</p>",
            unsafe_allow_html=True,
        )
        selected_quarter = st.select_slider(
            "Spotlight quarter", options=quarters, value=quarters[-1],
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
                "- Coverage: **2023 Q4 → 2025 Q4**, 8 states/territories\n"
                "- Joining: WPI per state + national CPI broadcast across "
                "states in long format. See README for full data dictionary."
            )

        st.markdown("---")
        st.markdown(
            '<p style="color:#6b7280;font-size:0.85rem;">'
            "Built for UTS Data Visualisation Asm3.<br>"
            "<strong>Narrative arc:</strong> What → So What → What Next."
            "</p>",
            unsafe_allow_html=True,
        )

    chapter_nav()
    section_hero(df)
    section_tldr(df)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    section_what_national(df, selected_quarter)
    section_what_state(df, selected_quarter)
    section_so_what_drivers(df)
    section_what_next_whatif(df)
    section_call_to_action()


if __name__ == "__main__":
    main()
