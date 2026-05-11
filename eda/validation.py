"""
Data validation module for the wage vs inflation narrative dataset.

Purpose
-------
These validation checks are designed to verify not only that the merged
dataset is structurally correct, but also that the downstream Streamlit
visualisations and narrative claims accurately reflect the underlying ABS
source data.

Validation layers
-----------------
1. Structural integrity
   - schema
   - nulls
   - duplicate coverage
   - quarter continuity

2. Join integrity
   - national-value broadcasting consistency
   - state-level variation correctness
   - derived metric correctness

3. Source reconciliation
   - final CSV values match ABS source spreadsheets

4. Narrative / visual integrity
   - chart-driving metrics correctly derived
   - timeline continuity
   - map geometry plausibility

Any failure raises immediately with a targeted error message explaining
which analytical component or visual narrative may be invalid.
"""


import pandas as pd

# ----------------------------------------------------
# SCHEMA + STRUCTURE VALIDATION
# ----------------------------------------------------

REQUIRED_COLUMNS = [
    'quarter_date',
    'quarter',
    'year',
    'quarter_num',
    'state_code',
    'state_name',
    'latitude',
    'longitude',
    'wage_index',
    'inflation_rate',
    'wage_growth',
    'real_wage_growth',
    'food',
    'housing',
    'transport'
]

EXPECTED_QUARTERS = [
    '2023 Q4',
    '2024 Q1',
    '2024 Q2',
    '2024 Q3',
    '2024 Q4',
    '2025 Q1',
    '2025 Q2',
    '2025 Q3',
    '2025 Q4'
]

EXPECTED_STATES = [
    'NSW',
    'VIC',
    'QLD',
    'SA',
    'WA',
    'TAS',
    'NT',
    'ACT'
]

def validate_schema(df):
    """
    Validate dataset schema and required analytical columns.

    Risk if failed:
    ----------------
    Downstream charts, joins, or narrative calculations may silently fail
    or render incorrect outputs.
    """

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        raise ValueError(
            f"[Schema] Missing required columns:\n{missing}\n\n"
            "Narrative charts and derived metrics may be incomplete."
        )

    return "Schema validated."


def validate_no_nulls(df):
    """
    Ensure no missing values exist in the analytical dataset.

    Risk if failed:
    ----------------
    Streamlit charts may silently drop rows or distort trends.
    """

    nulls = df.isnull().sum()
    bad = nulls[nulls > 0]

    if not bad.empty:
        raise ValueError(
            "[Null Integrity] Missing values detected:\n"
            f"{bad.to_string()}\n\n"
            "Visualisations may omit data points or misrepresent trends."
        )

    return "No missing values detected."


def validate_quarter_coverage(df):
    """
    Validate complete quarter × state coverage.

    Expected:
        9 quarters × 8 states = 72 rows

    Risk if failed:
    ----------------
    State maps or timelines may exclude regions or duplicate values.
    """

    missing = []

    for q in EXPECTED_QUARTERS:
        for s in EXPECTED_STATES:
            subset = df[
                (df['quarter'] == q) &
                (df['state_code'] == s)
            ]

            if subset.empty:
                missing.append(f"{q} × {s}")

    duplicates = df[
        df.duplicated(['quarter', 'state_code'], keep=False)
    ]

    issues = []

    if missing:
        issues.append(
            "Missing quarter/state combinations:\n"
            + "\n".join(missing)
        )

    if not duplicates.empty:
        issues.append(
            "Duplicate quarter/state rows detected:\n"
            + duplicates[['quarter', 'state_code']].to_string()
        )

    if issues:
        raise ValueError(
            "[Coverage Integrity]\n"
            + "\n\n".join(issues)
            + "\n\nState-level visualisations may be unreliable."
        )

    return "Quarter coverage validated — 72 expected rows confirmed."

# ----------------------------------------------------
# BROADCAST + JOIN VALIDATION
# ----------------------------------------------------

def validate_broadcast_consistency(df):
    """
    Validate that national ABS metrics were correctly broadcast across
    all state rows within each quarter.

    National metrics should be identical across states because:
        - CPI is national
        - wage_growth is national

    Risk if failed:
    ----------------
    State comparisons become analytically invalid.
    """

    national_cols = [
        'inflation_rate',
        'wage_growth',
        'real_wage_growth',
        'food',
        'housing',
        'transport'
    ]

    failures = []

    for quarter, group in df.groupby('quarter'):

        for col in national_cols:

            if group[col].nunique() > 1:
                failures.append(
                    f"{quarter} | {col} varies across states "
                    "(expected identical national values)"
                )

    if failures:
        raise ValueError(
            "[Broadcast Join Failure]\n"
            + "\n".join(failures)
            + "\n\nNational metrics were incorrectly joined."
        )

    return "Broadcast consistency validated."


def validate_state_variation(df):
    """
    Validate that wage_index correctly varies by state.

    wage_index is the ONLY metric expected to vary spatially.

    Risk if failed:
    ----------------
    Geographic visualisations become meaningless.
    """

    failures = []

    for quarter, group in df.groupby('quarter'):

        if group['wage_index'].nunique() == 1:
            failures.append(
                f"{quarter} | wage_index identical across all states"
            )

    if failures:
        raise ValueError(
            "[Spatial Variation Failure]\n"
            + "\n".join(failures)
            + "\n\nState maps would render as artificially flat."
        )

    return "State-level wage variation validated."


