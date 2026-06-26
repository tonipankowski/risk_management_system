import pandas as pd
from providers import CSVProvider
import risk
import portfolio
import storage

provider = CSVProvider("data/sample_prices.csv")
prices = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
returns = risk.compute_returns(prices)
vol = risk.compute_volatility(returns)
corr = risk.correlation_matrix(returns)
dd = risk.drawdown(returns)

storage.init_db()
positions = pd.Series({"AAPL": 10, "MSFT": 5, "SPY": 20})
#storage.save_positions(positions)
loaded = storage.load_positions()

print("Loaded from DB:\n", loaded)

prices_latest = portfolio.latest_price(prices)
weights = portfolio.compute_weights(positions, prices_latest)
print("Weights:\n", weights)
print("Weights sum:", weights.sum())

port = risk.portfolio_returns(returns, weights)
port_vol = risk.portfolio_volatility(port)
var_95 = risk.historical_var(port)
var_99 = risk.historical_var(port, confidence=0.99)


print(vol)
print(corr)

print(dd.groupby("ticker")["drawdown"].min())

print("Portfolio volatility:", port_vol)

print("Historical 95% VaR:", var_95)
print("Parametric 95% VaR:", risk.parametric_var(port))
print("Monte Carlo 95% VaR:", risk.montecarlo_var(port))

print("Historical 99% VaR:", var_99)
print("Parametric 99% VaR:", risk.parametric_var(port, confidence=0.99))
print("Monte Carlo 99% VaR:", risk.montecarlo_var(port, confidence=0.99))

print("Expected Shortfall 95%:", risk.expected_shortfall(port))
print("Expected Shortfall 99%:", risk.expected_shortfall(port, confidence=0.99))

summary, total = portfolio.portfolio_summary(positions, prices_latest)
print(summary)
print("Total portfolio value:", total)