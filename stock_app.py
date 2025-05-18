import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta

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
    
from datetime import datetime, timedelta

# =========================
# 📆 Today's Price in Last 15 Years
# =========================
st.subheader("📉 Today's Price Over the Last 15 Years")

today = datetime.today()
month_day = (today.month, today.day)
today_price_data = []

# Go back 15 years
for year in range(today.year - 15, today.year):
    try:
        date_str = f"{year}-{month_day[0]:02d}-{month_day[1]:02d}"
        target_date = pd.to_datetime(date_str)

        # Download 7-day window to ensure we get closest trading day
        past_data = yf.download(ticker, start=target_date - timedelta(days=3), end=target_date + timedelta(days=4), interval='1d')
        past_data.reset_index(inplace=True)

        if not past_data.empty:
            # Find the row closest to target date
            past_data['DateDiff'] = (past_data['Date'] - target_date).abs()
            closest_row = past_data.loc[past_data['DateDiff'].idxmin()]
            today_price_data.append({
                "Year": year,
                "Date": closest_row['Date'].date(),
                "Close": round(closest_row['Close'], 2)
            })
    except Exception as e:
        st.warning(f"Skipping year {year} due to error: {e}")

# Convert to DataFrame
today_df = pd.DataFrame(today_price_data)

if not today_df.empty:
    # 📈 Plot the result
    fig_today = go.Figure()
    fig_today.add_trace(go.Scatter(
        x=today_df['Year'],
        y=today_df['Close'],
        mode='lines+markers',
        line=dict(color='orange'),
        marker=dict(size=8),
        name='Close Price'
    ))

    fig_today.update_layout(
        title=f"{ticker} Closing Price Around {today.strftime('%b %d')} for the Past 15 Years",
        xaxis_title="Year",
        yaxis_title="Closing Price ($)",
        height=500
    )

    st.plotly_chart(fig_today, use_container_width=True)

    # Optional table preview
    st.subheader("📋 Historical Price Table")
    st.dataframe(today_df, use_container_width=True)
else:
    st.info("Not enough data available for this date in the past 15 years.")