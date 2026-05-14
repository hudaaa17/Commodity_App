import plotly.graph_objects as go

import requests

COMMODITY_TITLE_MAP = {
    "Zinc":       "Zinc Metal",
    "Zincdross":  "Zinc Oxide", # ---> Changed for time being
    #"Zincoxide":  "Zinc Oxide",
    "Rubber":     "Natural Rubber (RSS4)",
    "Cpo":        "Crude Palm Oil",
    "Brentcrude": "Brent Crude",
    "Silicon": "Silicon",
    "Polyurethane": "Polyurethane"
}

def get_usd_to_inr() -> float:
    """Fetch live USD to INR rate, fallback to 84.0 if API fails."""
    try:
        r = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=5
        )
        data = r.json()
        return float(data["rates"]["INR"])
    except Exception:
        return 84.0  # fallback rate


def plot_trend(df, commodity, display_name=None):
    """
    Professional interactive trend chart

    Input:
        df → DataFrame with Date, price
        commodity → string

    Returns:
        Plotly figure
    """

    if df.empty:
         print(f"⚠️ No data to plot for {commodity}")

    df = df.copy()
    fx_rate = get_usd_to_inr()
    df["price"] = df["price"] * fx_rate

    # ----------------------------
    # Add day index (1 → 30)
    # ----------------------------
    df["day"] = range(1, len(df) + 1)

    # ----------------------------
    # Create figure
    # ----------------------------
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["day"],
            y=df["price"],
            mode="lines+markers",
            name=commodity,
            line=dict(width=3),
            marker=dict(size=5),
            customdata=df["day"],
            showlegend=False,
            hovertemplate="Day %{customdata}<br>₹ %{y:,.2f}<extra></extra>"
        )
    )

    # ----------------------------
    # Highlight FINAL DAY (Day 30)
    # ----------------------------
    final_day = df.iloc[-1]

    fig.add_trace(
    go.Scatter(
        x=[final_day["day"]],
        y=[final_day["price"]],
        mode="markers+text",
        marker=dict(size=10),
        text=[f"₹ {final_day['price']:,.2f}"],
        textposition="top center",
        showlegend=False,
        customdata=[final_day["day"]],
        hovertemplate="Day %{customdata}<br>₹ %{y:,.2f}<extra></extra>"
    )
)

    # ----------------------------
    # Week markers (vertical lines)
    # ----------------------------
    week_marks = [7, 14, 21, 30]

    for w in week_marks:
        fig.add_vline(
            x=w,
            line_width=1,
            line_dash="dot"
        )
    title_name = display_name if display_name else commodity
    # ----------------------------
    # Layout (professional look)
    # ----------------------------
    fig.update_layout(
        title=dict(
        text=f"{title_name} — 30 Day Price Forecast",
        font=dict(
            color="rgba(255, 255, 255, 0.95)",
            size=14,
            family="DM Sans"
        )
    ),

        #xaxis_title="Forecast Horizon",
        yaxis_title="Price",

        template="plotly_white",

        hovermode="x unified",

        xaxis=dict(
            tickmode="array",
            tickvals=[1, 7, 14, 21, 30],
            ticktext=["Day 1", "Week 1", "Week 2", "Week 3", "Day 30"]
        ),

        margin=dict(l=40, r=20, t=50, b=40),

        height=400
    )

    fig.add_annotation(
        text=f"1 USD = ₹ {fx_rate:.2f}",
        xref="paper", yref="paper",
        x=1, y=1.08,
        showarrow=False,
        font=dict(size=10, color="#EEF0F3"),
        xanchor="right"
    )

    return fig
