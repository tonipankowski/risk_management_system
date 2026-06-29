# **Risk Management System**

A portfolio risk analysis tool


## **How it works**

1. You declare your portfolio - tickers and share quantities

2. The system saves your posittions to SQLite database

3. Fetches historical price data from market-data provider - Alpaca API

4. Validates the tickers, drops anything unusable

5. Prints the report on the dashboard


## **Architecture**

### providers.py
data layer with an abstract DataProvider
base class defines single contract - get_prices(tickers, start, end) and returns a DataFrame with columns - [date, ticker, adj_close]
Data Sources (interchangable in main.py):
1. YFinanceProvider - Yahoo Finance
2. AlpacaProvider - Alpaca market-data API
3. CSVProvider - local file reading

### storage.py
saves and loads positions from SQLite database. includes user_id column so it is ready to support multi-users. access isolated in save_positions and load_positons. Database possibly swappable to Postgres

### portfolio.py
converts quantities to portfolio weights using current prices and produces a summary of shares, price, value, weight and total portfolio value

### risk.py
works as a library of risk calculations.
- daily returns
- annualized volatility
- VaR (Value at Risk) (Historical, Parametric and Monte Carlo)
- Correlation matrix
- portfolio returns
- portfolio volatility
- Expected shortfall

### main.py
everything together

## **analysis**
building all three VaR methods the real happenings visible. parametric and monte carlo agree closely, historical separates itself in deep tail (99% VaR).
Diversification benefit is very much visible as well. Volatility of the portfolio is coming out as lower than the weighted average of each individual asset, showing that they can cancel each others movements

## **Setup**
```bash
python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```
For the Alpaca provider create .env file with your paper-trading API keys:

```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret_key
```

## **Usage**
`python src/main.py`

entering tickets -> sharing quantites -> type done to finish

## **Data source**
default provider uses a free market-data suitable for daily-bar risk analysis. A production system would and will use a paid feed for better reliability and market coverage

## **Roadmap**
- User authentication for multi-user support
- crypto data provider
- visual dashboard with charts, plots and VaR comparison