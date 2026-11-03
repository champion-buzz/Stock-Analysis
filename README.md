# Stock Price Explorer

A Streamlit app for exploring daily stock price changes, long-term history and short-term forecasts, using Yahoo Finance data.

The forecasts are a learning exercise and aren't financial advice.

## Tech Stack

- Python and Streamlit
- yfinance
- pandas
- Plotly
- Prophet

## Features

- Choose from SPY and eight large companies, including Apple, Tesla and NVIDIA
- See daily price changes as green and red bars, two months at a time
- Browse the full price history and download it as CSV
- Compare open and close prices on today's date over the last 15 years
- See a 7-day Prophet forecast as a weekday candlestick chart

## How It Works

The app downloads daily prices with yfinance and calculates the change from open to close. For the forecast, it trains a separate Prophet model for open, high, low and close, then combines the results into one chart.

## Next Steps

- Cache forecasts so the page reloads faster
- Measure forecast accuracy against past prices
- Add tests

## Run It

```bash
pip install -r requirements.txt
streamlit run stock_app.py
```