def validate_real_wage_formula(df, tolerance=0.01):
    """
    Validate:
        real_wage_growth = wage_growth - inflation_rate

    Risk if failed:
    ----------------
    The central narrative claim becomes invalid.
    """

    expected = (
        df['wage_growth'] - df['inflation_rate']
    ).round(4)

    actual = df['real_wage_growth'].round(4)

    diff = (expected - actual).abs()

    bad = df[diff > tolerance]

    if not bad.empty:

        out = bad[
            [
                'quarter',
                'state_code',
                'wage_growth',
                'inflation_rate',
                'real_wage_growth'
            ]
        ].copy()

        out['expected_real_wage_growth'] = expected[diff > tolerance]

        raise ValueError(
            "[Derived Metric Failure]\n"
            "real_wage_growth incorrectly calculated:\n\n"
            f"{out.to_string()}\n\n"
            "Chapter 1 narrative calculations are unreliable."
        )

    return "real_wage_growth formula validated."

# ----------------------------------------------------
# SOURCE RECONCILIATION
# ----------------------------------------------------

def validate_wage_growth_against_abs(
    final_df,
    abs_df,
    quarter_col,
    value_col,
    tolerance=0.05
):
    """
    Validate wage_growth values against ABS 634501 source spreadsheet.

    Risk if failed:
    ----------------
    National wage timeline may not reflect published ABS values.
    """

    failures = []

    national = (
        final_df
        .groupby('quarter')
        .first()
        .reset_index()
    )

    for _, row in national.iterrows():

        q = row['quarter']
        actual = row['wage_growth']

        src = abs_df[abs_df[quarter_col] == q]

        if src.empty:
            failures.append(f"{q} missing from ABS source")
            continue

        expected = float(src[value_col].iloc[0])

        if abs(actual - expected) > tolerance:
            failures.append(
                f"{q} | expected {expected}, got {actual}"
            )

    if failures:
        raise ValueError(
            "[ABS Reconciliation Failure — wage_growth]\n"
            + "\n".join(failures)
        )

    return "ABS wage_growth reconciliation validated."


def validate_cpi_against_abs(
    final_df,
    abs_df,
    mapping,
    quarter_col,
    tolerance=0.05
):
    """
    Validate CPI metrics against ABS 6401018 source spreadsheet.

    mapping example:
    {
        'inflation_rate': 'All Groups',
        'food': 'Food',
        'housing': 'Housing',
        'transport': 'Transport'
    }
    """

    failures = []

    national = (
        final_df
        .groupby('quarter')
        .first()
        .reset_index()
    )

    for final_col, abs_col in mapping.items():

        for _, row in national.iterrows():

            q = row['quarter']
            actual = row[final_col]

            src = abs_df[abs_df[quarter_col] == q]

            if src.empty:
                failures.append(f"{q} missing from ABS source")
                continue

            expected = float(src[abs_col].iloc[0])

            if abs(actual - expected) > tolerance:
                failures.append(
                    f"{q} | {final_col} "
                    f"expected {expected}, got {actual}"
                )

    if failures:
        raise ValueError(
            "[ABS Reconciliation Failure — CPI]\n"
            + "\n".join(failures)
        )

    return "ABS CPI reconciliation validated."

# ----------------------------------------------------
# VISUAL VALIDATION
# ----------------------------------------------------

def validate_map_geometry(df):
    """
    Validate Australian map coordinates.

    Risk if failed:
    ----------------
    Geographic charts may render incorrectly or place states offshore.
    """

    failures = []

    for _, row in df.iterrows():

        lat = row['latitude']
        lon = row['longitude']

        if not (-45 <= lat <= -10):
            failures.append(
                f"{row['state_code']} invalid latitude: {lat}"
            )

        if not (110 <= lon <= 160):
            failures.append(
                f"{row['state_code']} invalid longitude: {lon}"
            )

    if failures:
        raise ValueError(
            "[Map Geometry Failure]\n"
            + "\n".join(failures)
        )

    return "Map geometry validated."

def validate_datetime_columns(df):

    try:
        pd.to_datetime(df['quarter_date'])
    except Exception:
        raise ValueError(
            "[Datetime Failure]\n"
            "quarter_date could not be parsed as datetime."
        )

    return "Datetime parsing validated."


def validate_timeline_order(df):
    """
    Validate chronological continuity of quarter_date.

    Risk if failed:
    ----------------
    Time-series charts may render out-of-order trends.
    """

    dates = (
        pd.to_datetime(df['quarter_date'])
        .drop_duplicates()
        .sort_values()
    )

    gaps = dates.diff().dropna()

    bad = gaps[gaps > pd.Timedelta(days=185)]

    if not bad.empty:

        raise ValueError(
            "[Timeline Continuity Failure]\n"
            f"Quarter gaps detected:\n{bad.to_string()}\n\n"
            "Trend charts may skip quarters."
        )

    return "Timeline continuity validated."

# ----------------------------------------------------
# MASTER VALIDATION PIPELINE
# ----------------------------------------------------


def validate_all(df):

    checks = [
        validate_schema,
        validate_no_nulls,
        validate_quarter_coverage,
        validate_broadcast_consistency,
        validate_state_variation,
        validate_real_wage_formula,
        validate_map_geometry,
        validate_datetime_columns,
        validate_timeline_order,
    ]

    results = []

    for fn in checks:

        result = fn(df)

        results.append({
            "validation": fn.__name__,
            "status": "PASS",
            "message": result
        })

    return pd.DataFrame(results)
