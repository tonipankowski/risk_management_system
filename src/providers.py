from abc import ABC, abstractmethod
import pandas as pd
import yfinance as yf
import os
from dotenv import load_dotenv

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment

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
    
class AlpacaProvider(DataProvider):
    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("ALPACA_API_KEY")
        secret_key = os.environ.get("ALPACA_SECRET_KEY")
        self.client = StockHistoricalDataClient(api_key, secret_key)
        
    def get_prices(self, tickers, start, end):
        request = StockBarsRequest(symbol_or_symbols=tickers, timeframe=TimeFrame.Day, start=start, end=end, adjustment=Adjustment.ALL,)
        bars = self.client.get_stock_bars(request)
        raw = bars.df
        mod = (raw.reset_index()[["timestamp", "symbol", "close"]].rename(columns={"timestamp": "date", "symbol": "ticker", "close": "adj_close"}))
        mod["date"] = mod["date"].dt.tz_localize(None).dt.normalize()
        return mod

class AlpacaCryptoProvider(DataProvider):
    def __init__(self):
        self.client = CryptoHistoricalDataClient()

    def get_prices(self, tickers, start, end):
        request = CryptoBarsRequest(
            symbol_or_symbols=tickers, 
            timeframe=TimeFrame.Day, 
            start=start, 
            end=end,
        )
        bars = self.client.get_crypto_bars(request)
        raw = bars.df
        mod = (raw.reset_index()[["timestamp", "symbol", "close"]].rename(columns={"timestamp": "date", "symbol": "ticker", "close": "adj_close"}))
        mod["date"] = mod["date"].dt.tz_localize(None).dt.normalize()
        return mod
    
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
    
    provider = AlpacaProvider()
    df = provider.get_prices(["AAPL", "MSFT", "SPY"], "2024-01-01", "2025-01-01")
    print("\nAlpaca:")
    print(df.head())
    print(df.shape)

    p = AlpacaCryptoProvider()
    df = p.get_prices(["BTC/USD", "ETH/USD"], "2024-01-01", "2025-01-01")
    print(df.head())
    print(df.shape)