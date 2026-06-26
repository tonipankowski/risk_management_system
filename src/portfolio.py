def compute_weights(positions, prices):
    values = positions * prices
    total = values.sum()
    return values / total

def latest_price(prices):
    sorted_prices = prices.sort_values("date")
    latest = sorted_prices.groupby("ticker")["adj_close"].last()
    return latest
