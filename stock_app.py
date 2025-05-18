import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from prophet import Prophet
from scipy.spatial.distance import euclidean

st.set_page_config(page_title="Stock Explorer", layout="wide")
st.title("📈 Stock Price Explorer")

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

@st.cache_data
def load_all_data(ticker):
    df = yf.download(ticker, period="max", interval="1d", progress=False)
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

data = load_all_data(ticker)
data['Change'] = data['Close'] - data['Open']
data['Change%'] = (data['Change'] / data['Open'].squeeze()) * 100
data['Direction'] = data['Change'].apply(lambda x: 'Increase' if x > 0 else 'Decrease')
data['Year'] = data['Date'].dt.year
data['Month'] = data['Date'].dt.month

if "selected_date" not in st.session_state:
    latest_date = data["Date"].max()
    st.session_state.selected_date = latest_date.replace(day=1)

selected_date = st.session_state.selected_date
next_month = selected_date + relativedelta(months=1)
end_date = next_month + relativedelta(months=1)

month_data = data[(data['Date'] >= selected_date) & (data['Date'] < end_date)].copy()

st.subheader(f"📈 Daily Price Change – {ticker} – {selected_date.strftime('%B %Y')} & {next_month.strftime('%B %Y')}")

if month_data.empty:
    st.warning("⚠️ No data available for these months.")
else:
    bar_colors = ['green' if c > 0 else 'red' for c in month_data['Change']]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=month_data['Date'],
        y=month_data['Change'],
        marker_color=bar_colors,
        name='Daily Change'
    ))
    fig.update_layout(
        height=600,
        title=f"{ticker} – Daily Change: {selected_date.strftime('%B %Y')} to {next_month.strftime('%B %Y')}",
        xaxis_title="Date",
        yaxis_title="Change ($)",
        showlegend=False
    )
    config = {'scrollZoom': False, 'displayModeBar': True, 'responsive': True}
    st.plotly_chart(fig, use_container_width=True, config=config)

col1, col2, col3 = st.columns([1, 4, 1])

def prev_month():
    st.session_state.selected_date -= relativedelta(months=1)

def next_month_func():
    st.session_state.selected_date += relativedelta(months=1)

with col1:
    st.button("⬅️ Previous", on_click=prev_month)
with col3:
    st.button("Next ➡️", on_click=next_month_func)

st.subheader("📋 Full Historical Data Table")
preview = data[['Date', 'Open', 'High', 'Low', 'Close', 'Change', 'Change%', 'Direction']].copy()
preview['Change%'] = preview['Change%'].map("{:.2f}%".format)
st.dataframe(preview, use_container_width=True)

csv = data.to_csv(index=False)
st.download_button("📥 Download Full Historical CSV", data=csv, file_name=f"{ticker}_full_history.csv", mime="text/csv")

today = datetime.today()
month = today.month
day = today.day
today_label = today.strftime('%B %d')

st.subheader(f"📋 Historical Open & Close Table for {today_label} Over the Last 15 Years")

table_data = []
for y in range(today.year - 15, today.year):
    try:
        target = datetime(y, month, day)
        window_start = target - timedelta(days=3)
        window_end = target + timedelta(days=3)
        df = yf.download(ticker, start=window_start, end=window_end, interval="1d", progress=False)
        df.reset_index(inplace=True)
        if not df.empty:
            df['DateDiff'] = (df['Date'] - target).abs()
            row = df.sort_values("DateDiff").iloc[0]
            open_price = float(row["Open"])
            close_price = float(row["Close"])
            change = close_price - open_price
            change_pct = (change / open_price) * 100
            table_data.append({
                "Year": y,
                "Date": str(row["Date"])[:10],
                "Open": round(open_price, 2),
                "Close": round(close_price, 2),
                "Change": round(change, 2),
                "Change%": round(change_pct, 2)
            })
    except Exception as e:
        st.warning(f"Skipping {y}: {e}")

table_df = pd.DataFrame(table_data)
if not table_df.empty:
    st.dataframe(table_df, use_container_width=True)
    st.download_button(
        label="📥 Download Historical Table as CSV",
        data=table_df.to_csv(index=False),
        file_name=f"{ticker}_open_close_15years.csv",
        mime="text/csv"
    )
else:
    st.info("No historical data available for this date.")

st.subheader("🔮 AI Forecast: Next 7 Days")

def prepare_prophet_df(df, column):
    df_clean = df[['Date', column]].dropna().copy()
    df_clean.columns = ['ds', 'y']
    df_clean['ds'] = pd.to_datetime(df_clean['ds'])
    df_clean['y'] = pd.to_numeric(df_clean['y'], errors='coerce')
    return df_clean

def forecast_prophet(df, column, days=7):
    try:
        df_train = prepare_prophet_df(df, column)
        if df_train.empty or len(df_train['y']) < 10:
            raise ValueError("Not enough data for Prophet.")
        model = Prophet(daily_seasonality=True)
        model.fit(df_train)
        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)
        return forecast[['ds', 'yhat']].tail(days)
    except Exception as e:
        st.warning(f"⚠️ Error forecasting {column}: {e}")
        return None

ohlc_forecast = {}
for col in ['Open', 'High', 'Low', 'Close']:
    result = forecast_prophet(data, col)
    if result is not None:
        ohlc_forecast[col] = result

if all(k in ohlc_forecast for k in ['Open', 'High', 'Low', 'Close']):
    forecast_df = pd.DataFrame({'Date': ohlc_forecast['Close']['ds']})
    for col in ['Open', 'High', 'Low', 'Close']:
        forecast_df[col] = ohlc_forecast[col]['yhat'].values

    # Remove weekends (Saturday=5, Sunday=6)
    forecast_df = forecast_df[forecast_df['Date'].dt.weekday < 5]

    fig_forecast = go.Figure(data=[go.Candlestick(
        x=forecast_df['Date'],
        open=forecast_df['Open'],
        high=forecast_df['High'],
        low=forecast_df['Low'],
        close=forecast_df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig_forecast.update_layout(
        height=500,
        title=f"{ticker} – Forecasted OHLC (Weekdays Only)",
        xaxis_title="Date",
        yaxis_title="Price"
    )
    st.plotly_chart(fig_forecast, use_container_width=True)
else:
    st.warning("⚠️ Could not generate forecast for all OHLC values.")

