import pandas as pd
from datetime import date
from providers import AlpacaProvider
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

def print_dashboard(summary, total, port):
    print("=" * 50)
    print("  PORTFOLIO RISK REPORT")
    print("=" * 50)
    print(f"  Total value: ${total:,.2f}")
    print()
    print("  Holdings")
    for ticker, row in summary.iterrows():
        shares = row["shares"]
        value = row["value"]
        weight = row["weight"]
        print(f"  {ticker:<6} {shares:>6.0f} sh  ${value:,.2f}  {weight:.1%}")
    print()
    print("  RISK METRICS")
    print(f"  Volatility (annualized): {risk.portfolio_volatility(port):.1%}")
    print(f"  95% VaR (historical):    {risk.historical_var(port):.2%}")
    print(f"  95% VaR (parametric):    {risk.parametric_var(port):.2%}")        
    print(f"  95% VaR (Monte Carlo):   {risk.montecarlo_var(port):.2%}")
    print(f"  95% Expected Shortfall:  {risk.expected_shortfall(port):.2%}")
    print("=" * 50)
        
if __name__ == "__main__":
    
    storage.init_db()
    positions = pd.Series(get_user_positions())
    storage.save_positions(positions)
    
    tickers = list(positions.index)
    provider = AlpacaProvider()
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
    print_dashboard(summary, total, port)