import pandas as pd

def compute_weights(positions, prices):
    values = positions * prices
    total = values.sum()
    return values / total

def latest_price(prices):
    sorted_prices = prices.sort_values("date")
    latest = sorted_prices.groupby("ticker")["adj_close"].last()
    return latest

def portfolio_summary(positions, prices):
    values = positions * prices
    total = values.sum()
    weights = values / total
    summary = pd.DataFrame({
        "shares": positions,
        "price": prices,
        "value": values,
        "weight": weights,
    })
    return summary, total
    