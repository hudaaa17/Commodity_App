import pandas as pd


def get_commodity_series(df, commodity):
    """
    Extracts a single commodity time series from forecast DataFrame.

    Input:
        df → full forecast DataFrame
        commodity → column name (e.g. "Zinc", "CPO")

    Output:
        DataFrame with:
        Date | price
    """

    if df.empty:
        raise ValueError("Forecast DataFrame is empty")

    # ----------------------------
    # Normalize column matching
    # ----------------------------
    cols = {c.lower(): c for c in df.columns}

    if commodity.lower() not in cols:
        print(f"⚠️ {commodity} column not found → skipping")
        return pd.DataFrame()
    
    actual_col = cols[commodity.lower()]

    # ----------------------------
    # Extract series
    # ----------------------------
    df_out = df[["Date", actual_col]].copy()

    df_out = df_out.rename(columns={actual_col: "price"})

    # ----------------------------
    # Drop NaNs
    # ----------------------------
    df_out = df_out.dropna(subset=["price"])

    # ----------------------------
    # Sort (safety)
    # ----------------------------
    df_out = df_out.sort_values("Date").reset_index(drop=True)

    return df_out