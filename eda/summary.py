"""
This module provides functions to summarise the EDA process, including key findings and insights derived from the data analysis.
"""
def get_key_metrics(df):
    nat = df.drop_duplicates("quarter_date")

    return {
        "avg_real_wage": nat["real_wage_growth"].mean(),
        "latest_real_wage": nat.sort_values("quarter_date").iloc[-1]["real_wage_growth"],
        "avg_inflation": nat["inflation_rate"].mean()
    }