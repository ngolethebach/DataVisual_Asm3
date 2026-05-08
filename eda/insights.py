"""
This module provides functions for EDA process, including key findings and insights derived from the data analysis.
"""
from .features import get_national

def insight_real_wage_gap(df):
    """
    Insight: Real wage grow pattern across quarters.
    """
    nat = get_national(df)
    avg = nat["real_wage_growth"].mean()

    if avg < -0.5:
        message = "Households are experiencing sustained declines in purchasing power as wages fail to keep up with inflation."
        severity = "high"
    elif avg < 0:
        message = "Real wages are slightly declining, indicating a gradual erosion of purchasing power."
        severity = "medium"
    else:
        message = "Real wages are keeping pace with inflation, suggesting stable purchasing power."
        severity = "low"

    return {
        "title": "Are wages keeping up?",
        "value": round(avg, 2),
        "message": message,
        "visual": "line_chart_wage_vs_inflation",
        "severity": severity
    }

def insight_sparkline_gap(df):
    """
    Sparkline gap between wage growth and inflation.
    """
    nat = get_national(df)
    gap = (nat["inflation_rate"] - nat["wage_growth"]).mean()

    if gap > 0:
        message = (
            f"Inflation exceeds wage growth by an average of {gap:.2f} percentage points per quarter. "
            "Closing this gap is essential to restore real income growth."
        )
    else:
        message = (
            f"Wage growth exceeds inflation by an average of {abs(gap):.2f} percentage points per quarter. "
            "This suggests improving purchasing power for households."
        )

    return {
        "title": "The Wage–Inflation Gap",
        "value": round(gap, 2),
        "message": message,
        "visual": "gap_highlight_line_chart",
        "severity": "high" if gap > 0.5 else "medium"
    }

def insight_inflation_drivers(df):
    """
    Category: Inflation drivers by category.
    """
    nat = get_national(df)

    drivers = {
        "food": nat["food"].mean(),
        "housing": nat["housing"].mean(),
        "transport": nat["transport"].mean()
    }

    top = max(drivers, key=drivers.get)

    return {
        "title": "What’s driving inflation?",
        "value": round(drivers[top], 2),
        "message": (
            f"{top.capitalize()} is the largest contributor to inflation, rising faster than other categories "
            "and placing the most pressure on household budgets."
        ),
        "visual": "category_bar_chart",
        "severity": "high"
    }

def insight_state_gap(df):
    """
    State gap in wage index.
    """
    state_avg = df.groupby("state_code")["wage_index"].mean()

    worst = state_avg.idxmin()
    best = state_avg.idxmax()
    gap = state_avg.max() - state_avg.min()

    return {
        "title": "Are all states affected equally?",
        "value": round(gap, 2),
        "message": (
            f"There is a {gap:.2f} index point gap in wage levels between states. "
            f"{worst} has the lowest wage index, while {best} is the highest, indicating regional inequality."
        ),
        "visual": "state_map_or_bar",
        "severity": "medium" if gap < 5 else "high"
    }

def insight_persistence(df):
    """
    Persistence of real wage growth. Structural vs temporary?
    """
    nat = df.drop_duplicates("quarter_date").sort_values("quarter_date")
    recent = nat.tail(4)

    negative = (recent["real_wage_growth"] < 0).sum()

    if negative >= 3:
        message = "Real wage decline has persisted across multiple quarters, suggesting a structural economic issue."
        severity = "high"
    else:
        message = "Real wage trends show mixed outcomes, indicating short-term volatility rather than sustained decline."
        severity = "medium"

    return {
        "title": "Is this temporary or structural?",
        "value": int(negative),
        "message": message,
        "visual": "trend_line_recent",
        "severity": severity
    }

def insight_what_if(df, wage_increase):
    """
    Calculate the impact of a hypothetical wage increase on real wage growth.
    """
    nat = get_national(df)

    adjusted = nat["wage_growth"] + wage_increase
    new_real = (adjusted - nat["inflation_rate"]).mean()

    if new_real > 0:
        message = f"A {wage_increase:.1f}% wage increase would restore positive real wage growth."
        severity = "low"
    else:
        message = f"A {wage_increase:.1f}% wage increase would still be insufficient to offset inflation."
        severity = "high"

    return {
        "title": "What if wages increased?",
        "value": round(new_real, 2),
        "message": message,
        "visual": "what_if_slider_chart",
        "severity": severity
    }

def insight_policy_signal(df):
    nat = get_national(df)
    avg = nat["real_wage_growth"].mean()

    if avg < -1:
        message = "Urgent policy intervention is required to address sustained declines in purchasing power."
        severity = "high"
    elif avg < 0:
        message = "Targeted policy responses may be needed to stabilise household purchasing power."
        severity = "medium"
    else:
        message = "No immediate intervention is required, but continued monitoring is recommended."
        severity = "low"

    return {
        "title": "What does this mean for policy?",
        "value": round(avg, 2),
        "message": message,
        "visual": "final_summary_block",
        "severity": severity
    }