import pandas as pd
from providers import CSVProvider
import risk

provider = CSVProvider("data/sample_prices.csv")
prices = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")

returns = risk.compute_returns(prices)
weights = pd.Series({"AAPL": 0.35, "MSFT": 0.15, "SPY": 0.50})
port = risk.portfolio_returns(returns, weights)

print("Portfolio volatility:", risk.portfolio_volatility(port))
print("Historical 95% VaR:", risk.historical_var(port))
print("Parametric 95% VaR:", risk.parametric_var(port))
print("Monte Carlo 95% VaR:", risk.montecarlo_var(port))
print("Expected Shortfall 95%:", risk.expected_shortfall(port))