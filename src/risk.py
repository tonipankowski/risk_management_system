import pandas as pd
from providers import CSVProvider

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
if __name__ == "__main__":
    provider = CSVProvider("data/sample_prices.csv")
    prices = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    returns = compute_returns(prices)
    vol = compute_volatility(returns)
    corr = correlation_matrix(returns)
    
    print(returns.head())
    print(returns.shape)
    print(vol)
    print(corr)