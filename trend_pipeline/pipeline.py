from trend_pipeline.data_loader.load_forecasts import load_forecast_sheet
from trend_pipeline.processors.prepare_series import get_commodity_series
from trend_pipeline.plots.trend_plots import plot_trend


def run_trend_pipeline(commodity, spreadsheet_id):
    """
    End-to-end trend pipeline for ONE commodity

    Steps:
    1. Load forecast sheet
    2. Extract commodity series
    3. Generate Plotly chart

    Returns:
        Plotly Figure
    """

    # ----------------------------
    # 1. Load forecast data
    # ----------------------------
    df = load_forecast_sheet(spreadsheet_id)

    if df.empty:
        print("❌ Forecast sheet empty")
        return None
    
    # ----------------------------
    # 2. Extract commodity
    # ----------------------------
    df_c = get_commodity_series(df, commodity)

    if df_c.empty:
        print(f"⚠️ Skipping plot for {commodity}")
        return None

    # ----------------------------
    # 3. Plot chart
    # ----------------------------
    fig = plot_trend(df_c, commodity)

    return fig