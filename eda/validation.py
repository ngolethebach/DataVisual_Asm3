"""
Data validation module for EDA.
This module provides functions to validate the integrity and consistency of the merged dataset.
"""

def validate_schema(df):
    """
    Validate the schema of the dataset.
    """
    required_columns = ['quarter_date', 'quarter', 'year', 'quarter_num', 'state_code',
       'state_name', 'latitude', 'longitude', 'wage_index', 'inflation_rate',
       'wage_growth', 'real_wage_growth', 'food', 'housing', 'transport']

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")
    else:
        return 'Schema Validated'

def validate_no_nulls(df):
    if df.isnull().sum().sum() > 0:
        return "Warning: Dataset contains missing values."
    return "No missing values detected."

def validate_ranges(df):
    if (df["inflation_rate"].abs() > 10).any():
        return "Unusual inflation values detected."
    return "Values within expected range."
