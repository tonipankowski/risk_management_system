import streamlit as st 
import auth

auth.init_users_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    
if st.session_state.user_id is None:
    st.title("Portfolio Risk Management")
    mode = st.radio("Choose:", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if mode == "Register":
        password_confirm = st.text_input("Confirm Password", type="password")
    if st.button(mode):
        if mode == "Register":
            if password != password_confirm:
                st.error("Passwords do not match.")
            elif len(password) == 0:
                st.error("Password cannot be empty.")
            else:
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
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import date
    from providers import AlpacaProvider, AlpacaCryptoProvider
    import storage, portfolio, risk
    
    storage.init_db()
    user_id = st.session_state.user_id
    
    st.markdown("<h1 style='text-align: center;'>Your Portfolio</h1>", unsafe_allow_html=True)
       
    positions, asset_types = storage.load_positions(user_id)
    
    # SIDEBAR:
    st.sidebar.header("Manage Portfolio")

    # ADD
    with st.sidebar.expander("Add holding"):
        new_ticker = st.text_input("Ticker", key="add_ticker").strip().upper()
        new_type = st.radio("Type", ["stock", "crypto"], key="add_type")
        new_qty = st.text_input("Quantity", key="add_qty")
        if st.button("Add", key="add_btn"):
            try:
                qty = float(new_qty)
                # validate against the right provider
                prov = AlpacaProvider() if new_type == "stock" else AlpacaCryptoProvider()
                test = prov.get_prices([new_ticker], "2024-01-01", str(date.today()))
                if test.dropna(subset=["adj_close"]).empty:
                    st.sidebar.error(f"'{new_ticker}' returned no data.")
                else:
                    positions[new_ticker] = qty
                    asset_types[new_ticker] = new_type
                    storage.save_positions(positions, asset_types, user_id)
                    st.rerun()
            except ValueError:
                st.sidebar.error("Quantity must be a number.")

    # DELETE
    if len(positions) > 0:
        with st.sidebar.expander("Delete holding"):
            del_ticker = st.selectbox("Ticker to remove", list(positions.index), key="del_ticker")
            if st.button("Delete", key="del_btn"):
                positions = positions.drop(del_ticker)
                asset_types.pop(del_ticker, None)
                storage.save_positions(positions, asset_types, user_id)
                st.rerun()

    # CHANGE QUANTITY
    if len(positions) > 0:
        with st.sidebar.expander("Change quantity"):
            chg_ticker = st.selectbox("Ticker", list(positions.index), key="chg_ticker")
            chg_qty = st.text_input("New quantity", key="chg_qty")
            if st.button("Update", key="chg_btn"):
                try:
                    positions[chg_ticker] = float(chg_qty)
                    storage.save_positions(positions, asset_types, user_id)
                    st.rerun()
                except ValueError:
                    st.sidebar.error("Quantity must be a number.")
                    
    st.sidebar.divider()
    
    with st.sidebar.expander("Change password"):
        old_pw = st.text_input("Current password", type="password", key="old_pw")
        new_pw = st.text_input("New password", type="password", key="new_pw")
        new_pw2 = st.text_input("Confirm new password", type="password", key="new_pw2")
        if st.button("Update password", key="pw_btn"):
            if new_pw != new_pw2:
                st.sidebar.error("New passwords do not match.")
            elif len(new_pw) == 0:
                st.sidebar.error("New passwords cannot be empty.")
            else:
                success = auth.change_password(user_id, old_pw, new_pw)
                if success:
                    st.sidebar.success("Password updated successfully.")
                else:
                    st.sidebar.error("Current password is incorrect.")
                    
    with st.sidebar.expander("Settings"):
        risk_free = st.number_input(
            "Risk-free rate (%)", 
            min_value=0.0, 
            max_value=20.0, 
            value=4.0, 
            step=0.5, 
            key="risk_free"
        ) / 100 
        
    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()
    
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
        c4.metric("Sharpe", f"{risk.sharpe_ratio(port, risk_free):.2f}")
        
        st.subheader("Holdings")
        col_table, col_donut = st.columns([3, 2])
        with col_table:
            display = summary.copy()
            display["weight"] = (display["weight"] * 100).round(1).astype(str) + "%"
            display["value"] = display["value"].round(2)
            display["price"] = display["price"].round(2)
            st.dataframe(display, use_container_width=True)
        with col_donut:
            fig_donut = px.pie(
                values=summary["value"],
                names=summary.index,
                hole=0.55,
                color_discrete_sequence=["#00D09C", "#4A90D9", "#FF6B6B", "#F5A623", "#9B59B6"]
            )
            fig_donut.update_traces(
                textposition="inside",
                textinfo="percent",
            )
            fig_donut.update_layout(
                height=380, 
                margin=dict(t=10, b=10, l=10, r=10), 
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.05,
                    xanchor="center",
                    x=0.5
                ),
                showlegend=True,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Correlation", "VaR Comparison", "Drawdown", "Portfolio Value Over Time", "Return Distribution"])
        
        with tab1:
            corr = risk.correlation_matrix(prices, asset_types)
            fig = px.imshow(corr, text_auto=".2f", 
                            color_continuous_scale="RdBu_r",
                            zmin=-1, zmax=1, 
                            aspect="auto")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            methods = ["Historical", "Parametric", "Monte Carlo"]
            var_95 = [
                risk.historical_var(port) * 100,
                risk.parametric_var(port) * 100,
                risk.montecarlo_var(port) * 100,
            ]
            var_99 = [
                risk.historical_var(port, 0.99) * 100,
                risk.parametric_var(port, 0.99) * 100,
                risk.montecarlo_var(port, 0.99) * 100,
            ]
            fig_var = go.Figure()
            fig_var.add_trace(go.Bar(name="95%", x=methods, y=var_95, marker_color="#00D09C"))
            fig_var.add_trace(go.Bar(name="99%", x=methods, y=var_99, marker_color="#FF4B4B"))
            fig_var.update_layout(
                barmode="group",
                yaxis_title="Daily VaR (%)",
                height=400     
            )
            st.plotly_chart(fig_var, use_container_width=True)
            
        with tab3:
            cum_value = (1 + port).cumprod()
            running_peak = cum_value.cummax()
            dd_series = (cum_value - running_peak) / running_peak

            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=dd_series.index,
                y=dd_series * 100,
                fill="tozeroy",                 # fill the area down to zero = underwater look
                line=dict(color="#FF4B4B"),
                name="Drawdown",
            ))
            fig_dd.update_layout(
                yaxis_title="Drawdown (%)",
                height=400,
            )
            st.plotly_chart(fig_dd, use_container_width=True)    
        
        with tab4:
            cum_value = (1 + port).cumprod()
            equity_curve = cum_value / cum_value.iloc[0] * total  
            
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=equity_curve.index,
                y=equity_curve,
                line=dict(color="#4A90D9"),
                name="Portfolio Value",
            ))
            fig_eq.update_layout(
                yaxis_title="Value ($)",
                height=400,
            )
            st.plotly_chart(fig_eq, use_container_width=True)
            
        with tab5:
            var_95 = risk.historical_var(port)
            es_95 = risk.expected_shortfall(port)
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=port * 100,
                nbinsx=50,
                marker_color="#4A90D9",
                name="Daily Returns",
            ))
            fig_hist.add_vline(
                x=var_95,
                line=dict(color="#00D09C", width=2, dash="dash"),
                annotation_text=f"VaR 95%: {var_95:.2%}",
            )
            
            fig_hist.add_vline(
                x=es_95,
                line=dict(color="#FF4B4B", width=2, dash="dash"),
                annotation_text=f"ES 95%: {es_95:.2%}",
            )
            fig_hist.update_layout(
                xaxis_title="Daily Returns",
                yaxis_title="Frequency",
                height=400,
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
        st.subheader("Risk Metrics")
        st.write("")
        m1, m2 = st.columns(2)
        with m1:
            st.write(f"#### Historical VaR (95%): {risk.historical_var(port):.2%}")
            st.write(f"#### Parametric VaR (95%): {risk.parametric_var(port):.2%}")
            st.write(f"#### Monte Carlo VaR (95%): {risk.montecarlo_var(port):.2%}")
        with m2:
            st.write(f"#### Expected Shortfall (95%): {risk.expected_shortfall(port):.2%}")
            st.write(f"#### Sharpe Ratio: {risk.sharpe_ratio(port, risk_free):.2f}")
            st.write(f"#### Annualized Volatility: {risk.portfolio_volatility(port):.1%}")
            