import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# --- Page Setup ---
st.set_page_config(page_title="📈 Scrollable Stock Viewer", layout="wide")
st.title("📊 Scrollable Stock Viewer (10 Years)")

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

# --- Load full 10-year data ---
@st.cache_data
def load_10_years(ticker):
    end = datetime.date.today()
    start = end.replace(year=end.year - 10)
    df = yf.download(ticker, start=start, end=end)
    df.reset_index(inplace=True)
    df['Change'] = df['Close'] - df['Open']
    df['Change%'] = (df['Change'] / df['Open']) * 100
    return df

df = load_10_years(ticker)

if df.empty:
    st.warning("⚠️ No data available.")
else:
    # --- Scrollable Chart ---
    st.subheader(f"📈 {ticker} - Open vs Close (Last 10 Years)")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Open'], name='Open', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Close', line=dict(color='green')))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price ($)",
        title=f"{ticker} - Scrollable Open vs Close (10 Years)",
        height=600,
        xaxis=dict(rangeslider=dict(visible=True))  # 👈 Enables scrolling
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Data Table & Download ---
    st.subheader("📋 Data Table")
    table = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change', 'Change%']].copy()
    table['Change%'] = table['Change%'].map("{:.2f}%".format)
    st.dataframe(table, use_container_width=True)

    st.download_button(
        label="📥 Download CSV",
        data=table.to_csv(index=False),
        file_name=f"{ticker}_10_years_scrollable.csv",
        mime="text/csv"
    )