import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_chat import message
from openai import OpenAI
import io

# App configuration
st.set_page_config(page_title="Stock Visualizer + Chatbot", layout="wide")
st.title("📊 Stock Visualizer + 💬 Chatbot Assistant")

# Secure OpenAI key from secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Stock selector
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

# Load 2 years of daily data
@st.cache_data
def load_data(ticker):
    df = yf.download(ticker, period="2y", interval="1d")
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

data = load_data(ticker)
data = data.sort_values("Date")
data['Year'] = data['Date'].dt.year
data['Month'] = data['Date'].dt.month
data['MonthName'] = data['Date'].dt.month_name()
data['Change'] = data['Close'] - data['Open']
data['Change%'] = (data['Change'] / data['Open'].squeeze()) * 100
data['Direction'] = data['Change'].apply(lambda x: 'Increase' if x > 0 else 'Decrease')

# Time filter
st.subheader("📅 Select Time Period")
year = st.selectbox("Year", sorted(data['Year'].unique(), reverse=True))
month_options = data[data['Year'] == year]['Month'].unique()
month_names = [pd.to_datetime(str(m), format='%m').strftime('%B') for m in month_options]
month_map = dict(zip(month_names, month_options))
month_name = st.selectbox("Month", month_names)
month = month_map[month_name]

# Filter data
filtered = data[(data['Year'] == year) & (data['Month'] == month)].copy()
filtered = filtered.sort_values("Date")

# Chart
if filtered.empty or len(filtered) < 2:
    st.warning("⚠️ No data for this period.")
else:
    st.subheader(f"📈 Daily Price Change: {ticker} - {month_name} {year}")
    bar_colors = ['green' if c > 0 else 'red' for c in filtered['Change']]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=filtered['Date'],
        y=filtered['Change'],
        marker_color=bar_colors,
        name='Close - Open'
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Daily Change ($)",
        title=f"{ticker} Daily Gains/Losses",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.subheader("📋 Data Table")
    preview = filtered[['Date', 'Open', 'High', 'Low', 'Close', 'Change', 'Change%', 'Direction']].copy()
    preview['Change%'] = preview['Change%'].map("{:.2f}%".format)
    st.dataframe(preview, use_container_width=True)

    # Download
    st.subheader("📥 Download This Data")
    csv = filtered.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name=f"{ticker}_{month_name}_{year}.csv", mime="text/csv")

# Chatbot
st.divider()
st.header("💬 Ask a Question About This Stock")

# Load recent data for context
stock_obj = yf.Ticker(ticker)
stock_hist = stock_obj.history(period="1mo")
stock_info = stock_obj.info

# Chat history
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# User input
user_question = st.chat_input("Ask about recent performance, market cap, trend...")

if user_question:
    st.session_state.chat_messages.append({"role": "user", "content": user_question})

    # Context for OpenAI
    context = f"You are a helpful stock assistant. The user is asking about {ticker}.\n"
    context += f"Recent stock prices:\n{stock_hist.tail(3)}\n"
    context += f"Company info:\nName: {stock_info.get('longName', ticker)}, Sector: {stock_info.get('sector', 'N/A')}\n"

    messages = [{"role": "system", "content": context}] + st.session_state.chat_messages

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        bot_reply = response.choices[0].message.content
        st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
    except Exception as e:
        st.error(f"❌ OpenAI Error: {e}")

# Display chat
for msg in st.session_state.chat_messages:
    message(msg["content"], is_user=(msg["role"] == "user"))