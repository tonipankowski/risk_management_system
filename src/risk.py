import pandas as pd
from scipy.stats import norm
import numpy as np

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Add a return column daily pct change per ticker"""
    df = prices.sort_values(["ticker", "date"])
    df["return"] = df.groupby("ticker")["adj_close"].pct_change(fill_method=None)
    df = df.dropna()
    return df

def compute_volatility(returns):
    """Annual volatility"""
    return returns.groupby("ticker")["return"].std() * (252 ** 0.5)

def correlation_matrix(prices, asset_types=None):
    wr = wide_returns(prices, asset_types, fill=False)
    return wr.corr()

def drawdown(returns: pd.DataFrame) -> pd.DataFrame:
    df = returns.sort_values(["ticker", "date"])
    df["cum_value"] = df.groupby("ticker")["return"].transform(lambda x: (1 + x).cumprod())
    df["running_peak"] = df.groupby("ticker")["cum_value"].cummax()
    df["drawdown"] = (df["cum_value"] - df["running_peak"]) / df["running_peak"] 
    return df

def wide_returns(prices, asset_types=None, fill=True):
    wide = prices.pivot(index="date", columns="ticker", values="adj_close")
    has_crypto = asset_types is not None and "crypto" in asset_types.values()
    if has_crypto and fill:
        wide = wide.ffill()
    return wide.pct_change(fill_method=None).dropna()

def portfolio_returns(prices, weights, asset_types=None):
    wr = wide_returns(prices, asset_types, fill=True)
    return (wr * weights).sum(axis=1)

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
    
def sharpe_ratio(portfolio_returns, risk_free=0.04):
    annual_return = portfolio_returns.mean() * 252
    annual_vol = portfolio_returns.std() * (252 ** 0.5)
    return (annual_return - risk_free) / annual_vol