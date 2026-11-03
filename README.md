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

## What I Learned

The biggest lesson from this project is not to jump straight into coding. Building goes better when you follow a process:

1. **Get a clear picture first.** Decide what you're building and how it should work before writing code. For this app, that means knowing where the data comes from, which views the page needs, and what the forecast should show.
2. **Build toward that picture.** With the goal clear, each piece of code has a purpose.
3. **Make small changes along the way.** The plan doesn't have to be perfect. Minor changes here and there are fine, as long as the overall picture stays the same.

The forecast is a good example. The models retrained on every page reload until caching was added. How often they should run is worth deciding early.

## Next Steps

- Measure forecast accuracy against past prices
- Add tests

## Run It

```bash
pip install -r requirements.txt
streamlit run stock_app.py
```
