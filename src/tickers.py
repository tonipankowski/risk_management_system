"""Curated ticker lists for the add-holding picker.

Each entry maps a human-readable label to (ticker, asset_type). Commodities are
just ETFs, so they trade through the stock provider like any other equity.
"""

STOCKS = {
    "Apple (AAPL)": ("AAPL", "stock"),
    "Microsoft (MSFT)": ("MSFT", "stock"),
    "Nvidia (NVDA)": ("NVDA", "stock"),
    "Amazon (AMZN)": ("AMZN", "stock"),
    "Alphabet (GOOGL)": ("GOOGL", "stock"),
    "Meta (META)": ("META", "stock"),
    "Tesla (TSLA)": ("TSLA", "stock"),
    "JPMorgan Chase (JPM)": ("JPM", "stock"),
    "Johnson & Johnson (JNJ)": ("JNJ", "stock"),
    "Exxon Mobil (XOM)": ("XOM", "stock"),
}

ETFS = {
    "S&P 500 (SPY)": ("SPY", "stock"),
    "Nasdaq 100 (QQQ)": ("QQQ", "stock"),
    "Total US Market (VTI)": ("VTI", "stock"),
    "Developed ex-US (VEA)": ("VEA", "stock"),
    "Emerging Markets (VWO)": ("VWO", "stock"),
    "US Aggregate Bonds (AGG)": ("AGG", "stock"),
    "20+ Year Treasuries (TLT)": ("TLT", "stock"),
    "Real Estate (VNQ)": ("VNQ", "stock"),
}

COMMODITIES = {
    "Gold (GLD)": ("GLD", "stock"),
    "Silver (SLV)": ("SLV", "stock"),
    "Broad Commodities (DBC)": ("DBC", "stock"),
    "Crude Oil (USO)": ("USO", "stock"),
    "Natural Gas (UNG)": ("UNG", "stock"),
    "Copper Miners (COPX)": ("COPX", "stock"),
    "Agriculture (DBA)": ("DBA", "stock"),
    "Gold Miners (GDX)": ("GDX", "stock"),
    "Platinum (PPLT)": ("PPLT", "stock"),
    "Uranium (URA)": ("URA", "stock"),
}

CRYPTO = {
    "Bitcoin (BTC)": ("BTC/USD", "crypto"),
    "Ethereum (ETH)": ("ETH/USD", "crypto"),
    "Solana (SOL)": ("SOL/USD", "crypto"),
    "Litecoin (LTC)": ("LTC/USD", "crypto"),
    "Chainlink (LINK)": ("LINK/USD", "crypto"),
    "Avalanche (AVAX)": ("AVAX/USD", "crypto"),
    "Dogecoin (DOGE)": ("DOGE/USD", "crypto"),
    "Uniswap (UNI)": ("UNI/USD", "crypto"),
    "Aave (AAVE)": ("AAVE/USD", "crypto"),
    "Bitcoin Cash (BCH)": ("BCH/USD", "crypto"),
}

CATEGORIES = {
    "Stocks": STOCKS,
    "ETFs": ETFS,
    "Commodities": COMMODITIES,
    "Crypto": CRYPTO,
}


# ticker -> full name, derived from the catalog labels ("Bitcoin (BTC)" -> "Bitcoin")
NAMES = {
    ticker: label.rsplit(" (", 1)[0]
    for catalog in CATEGORIES.values()
    for label, (ticker, _) in catalog.items()
}


def display_name(ticker):
    """Full name for a ticker, falling back to the ticker itself."""
    return NAMES.get(ticker, ticker)
