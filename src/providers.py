from abc import ABC, abstractmethod
import pandas as pd
import yfinance as yf

class DataProvider(ABC):
    @abstractmethod
    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        """Return columns [date, ticker, adj_close] one row per ticker per day"""
        ... 
    
class YFinanceProvider(DataProvider):
    def get_prices(self, tickers, start, end):
        raw = yf.download(tickers, start=start, end=end, auto_adjust=True)
        mod = (raw["Close"].reset_index().melt(id_vars="Date", var_name="ticker", value_name="adj_close").rename(columns={"Date": "date"}))
        return mod
               
if __name__ == "__main__":
    provider = YFinanceProvider()
    df = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    print(df.head())
    print(df.shape)