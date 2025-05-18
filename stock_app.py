import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import io

# Streamlit config
st.set_page_config(page_title="Stock Bar Chart Viewer", layout="wide")
st.title("📊 Stock Daily Change Bar Chart (Close - Open)")

# Stock selection
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

# Load 2 years of data
@st.cache_data
def load_data(ticker):
    df = yf.download(ticker, period="2y", interval="1d")
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

data = load_data(ticker)
data = data.sort_values("Date")

# Add time columns
data['Year'] = data['Date'].dt.year
data['Month'] = data['Date'].dt.month
data['MonthName'] = data['Date'].dt.month_name()

# Calculate change and direction
data['Change'] = data['Close'] - data['Open']
data['Change%'] = (data['Change'] / data['Open'].squeeze()) * 100
data['Direction'] = data['Change'].apply(lambda x: 'Increase' if x > 0 else 'Decrease')

# 📅 Year and month selection
st.subheader("📅 Select Time Period")
year = st.selectbox("Year", sorted(data['Year'].unique(), reverse=True))
month_options = data[data['Year'] == year]['Month'].unique()
month_names = [pd.to_datetime(str(m), format='%m').strftime('%B') for m in month_options]
month_map = dict(zip(month_names, month_options))
month_name = st.selectbox("Month", month_names)
month = month_map[month_name]

# Filter for selected period
filtered = data[(data['Year'] == year) & (data['Month'] == month)].copy()
filtered = filtered.sort_values("Date")

# ✅ Chart Section
if filtered.empty or len(filtered) < 2:
    st.warning("⚠️ No data available for this period.")
else:
    st.subheader(f"📈 {ticker} Daily Price Change – {month_name} {year}")

    bar_colors = ['green' if change > 0 else 'red' for change in filtered['Change']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=filtered['Date'],
        y=filtered['Change'],
        marker_color=bar_colors,
        name='Daily Change (Close - Open)'
    ))

    fig.update_layout(
        title=f"{ticker} - Daily Price Change (Close - Open) for {month_name} {year}",
        xaxis_title="Date",
        yaxis_title="Change ($)",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # 📋 Table preview
    st.subheader("📋 Data Table Preview")
    preview = filtered[['Date', 'Open', 'High', 'Low', 'Close', 'Change', 'Change%', 'Direction']].copy()
    preview['Change%'] = preview['Change%'].map("{:.2f}%".format)
    st.dataframe(preview, use_container_width=True)

    # 📥 Download button
    st.subheader("📥 Download This Data")
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{ticker}_{month_name}_{year}_change_chart.csv",
        mime="text/csv"
    )