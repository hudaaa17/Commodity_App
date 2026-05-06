import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from trend_pipeline.pipeline import run_trend_pipeline

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

import re

def clean_date(val):
    if not val or val in ("None", "nan", "NaT"):
        return None
    val = str(val).strip()
    
    # Remove anything in brackets like "(MPOB)", "(2-Day Lag)"
    val = re.sub(r'\(.*?\)', '', val).strip()
    
    # Take only first 10 chars to strip time portion
    # Handles: "2026-05-05 06:02:14" → "2026-05-05"
    if re.match(r'^\d{4}-\d{2}-\d{2}', val):
        return val[:10]
    
    # Handles: "27-02-2026 10:43" or "27-02-2026"
    if re.match(r'^\d{2}-\d{2}-\d{4}', val):
        parts = val[:10].split("-")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    
    # Handles: "2026-04" year-month only
    if re.match(r'^\d{4}-\d{2}$', val):
        return val + "-01"
    
    return None

def fmt_date(ts, original):
    if pd.isna(ts):
        return "N/A"
    # If original was year-month only, show as "Apr 2026"
    if re.match(r'^\d{4}-\d{2}$', str(original).strip()):
        return ts.strftime("%b %Y")
    return ts.strftime("%d %b %Y")



st.set_page_config(
    page_title="Commodity Dashboard",
    page_icon="📈",
    layout="wide"
)

# ─────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:         #0D0F14;
    --surface:    #13161D;
    --surface2:   #1A1E28;
    --border:     #252A38;
    --accent:     #C9A84C;
    --accent2:    #E8C96A;
    --text:       #E8E4DA;
    --muted:      #6B7280;
    --green:      #4ADE80;
    --red:        #F87171;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

[data-testid="stAppViewContainer"] > .main {
    background-color: var(--bg) !important;
}

[data-testid="stHeader"] {
    background-color: var(--bg) !important;
    border-bottom: 1px solid var(--border);
}

/* Hide Streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Hero Header ── */
.hero {
    text-align: center;
    padding: 3rem 0 2rem 0;
    position: relative;
}
.hero-eyebrow {
    font-size: 1.2rem;
    font-weight: 600;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.75rem;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 4.2rem;
    color: var(--text);
    line-height: 1.1;
    margin-bottom: 0.5rem;
}
.hero-title em {
    color: var(--accent);
    font-style: italic;
}
.hero-sub {
    font-size: 1.5rem;
    color: var(--text);
    font-weight: 300;
}
.hero-line {
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    margin: 1.5rem auto 0;
}

/* ── Section Title ── */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: var(--text);
    margin: 2.5rem 0 0.3rem 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── Commodity Card ── */
.commodity-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
    height: 100%;
}
.commodity-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.commodity-card:hover {
    border-color: var(--accent);
}
.card-commodity {
    font-size: 0.80rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.4rem;
}
.card-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: var(--text);
    margin-bottom: 1rem;
    line-height: 1.3;
}
.card-prices {
    display: flex;
    gap: 1.2rem;
    margin-bottom: 1.2rem;
    flex-wrap: wrap;
}
.price-block {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    flex: 1;
    min-width: 80px;
}
.price-label {
    font-size: 0.80rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 2px;
}
.price-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text);
    font-variant-numeric: tabular-nums;
}
.price-value.usd { color: var(--accent2); }
.price-value.inr { color: var(--green); }
.card-meta {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.meta-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem;
}
.meta-key { color: var(--muted); }
.meta-val { color: var(--text); font-weight: 500; }
.card-unit-badge {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.80rem;
    color: var(--muted);
    margin-bottom: 0.8rem;
}
.source-link {
    color: var(--accent);
    text-decoration: none;
    font-size: 0.78rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 200px;
    display: inline-block;
}
.source-link:hover {
    color: var(--accent2);
    text-decoration: underline;
}

