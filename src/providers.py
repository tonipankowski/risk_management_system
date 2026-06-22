from abc import ABC, abstractmethod
import pandas as pd

class DataProvider(ABC):
    @abstractmethod
    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        """Return columns [date, ticker, adj_close] one row per ticker per day"""
        ... 
    