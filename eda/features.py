"""
This module provides features that supports in building insights.
"""

def get_national(df):
    return df.drop_duplicates("quarter_date")

def get_latest(df):
    return df[df["quarter_date"] == df["quarter_date"].max()]

def compute_wage_gap(df):
    nat = get_national(df)
    return nat["inflation_rate"] - nat["wage_growth"]