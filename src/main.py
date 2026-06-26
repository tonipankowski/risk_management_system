import pandas as pd
from datetime import date
from providers import YFinanceProvider
import risk
import portfolio
import storage

def get_user_positions():
    positions = {}
    print("Enter your portfolio. Type 'done' when finished.")
    while True:
        ticker = input("Ticker (or 'done'): ").strip().upper()
        if ticker == "DONE":
            break
        if ticker == "":
            continue
        qty = input(f"Number of shares of {ticker}: ").strip()
        try:
            positions[ticker] = float(qty)
        except ValueError:
            print(f" '{qty}' isn't a valid number - skipping {ticker}, try again.")
        
    return positions

if __name__ == "__main__":
    
    storage.init_db()
    positions = pd.Series(get_user_positions())
    storage.save_positions(positions)
    
    tickers = list(positions.index)
    provider = YFinanceProvider()
    prices = provider.get_prices(tickers, "2024-01-01", str(date.today()))
    
    valid = set(prices.dropna(subset=["adj_close"])["ticker"].unique())
    requested = set(tickers)
    missing = requested - valid
    if missing:
        print(f"Warning: no data for {missing}.")
        positions = positions.drop(list(missing))
        tickers = list(positions.index)
    
    prices = prices[prices["ticker"].isin(tickers)]
    prices = prices.dropna(subset=["adj_close"])
    
    returns = risk.compute_returns(prices)
    prices_latest = portfolio.latest_price(prices)
    weights = portfolio.compute_weights(positions, prices_latest)
    port = risk.portfolio_returns(returns, weights)
    
    summary, total = portfolio.portfolio_summary(positions, prices_latest)
    print(summary)
    print("Total portfolio value:", total)
    print("Portfolio volatility:", risk.portfolio_volatility(port))
    print("Historical 95% VaR:", risk.historical_var(port))
    print("Parametric 95% VaR:", risk.parametric_var(port))
    print("Monte Carlo 95% VaR:", risk.montecarlo_var(port))
    print("Expected Shortfall 95%:", risk.expected_shortfall(port))
    