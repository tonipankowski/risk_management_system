import pandas as pd
from datetime import date
from providers import AlpacaProvider, AlpacaCryptoProvider
import risk
import portfolio
import storage
import auth

def get_user_positions():
    positions = {}
    asset_types = {}
    print("Enter your portfolio. Type 'done' when finished.")
    while True:
        ticker = input("Ticker (or 'done'): ").strip().upper()
        if ticker == "DONE":
            break
        if ticker == "":
            continue
        atype = input(f"Is {ticker} a stock or crypto? ").strip().lower()
        if atype == "stock":
            asset_type = "stock"
        elif atype == "crypto":
            asset_type = "crypto"
        else:
            print(" Please answer 'stock' or 'crypto'.")
            continue
        qty = input(f"Number of shares of {ticker}: ").strip()
        try:
            positions[ticker] = float(qty)
            asset_types[ticker] = asset_type 
        except ValueError:
            print(f" '{qty}' isn't a valid number - skipping {ticker}, try again.")
        
    return positions, asset_types

def print_dashboard(summary, total, port, prices, asset_types):
    print()
    print("=" * 50)
    print("  PORTFOLIO RISK REPORT")
    print("=" * 50)
    print(f"  Total value: ${total:,.2f}")
    print()
    print("  Holdings")
    for ticker, row in summary.iterrows():
        shares = row["shares"]
        value = row["value"]
        weight = row["weight"]
        print(f"  {ticker:<6} {shares:>6.0f} sh  ${value:,.2f}  {weight:.1%}")
    print()
    print("=" * 50)
    print("  RISK METRICS")
    print()
    print(f"  Volatility (annualized): {risk.portfolio_volatility(port):.1%}")
    print(f"  95% VaR (historical):    {risk.historical_var(port):.2%}")
    print(f"  95% VaR (parametric):    {risk.parametric_var(port):.2%}")        
    print(f"  95% VaR (Monte Carlo):   {risk.montecarlo_var(port):.2%}")
    print(f"  95% Expected Shortfall:  {risk.expected_shortfall(port):.2%}")
    print()
    print(f"  Sharpe ratio:            {risk.sharpe_ratio(port):.2f}")
    print("=" * 50)
    print("  CORRELATION MATRIX")
    print()
    corr = risk.correlation_matrix(prices, asset_types)
    corr.index.name = None
    corr.columns.name = None
    corr_text = corr.round(2).to_string()
    for line in corr_text.split("\n"):
        print(f"  {line}")
    print("=" * 50)

def do_auth():
    while True:
        choice = input("register or login? ").strip().lower()
        
        if choice == "register":
            username = input("Choose a username: ").strip()
            password = input("Choose a password: ").strip()
            user_id = auth.register(username, password)
            if user_id is None:
                print("That username is taken. Try another.")
                continue
            print(f"Account created. You are logged in.")
            return user_id
        
        elif choice == "login":
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            user_id = auth.login(username, password)
            if user_id is None:
                print("Invalid username or password.")
                continue
            print("Logged in.")
            return user_id
        
        else:
            print("PLease type 'register' or 'login'.")
            
if __name__ == "__main__":
    auth.init_users_db()
    storage.init_db()
    
    user_id = do_auth()
    
    positions,asset_types = storage.load_positions (user_id)
    if len(positions) == 0:
        print("\nNo saved portfolio found. Create one now.")
        pos_dict, asset_types = get_user_positions()
        positions = pd.Series(pos_dict)
        storage.save_positions(positions, asset_types, user_id)
        
    stock_provider = AlpacaProvider()
    crypto_provider = AlpacaCryptoProvider()
        
    while True:
        tickers = list(positions.index)
        
        stock_tickers = [t for t in tickers if asset_types[t] == "stock"]
        crypto_tickers = [t for t in tickers if asset_types[t] == "crypto"]
        
        frames = []
        if stock_tickers:
            frames.append(stock_provider.get_prices(stock_tickers, "2024-01-01", str(date.today())))
        if crypto_tickers:
            frames.append(crypto_provider.get_prices(crypto_tickers, "2024-01-01", str(date.today())))
        prices = pd.concat(frames)
        
        valid = set(prices.dropna(subset=["adj_close"])["ticker"].unique())
        missing = set(tickers) - valid
        if missing:
            print(f"Warning: no data for {missing}.")
            positions = positions.drop(list(missing))
            for t in missing:
                asset_types.pop(t, None)
            storage.save_positions(positions, asset_types, user_id)
            tickers = list(positions.index)
    
        prices = prices[prices["ticker"].isin(tickers)]
        prices = prices.dropna(subset=["adj_close"])
    
        prices_latest = portfolio.latest_price(prices)
        weights = portfolio.compute_weights(positions, prices_latest)
        port = risk.portfolio_returns(prices, weights, asset_types)
        summary, total = portfolio.portfolio_summary(positions, prices_latest)
        
        print_dashboard(summary, total, port, prices, asset_types)
        
        action = input(
            "\nOptions: (add) ticker, (delete) ticker, (change) quantity, (quit): ").strip().lower()
        
        if action == "quit":
            print("See you later!")
            break
        
        elif action == "add":
            ticker = input("Ticker to add: ").strip().upper()
            atype = input(f"Is {ticker} a stock or crypto? ").strip().lower()
            if atype not in ("stock", "crypto"):
                print("Please answer 'stock' or 'crypto'.")
                continue
            qty = input(f"Number of shares of {ticker}: ").strip()
            try:
                qty = float(qty)
            except ValueError:
                print(f"'{qty}' isn't a valid number.")
                continue
            prov = stock_provider if atype == "stock" else crypto_provider
            test = prov.get_prices([ticker], "2024-01-01", str(date.today()))
            if test.dropna(subset=["adj_close"]).empty:
                print(f"'{ticker}' isn't a valid ticker - not added.")
            else:
                positions[ticker] = qty
                asset_types[ticker] = atype
                storage.save_positions(positions, asset_types, user_id)
                
        elif action == "delete":
            ticker = input("Ticker to delete: ").strip().upper()
            if ticker in positions.index:
                positions = positions.drop(ticker)
                asset_types.pop(ticker, None)
                storage.save_positions(positions, asset_types, user_id)
            else:
                print(f"{ticker} not found in the portfolio.")
        
        elif action == "change":
            ticker = input("Ticker to change: ").strip().upper()
            if ticker in positions.index:
                qty = input(f"New number of shares of {ticker}: ").strip()
                try:
                    positions[ticker] = float(qty)
                    storage.save_positions(positions, asset_types, user_id)
                except ValueError:
                    print(f"'{qty}' isn't a valid number.")
            else:
                print(f"{ticker} not found in the portfolio.")
        else:
            print("Please choose add, delete, change or quit.")