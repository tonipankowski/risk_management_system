import streamlit as st 
import auth

auth.init_users_db()

st.title("Portfolio Risk Management")

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    
if st.session_state.user_id is None:
    mode = st.radio("Choose:", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button(mode):
        if mode == "Register":
            user_id = auth.register(username, password)
            if user_id is None:
                st.error("That username is taken. Try another.")
            else:
                st.session_state.user_id = user_id
                st.rerun()
        else:
            user_id = auth.login(username, password)
            if user_id is None:
                st.error("Invalid username or password.")
            else:
                st.session_state.user_id = user_id
                st.rerun()
else:
    import pandas as pd
    from datetime import date
    from providers import AlpacaProvider, AlpacaCryptoProvider
    import storage, portfolio, risk
    
    storage.init_db()
    user_id = st.session_state.user_id
    
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("Your Portfolio")
    with col_logout:
        if st.button("Log out"):
            st.session_state.user_id = None
            st.rerun()
            
    positions, asset_types = storage.load_positions(user_id)
    
    if len(positions) == 0:
        st.info("No portfolio saved yet.")
    else:
        tickers = list(positions.index)
        stock_tickers = [t for t in tickers if asset_types[t] == "stock"]
        crypto_tickers = [t for t in tickers if asset_types[t] == "crypto"]
        
        frames = []
        if stock_tickers:
            frames.append(AlpacaProvider().get_prices(stock_tickers, "2024-01-01", str(date.today())))
        if crypto_tickers:
            frames.append(AlpacaCryptoProvider().get_prices(crypto_tickers, "2024-01-01", str(date.today())))
        prices = pd.concat(frames)
        prices = prices.dropna(subset=["adj_close"])
        
        prices_latest = portfolio.latest_price(prices)
        weights = portfolio.compute_weights(positions, prices_latest)
        port = risk.portfolio_returns(prices, weights, asset_types)
        summary, total = portfolio.portfolio_summary(positions, prices_latest)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Value", f"${total:,.0f}")
        c2.metric("Volatility", f"{risk.portfolio_volatility(port):.1%}")
        c3.metric("95% VaR", f"{risk.historical_var(port):.2%}")
        c4.metric("Sharpe", f"{risk.sharpe_ratio(port):.2f}")
        
        st.subheader("Holdings")
        display = summary.copy()
        display["weight"] = (display["weight"] * 100).round(1).astype(str) + "%"
        display["value"] = display["value"].round(2)
        display["price"] = display["price"].round(2)
        st.dataframe(display, use_container_width=True)
        
        st.subheader("Risk Metrics")
        m1, m2 = st.columns(2)
        with m1:
            st.write(f"**Historical VaR (95%):** {risk.historical_var(port):.2%}")
            st.write(f"**Parametric VaR (95%):** {risk.parametric_var(port):.2%}")
            st.write(f"**Monte Carlo VaR (95%):** {risk.montecarlo_var(port):.2%}")
        with m2:
            st.write(f"**Expected Shortfall (95%):** {risk.expected_shortfall(port):.2%}")
            st.write(f"**Sharpe Ratio:** {risk.sharpe_ratio(port):.2f}")
            st.write(f"**Annualized Volatility:** {risk.portfolio_volatility(port):.1%}")