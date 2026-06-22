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

class CSVProvider(DataProvider):
    def __init__(self, path):
        self.path = path
        
    def get_prices(self, tickers, start, end):
        raw = pd.read_csv(self.path, parse_dates=["date"])
        return raw
               
if __name__ == "__main__":
    yf_provider = YFinanceProvider()
    df = yf_provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    df.to_csv("data/sample_prices.csv", index=False)
    print("YFINANCE:")
    print(df.head())
    print(df.shape)
    
    csv_provider = CSVProvider("data/sample_prices.csv")
    df2 = csv_provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    print("\nCSV:")
    print(df2.head())
    print(df2.shape)
