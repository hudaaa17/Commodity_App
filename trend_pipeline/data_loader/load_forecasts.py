import pandas as pd
from data_handling.utils.sheet_utils import get_sheets_service


def load_forecast_sheet(spreadsheet_id, sheet_name="RecursiveForecast"):
    """
    Load full forecast sheet into DataFrame.

    Expected format:
    Date | Zinc | CPO | BrentCrude | ...

    Returns:
        pd.DataFrame with proper types
    """

    service = get_sheets_service()

    try:
        # ----------------------------
        # Fetch data from Google Sheets
        # ----------------------------
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_name
        ).execute()

        values = result.get("values", [])

        if not values or len(values) < 2:
            return pd.DataFrame()

        # ----------------------------
        # Build DataFrame
        # ----------------------------
        df = pd.DataFrame(values[1:], columns=values[0])

        # Clean column names
        df.columns = df.columns.str.strip()

        # ----------------------------
        # Convert Date column
        # ----------------------------
        if "Date" not in df.columns:
            raise ValueError("Missing 'Date' column in forecast sheet")

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        # ----------------------------
        # Convert numeric columns
        # ----------------------------
        for col in df.columns:
            if col == "Date":
                continue

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
            )

            df[col] = pd.to_numeric(df[col], errors="coerce")

        # ----------------------------
        # Drop invalid rows
        # ----------------------------
        df = df.dropna(subset=["Date"])

        # Sort by date
        df = df.sort_values("Date").reset_index(drop=True)

        return df

    except Exception as e:
        print(f"[load_forecast_sheet ERROR] {e}")
        return pd.DataFrame()