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
      .block-container { padding-top: 2.5rem; padding-bottom: 4rem; max-width: 1200px; }
      h1, h2, h3 { font-family: Georgia, "Times New Roman", serif; letter-spacing: -0.01em; }
      h1 { font-size: 3.0rem !important; line-height: 1.1; margin-bottom: 0.5rem; }
      h2 { font-size: 2.0rem !important; margin-top: 2.5rem; }
      h3 { font-size: 1.35rem !important; }
      .hero-kicker {
        text-transform: uppercase; letter-spacing: 0.18em;
        color: #6b7280; font-size: 0.85rem; font-weight: 600;
        margin-bottom: 0.5rem;
      }
      .hero-stat {
        font-family: Georgia, serif; font-size: 4.5rem; line-height: 1;
        color: #dc2626; font-weight: 700; margin: 0.25rem 0;
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
      .section-divider {
        height: 1px; background: #d1d5db; margin: 3rem 0 2rem 0;
        border: none;
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
        "Between late 2023 and the end of 2025, the headlines told a "
        "reassuring story: wages were growing. The number on your payslip "
        "was getting bigger. And yet, for most Australians, life kept "
        "getting more expensive faster than the paycheck could keep up. "
        "This is the gap between the <em>nominal</em> wage and the "
        "<em>real</em> wage — and over nine quarters, that gap has a shape."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="hero-stat">{n_negative} of {n_total}</div>'
        '<p class="narrative" style="margin-top:-0.5rem;">'
        "quarters in which the average Australian worker went "
        "<strong>backwards</strong> in real terms — wage growth slower than "
        f"inflation. Cumulative real wage growth across the period: "
        f"<strong>{cum_real:+.1f}%</strong>."
        "</p>",
        unsafe_allow_html=True,
    )


def section_what_national(df: pd.DataFrame, selected_quarter: str) -> None:
    """What — the national picture. Wage growth vs inflation timeline,
    with a highlighted marker at the user-selected quarter."""
    nat = national_series(df)
    sel_row = nat[nat["quarter"] == selected_quarter].iloc[0]

    st.markdown("## Chapter 1 — The Headline Number Lies")
    st.markdown(
        '<p class="narrative">'
        "ABS publishes two numbers every quarter. The Wage Price Index "
        "tells you how fast pay is rising. The Consumer Price Index tells "
        "you how fast your shopping basket is rising. Most reporting "
        "quotes one or the other in isolation. The story emerges when "
        "you put them on the same axis."
        "</p>",
        unsafe_allow_html=True,
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
            "Use the sidebar slider to scrub.",
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card(
            "Wage growth (QoQ)", f"{sel_row['wage_growth']:+.1f}%",
            "ABS WPI, all sectors, original.",
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card(
            "Inflation (QoQ)", f"{sel_row['inflation_rate']:+.1f}%",
            "ABS CPI, All Groups, weighted 8-cap-city avg.",
        ), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card(
            "Real wage Δ", f"{real_delta:+.1f}%",
            f"Workers were {delta_word} the cost of living.",
        ), unsafe_allow_html=True)


def section_what_state(df: pd.DataFrame, selected_quarter: str) -> None:
    """What — the spatial picture. Map of wage index by state for the
    selected quarter, plus a horizontal-bar comparison."""
    snapshot = df[df["quarter"] == selected_quarter].copy()
    snapshot = snapshot.set_index("state_code").loc[STATE_ORDER].reset_index()

    st.markdown("## Chapter 2 — Eight Australias, Eight Pay Stories")
    st.markdown(
        '<p class="narrative">'
        "National averages flatten everything. Tasmania pays differently "
        "from the ACT; Queensland tracks differently from Western "
        "Australia. The Wage Price Index — re-based to 100 in Sep 2008 "
        "— shows where each state has gotten to. Hover any bubble for "
        "the full numbers."
        "</p>",
        unsafe_allow_html=True,
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

    st.markdown("## Chapter 3 — Where the Money Actually Went")
    st.markdown(
        '<p class="narrative">'
        "When CPI says \"inflation was 0.6% this quarter,\" that 0.6% is "
        "an average across hundreds of categories. Some are flat. Some "
        "are catastrophic. For renters and commuters, the headline rate "
        "underweights the line items that actually determine whether the "
        "month ends in the black."
        "</p>",
        unsafe_allow_html=True,
    )

    fig = go.Figure()
    for col, name in [("housing", "Housing"),
                      ("food", "Food & non-alc."),
                      ("transport", "Transport")]:
        fig.add_trace(go.Scatter(
            x=nat["quarter"], y=nat[col],
            mode="lines+markers",
            name=name,
            line=dict(color=PALETTE[col], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:+.1f}}%<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=nat["quarter"], y=nat["inflation_rate"],
        mode="lines", name="All Groups CPI",
        line=dict(color=PALETTE["ink"], width=2, dash="dash"),
        hovertemplate="<b>%{x}</b><br>All Groups CPI: %{y:+.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text="QoQ % change — CPI sub-categories vs headline",
            x=0, font=dict(size=16),
        ),
        yaxis_title="QoQ % change",
    )
    _apply_chart_theme(fig, height=440)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

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

    st.markdown("## Chapter 4 — When Do Real Wages Recover?")
    st.markdown(
        '<p class="narrative">'
        "Pull the levers below to set a quarterly wage-growth and "
        "inflation rate for the next two years. The dashed line shows "
        "where cumulative real wages end up under your scenario, "
        "starting from where the actual data leaves off."
        "</p>",
        unsafe_allow_html=True,
    )

    cw, ci, ct = st.columns([1, 1, 1])
    with cw:
        scen_wage = st.slider(
            "Hypothetical quarterly wage growth (%)",
            min_value=0.0, max_value=2.0, value=0.9, step=0.1,
            help="Average QoQ wage growth across the period was about 0.85%.",
        )
    with ci:
        scen_inflation = st.slider(
            "Hypothetical quarterly inflation (%)",
            min_value=0.0, max_value=2.0, value=0.7, step=0.1,
            help="Average QoQ inflation across the period was about 0.7%.",
        )
    with ct:
        target = st.number_input(
            "Recovery target — cumulative real-wage gain (%)",
            min_value=-5.0, max_value=10.0, value=3.0, step=0.5,
            help="How much cumulative real-wage growth counts as 'recovered'?",
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
    """Closing — three stakeholder lenses on the same story."""
    st.markdown("## Chapter 5 — So What Should Anyone Do About It?")
    st.markdown(
        '<p class="narrative">'
        "The same data carries a different obligation depending on whose "
        "desk it lands on."
        "</p>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "### For the policymaker\n"
            "Headline wage growth is not a substitute for real income "
            "growth. Forecasts should track the gap, not just the "
            "numerator. Sub-category CPI is where rent assistance and "
            "fuel-tax decisions live."
        )
    with c2:
        st.markdown(
            "### For the journalist\n"
            "\"Wages up 0.7%\" is not the headline. The headline is the "
            "delta against inflation, and the delta against the categories "
            "your readers actually spend on. Lead with the gap."
        )
    with c3:
        st.markdown(
            "### For the household\n"
            "Your perception that things got harder is not vibes. Across "
            "nine quarters, real wages crawled. The recovery, if it comes, "
            "depends on which of the three sliders above moves."
        )

    st.markdown(
        '<p class="narrative" style="margin-top:2rem;">'
        "<strong>Data:</strong> Australian Bureau of Statistics — Wage "
        "Price Index (cat. 6345.0) and Consumer Price Index (cat. 6401.0), "
        "joined per state/territory. See <code>data/wage_inflation.csv</code> "
        "and the README data dictionary for full provenance."
        "</p>",
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
            "Scrub the slider to move the spotlight quarter on the "
            "national timeline and the state map."
            "</p>",
            unsafe_allow_html=True,
        )
        selected_quarter = st.select_slider(
            "Spotlight quarter", options=quarters, value=quarters[-1],
        )
        st.markdown("---")
        st.markdown(
            '<p style="color:#6b7280;font-size:0.85rem;">'
            "Built for UTS Data Visualisation Asm3.<br>"
            "<strong>Narrative arc:</strong> What → So What → What Next."
            "</p>",
            unsafe_allow_html=True,
        )

    section_hero(df)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    section_what_national(df, selected_quarter)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    section_what_state(df, selected_quarter)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    section_so_what_drivers(df)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    section_what_next_whatif(df)
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    section_call_to_action()


if __name__ == "__main__":
    main()
