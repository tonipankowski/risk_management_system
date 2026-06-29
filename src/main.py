import pandas as pd
from datetime import date
from providers import AlpacaProvider
import risk
import portfolio
import storage
import auth

def get_user_positions():
    positions = {}
    print("Enter your portfolio. Type 'done' when finished.")
    while True:
        ticker = input("Ticker (or 'done'): ").strip().upper()
        if ticker == "DONE":
            break
        if ticker == "":
            continue
        qty = input(f"Number of shares of {ticker}: ").strip()
        try:
            positions[ticker] = float(qty)
        except ValueError:
            print(f" '{qty}' isn't a valid number - skipping {ticker}, try again.")
        
    return positions

def print_dashboard(summary, total, port, returns):
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
    print("=" * 50)
    print("  CORRELATION MATRIX")
    print()
    corr = risk.correlation_matrix(returns)
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
            print("PLease type 'r' or 'l'.")
            
if __name__ == "__main__":
    auth.init_users_db()
    storage.init_db()
    
    user_id = do_auth()
    
    positions = storage.load_positions (user_id)
    if len(positions) == 0:
        print("\nNo saved portfolio found. Create one now.")
        positions = pd.Series(get_user_positions())
        storage.save_positions(positions, user_id)
        
    while True:
        tickers = list(positions.index)
        provider = AlpacaProvider()
        prices = provider.get_prices(tickers, "2024-01-01", str(date.today()))
    
        valid = set(prices.dropna(subset=["adj_close"])["ticker"].unique())
        requested = set(tickers)
        missing = requested - valid
        if missing:
            print(f"Warning: no data for {missing}.")
            positions = positions.drop(list(missing))
            tickers = list(positions.index)
    
        prices = prices[prices["ticker"].isin(tickers)]
        prices = prices.dropna(subset=["adj_close"])
    
        returns = risk.compute_returns(prices)
        prices_latest = portfolio.latest_price(prices)
        weights = portfolio.compute_weights(positions, prices_latest)
        port = risk.portfolio_returns(returns, weights)
        summary, total = portfolio.portfolio_summary(positions, prices_latest)
        
        print_dashboard(summary, total, port, returns)
        
        action = input(
            "\nOptions: (add) ticker, (delete) ticker, (change) quantity, (quit): "
        ).strip().lower()
        
        if action == "quit":
            print("See you later!")
            break
        
        elif action == "add":
            ticker = input("Ticker to add: ").strip().upper()
            qty = input(f"Number of shares of {ticker}: ").strip()
            try:
                qty = float(qty)
            except ValueError:
                print(f"'{qty}' isn't a valid number.")
                continue
            
            test = provider.get_prices([ticker], "2024-01-01", str(date.today()))
            if test.dropna(subset=["adj_close"]).empty:
                print(f"'{ticker}' isn't a valid ticker - not added.")
            else:
                positions[ticker] = qty
                storage.save_positions(positions, user_id)
                
        elif action == "delete":
            ticker = input("Ticker to delete: ").strip().upper()
            if ticker in positions.index:
                positions = positions.drop(ticker)
                storage.save_positions(positions, user_id)
            else:
                print(f"{ticker} not found in the portfolio.")
        
        elif action == "change":
            ticker = input("Ticker to change: ").strip().upper()
            if ticker in positions.index:
                qty = input(f"New number of shares of {ticker}: ").strip()
                try:
                    positions[ticker] = float(qty)
                    storage.save_positions(positions, user_id)
                except ValueError:
                    print(f"'{qty}' isn't a valid number.")
            else:
                print(f"{ticker} not found in the portfolio.")
        else:
            print("Please choose add, delete, change or quit.")