/* ── Derived Badge ── */
.derived-badge {
    display: inline-block;
    background: rgba(201, 168, 76, 0.12);
    border: 1px solid rgba(201, 168, 76, 0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.65rem;
    color: var(--accent);
    letter-spacing: 0.05em;
    margin-left: 8px;
}

/* ── No Forecast Card ── */
.no-forecast-card {
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}
.no-forecast-icon { font-size: 2rem; }
.no-forecast-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
}
.no-forecast-sub {
    font-size: 0.75rem;
    color: var(--muted);
}

/* ── Error / NA Card ── */
.na-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
}

/* ── Last Refresh ── */
.refresh-bar {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    color: var(--muted);
    margin-bottom: 1rem;
}
.refresh-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--green);
    display: inline-block;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Plotly chart background fix */
.js-plotly-plot .plotly, .js-plotly-plot .plotly .svg-container {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

COMMODITY_DISPLAY = {
    "Zinc Metal":                   {"key": "Zinc Metal",           "derived": False},
    "Zinc Dross":                   {"key": "Zinc Dross",           "derived": True},
    "Zinc Oxide":                   {"key": "Zinc Oxide",           "derived": True},
    "Natural Rubber (India - RSS4)":{"key": "Natural Rubber (India - RSS4)", "derived": False},
    "Crude Palm Oil":               {"key": "Crude Palm Oil",       "derived": False},
    "Crude Oil Indian Basket":      {"key": "Crude Oil (Indian Basket)", "derived": False},
    "Brent Crude":                  {"key": "Brent Crude",          "derived": False},
}

# Mapping from display name → RecursiveForecast column name
FORECAST_COL_MAP = {
    "Zinc Metal":                    "Zinc Metal",
    "Zinc Dross":                    "Zinc Dross",
    "Zinc Oxide":                    "Zinc Oxide",
    "Natural Rubber (India - RSS4)": "Natural Rubber (RSS4)",
    "Crude Palm Oil":                "Crude Palm Oil",
    "Crude Oil Indian Basket":       "Crude Oil Indian Basket",  # 
    "Brent Crude":                   "Brent Crude",
}


@st.cache_data(ttl=3600, show_spinner=False)
def load_raw_data():
    """Load latest price for each commodity from raw spreadsheet Sheet1."""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["GCP_SERVICE_ACCOUNT"], scopes=SCOPE
        )
        client = gspread.authorize(creds)
        sheet_id = st.secrets["spreadsheets"]["raw"]
        ws = client.open_by_key(sheet_id).worksheet("Sheet1")
        records = ws.get_all_records()
        if not records:
            return {}

        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip().str.lower()

        # Parse date
        df["last_updated"] = df["last_updated"].replace(
                        ["Not Available", "N/A", "NA", "none", ""], None)
        
        df["last_updated_raw"] = df["last_updated"].astype(str)  # ← before cleaning
        df["last_updated_clean"] = df["last_updated_raw"].apply(clean_date)
        df["last_updated_dt"] = pd.to_datetime(df["last_updated_clean"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        latest = (
            df.sort_values("date", ascending=False, na_position="last")
            .groupby("commodity", as_index=False)
            .first()
        )

        result = {}
        for _, row in latest.iterrows():
            result[row["commodity"]] = {
                "commodity":    row["commodity"],
                "price_usd":    row.get("price_usd", "N/A"),
                "price_inr":    row.get("price_inr", "N/A"),
                "unit":         row.get("unit", ""),
                "last_updated": fmt_date(row["last_updated_dt"], row["last_updated_raw"]),
                "source":       row.get("source", "—"),
            }
        return result
    except Exception as e:
        st.error(f"Failed to load raw data: {e}")
        return {}


def get_forecast_fig(display_name, training_sheet_id):
    col = FORECAST_COL_MAP.get(display_name)
    if col is None:          # ← this only triggers if value IS None
        return None          #    
    try:
        fig = run_trend_pipeline(col, training_sheet_id)
        return fig
    except Exception:
        return None          # ← if data isn't in sheet yet, returns None gracefully


# ─────────────────────────────────────────
# CARD RENDERERS
# ─────────────────────────────────────────
def render_commodity_card(display_name, data, is_derived):
    derived_html = '<span class="derived-badge">⚗ Derived</span>' if is_derived else ""
    usd = data.get("price_usd", "N/A")
    inr = data.get("price_inr", "N/A")
    source = data.get("source", "—")

    # Format prices
    def fmt(v):
        try:
            return f"{float(str(v).replace(',', '')):,.2f}"
        except:
            return str(v)
        
    if source.startswith("http"):
        source_html = f'<a href="{source}" target="_blank" class="source-link">{source}</a>'
    else:
        source_html = f'<span class="meta-val">{source}</span>'

    st.markdown(f"""
    <div class="commodity-card">
        <div class="card-commodity">Live Price {derived_html}</div>
        <div class="card-name">{display_name}</div>
        <div class="card-unit-badge">{data.get('unit', '—')}</div>
        <div class="card-prices">
            <div class="price-block">
                <div class="price-label">USD</div>
                <div class="price-value usd">$ {fmt(usd)}</div>
            </div>
            <div class="price-block">
                <div class="price-label">INR</div>
                <div class="price-value inr">₹ {fmt(inr)}</div>
            </div>
        </div>
        <div class="card-meta">
            <div class="meta-row">
                <span class="meta-key">Updated</span>
                <span class="meta-val">{data.get('last_updated', '—')}</span>
            </div>
            <div class="meta-row" style="align-items: flex-start; gap: 8px;">
                <span class="meta-key" style="white-space: nowrap;">Source</span>
                {source_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_na_card(display_name):
    st.markdown(f"""
    <div class="na-card">
        <div style="font-size:1.5rem; margin-bottom:0.5rem;">⚠️</div>
        <div style="font-weight:600; color:#E8E4DA; margin-bottom:0.3rem;">{display_name}</div>
        <div>Data unavailable</div>
    </div>
    """, unsafe_allow_html=True)


def render_no_forecast_card(display_name):
    st.markdown(f"""
    <div class="no-forecast-card">
        <div class="no-forecast-icon">🔭</div>
        <div class="no-forecast-title">Forecast Unavailable</div>
        <div class="no-forecast-sub">Insufficient historical data<br>for {display_name}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────
def main():

    RAW_ID      = st.secrets["spreadsheets"]["raw"] # do not remove it from here it is referenced inside a function.
    TRAINING_ID = st.secrets["spreadsheets"]["training"]

    # ── Hero ──
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">Live Market Intelligence</div>
        <div class="hero-title">Commodity <em>Dashboard</em></div>
        <div class="hero-sub">Real-time prices · 30-day recursive forecasts ·</div>
        <div class="hero-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load data ──
    with st.spinner("Loading market data..."):
        raw_data = load_raw_data()



    # ── Render each commodity ──

    for display_name, meta in COMMODITY_DISPLAY.items():
        commodity_key = meta["key"]
        is_derived    = meta["derived"]
        data          = raw_data.get(commodity_key)

        st.markdown(f"""
        <div class="section-title">
            {display_name}
        </div>
        """, unsafe_allow_html=True)

        col_card, col_chart = st.columns([1, 2.5], gap="large")

        with col_card:
            if data:
                render_commodity_card(display_name, data, is_derived)
            else:
                render_na_card(display_name)

        with col_chart:
            with st.spinner(f"Loading forecast..."):
                fig = get_forecast_fig(display_name, TRAINING_ID)

            if fig is not None:
                # Style the plotly chart to match dark theme
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(19,22,29,1)",
                    font=dict(family="DM Sans", color="#ECF0F6", size=11),
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(
                        gridcolor="#252A38",
                        linecolor="#252A38",
                        tickcolor="#252A38",
                    ),
                    yaxis=dict(
                        gridcolor="#252A38",
                        linecolor="#252A38",
                        tickcolor="#252A38",
                    ),
                    legend=dict(
                        bgcolor="rgba(0,0,0,0)",
                        bordercolor="#252A38",
                    ),
                    height=260,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                render_no_forecast_card(display_name)

        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()