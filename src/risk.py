import pandas as pd
from providers import CSVProvider

def compute_return(prices: pd.DataFrame) -> pd.DataFrame:
    """Add a return column daily pct change per ticker"""
    df = prices.sort_values(["ticker", "date"])
    df["return"] = df.groupby("ticker")["adj_close"].pct_change()
    df = df.dropna()
    return df
    
if __name__ == "__main__":
    provider = CSVProvider("data/sample_prices.csv")
    prices = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    returns = compute_return(prices)
    print(returns.head())
    print(returns.shape)