import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# --- Page Setup ---
st.set_page_config(page_title="📈 Stock Viewer + Historical Trend", layout="wide")
st.title("📊 Stock Viewer + 🔁 Same-Date 10-Year Trend")

# --- Stock Dropdown ---
stock_options = {
    "S&P 500 (SPY)": "SPY",
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Tesla (TSLA)": "TSLA",
    "Amazon (AMZN)": "AMZN",
    "Google (GOOGL)": "GOOGL",
    "NVIDIA (NVDA)": "NVDA",
    "Meta (META)": "META",
    "Netflix (NFLX)": "NFLX"
}
selected_stock = st.selectbox("Choose a stock:", list(stock_options.keys()))
ticker = stock_options[selected_stock]

# --- Load 2 Years of Daily Data ---
@st.cache_data
def load_recent_data(ticker):
    df = yf.download(ticker, period="2y", interval="1d")
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    df['Change'] = df['Close'] - df['Open']
    df['Change%'] = (df['Change'] / df['Open']) * 100
    return df

data = load_recent_data(ticker)

# --- MAIN CHART: Last 2 Years ---
st.subheader(f"📊 {ticker} – Open vs Close Price (Last 2 Years)")

fig_main = go.Figure()
fig_main.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name='Open', line=dict(color='blue')))
fig_main.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name='Close', line=dict(color='green')))
fig_main.update_layout(
    xaxis_title='Date',
    yaxis_title='Price ($)',
    height=500,
    xaxis=dict(rangeslider=dict(visible=True))
)
st.plotly_chart(fig_main, use_container_width=True)

# --- Table + Download ---
st.subheader("📋 Data Table (Last 2 Years)")
table = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change', 'Change%']].copy()
table['Change%'] = table['Change%'].map("{:.2f}%".format)
st.dataframe(table, use_container_width=True)

st.download_button(
    label="📥 Download CSV",
    data=table.to_csv(index=False),
    file_name=f"{ticker}_2_years.csv",
    mime="text/csv"
)

# --- SAME DATE HISTORICAL TREND (Last 10 Years) ---
st.divider()
st.header(f"📅 Historical Price on {datetime.date.today():%b %d} (Last 10 Years)")

# Get same or closest date for last 10 years
@st.cache_data
def get_same_day_trend(ticker):
    today = datetime.date.today()
    month = today.month
    day = today.day
    start_year = today.year - 10
    end_year = today.year

    df = yf.download(ticker, start=f"{start_year}-01-01", end=f"{end_year+1}-01-01")
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day

    # Get closest date for each year
    closest_rows = []
    for year in range(start_year, end_year + 1):
        target_date = datetime.date(year, month, day)
        year_data = df[df['Year'] == year]
        if year_data.empty:
            continue
        year_data['Delta'] = (year_data['Date'] - pd.Timestamp(target_date)).abs()
        closest = year_data.loc[year_data['Delta'].idxmin()]
        closest_rows.append(closest)

    result_df = pd.DataFrame(closest_rows)
    result_df = result_df[['Date', 'Open', 'Close', 'High', 'Low', 'Volume']]
    result_df['Year'] = result_df['Date'].dt.year
    result_df = result_df.sort_values('Year')
    return result_df

trend_data = get_same_day_trend(ticker)

if trend_data.empty:
    st.warning("⚠️ No historical data available for this date.")
else:
    # --- Chart: Year-over-Year Trend ---
    st.subheader(f"📈 Open vs Close on {datetime.date.today():%b %d} Over Last 10 Years")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_data['Year'],
        y=trend_data['Open'],
        mode='lines+markers',
        name='Open',
        line=dict(color='blue')
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend_data['Year'],
        y=trend_data['Close'],
        mode='lines+markers',
        name='Close',
        line=dict(color='green')
    ))
    fig_trend.update_layout(
        xaxis_title='Year',
        yaxis_title='Price ($)',
        title=f"{ticker} Price on ~{datetime.date.today():%b %d} (Closest Date Each Year)",
        height=500
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Table ---
    st.subheader("📋 Same-Date Trend Table (10 Years)")
    st.dataframe(trend_data, use_container_width=True)

    st.download_button(
        label="📥 Download Same-Date Trend",
        data=trend_data.to_csv(index=False),
        file_name=f"{ticker}_same_day_10_years.csv",
        mime="text/csv"
    )