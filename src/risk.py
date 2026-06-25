import pandas as pd
from providers import CSVProvider
from scipy.stats import norm
import numpy as np

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Add a return column daily pct change per ticker"""
    df = prices.sort_values(["ticker", "date"])
    df["return"] = df.groupby("ticker")["adj_close"].pct_change()
    df = df.dropna()
    return df

def compute_volatility(returns):
    """Annual volatility"""
    return returns.groupby("ticker")["return"].std() * (252 ** 0.5)

def correlation_matrix(returns):
    wide = returns.pivot(index="date", columns="ticker", values="return")
    wide = wide.corr()
    return wide

def drawdown(returns: pd.DataFrame) -> pd.DataFrame:
    df = returns.sort_values(["ticker", "date"])
    df["cum_value"] = df.groupby("ticker")["return"].transform(lambda x: (1 + x).cumprod())
    df["running_peak"] = df.groupby("ticker")["cum_value"].cummax()
    df["drawdown"] = (df["cum_value"] - df["running_peak"]) / df["running_peak"] 
    return df

def portfolio_returns(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Weighted portfolio return series, one value per date"""
    wide = returns.pivot(index="date", columns="ticker", values="return")
    weighted = wide * weights
    return weighted.sum(axis=1)
    
def portfolio_volatility(portfolio_returns):
    return portfolio_returns.std() * (252 ** 0.5)

def historical_var(portfolio_returns, confidence=0.95):
    """Historical VaR"""
    return -portfolio_returns.quantile(1 - confidence)

def parametric_var(portfolio_returns, confidence=0.95):
    """Parametric VaR"""
    mean = portfolio_returns.mean()
    std = portfolio_returns.std()
    z = norm.ppf(1 - confidence)
    return -(mean + z * std)

def montecarlo_var(portfolio_returns, confidence=0.95, n_simulations=10000):
    """Monte Carlo VaR"""
    np.random.seed(42)
    mean = portfolio_returns.mean()
    std = portfolio_returns.std()

    simulated = np.random.normal(mean, std, n_simulations)
    return -np.quantile(simulated, 1 - confidence)
    
def expected_shortfall(portfolio_returns, confidence=0.95):
    """average loss on days worse than the VaR threshold."""
    threshold = portfolio_returns.quantile(1 - confidence)
    tail = portfolio_returns[portfolio_returns <= threshold]
    return -tail.mean()
    
if __name__ == "__main__":
    provider = CSVProvider("data/sample_prices.csv")
    prices = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    returns = compute_returns(prices)
    vol = compute_volatility(returns)
    corr = correlation_matrix(returns)
    dd = drawdown(returns)
    weights = pd.Series({"AAPL": 0.35, "MSFT": 0.15, "SPY": 0.50})
    port = portfolio_returns(returns, weights)
    port_vol = portfolio_volatility(port)
    var_95 = historical_var(port)
    var_99 = historical_var(port, confidence=0.99)
    
    print(returns.head())
    print(returns.shape)
    print(vol)
    print(corr)
    print(dd.head())
    print(dd.groupby("ticker")["drawdown"].min())
    print(port.head())
    print(port.shape)
    print("Portfolio volatility:", port_vol)
    
    print("Historical 95% VaR:", var_95)
    print("Parametric 95% VaR:", parametric_var(port))
    print("Monte Carlo 95% VaR:", montecarlo_var(port))
    
    print("Historical 99% VaR:", var_99)
    print("Parametric 99% VaR:", parametric_var(port, confidence=0.99))
    print("Monte Carlo 99% VaR:", montecarlo_var(port, confidence=0.99))
    
    print("Expected Shortfall 95%:", expected_shortfall(port))
    print("Expected Shortfall 99%:", expected_shortfall(port, confidence=0.99))