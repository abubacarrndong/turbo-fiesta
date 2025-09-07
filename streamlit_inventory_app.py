import io
import pandas as pd
import numpy as np
import streamlit as st

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

st.set_page_config(page_title="Gambia AI Inventory Forecast", layout="wide")

def parse_uploaded_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file)
    return df

def ensure_sales_format(df):
    required = {"Date", "Product", "Units_Sold"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}. Required: Date, Product, Units_Sold. Optional: Current_Stock")
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Units_Sold"] = pd.to_numeric(df["Units_Sold"], errors="coerce").fillna(0)
    if "Current_Stock" in df.columns:
        df["Current_Stock"] = pd.to_numeric(df["Current_Stock"], errors="coerce").fillna(0)
    else:
        df["Current_Stock"] = 0
    return df

def prophet_forecast(series_df, periods):
    model = Prophet(seasonality_mode="additive", weekly_seasonality=True, daily_seasonality=False)
    model.fit(series_df)
    future = model.make_future_dataframe(periods=periods)
    fc = model.predict(future)
    return fc[["ds", "yhat", "yhat_lower", "yhat_upper"]]

def moving_average_forecast(series_df, periods, window=7):
    series_df = series_df.sort_values("ds")
    last_avg = series_df["y"].tail(window).mean() if not series_df.empty else 0.0
    last_date = series_df["ds"].max() if not series_df.empty else pd.Timestamp.today().normalize()
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, periods + 1)]
    fc = pd.DataFrame({
        "ds": future_dates,
        "yhat": [last_avg] * periods,
        "yhat_lower": [max(0, last_avg * 0.8)] * periods,
        "yhat_upper": [last_avg * 1.2] * periods,
    })
    return fc

def forecast_product(product_df, horizon_days):
    df = product_df.rename(columns={"Date": "ds", "Units_Sold": "y"})[["ds", "y"]].dropna()
    df = df.groupby("ds", as_index=False)["y"].sum()
    if PROPHET_AVAILABLE and len(df) >= 7:
        try:
            fc = prophet_forecast(df, horizon_days)
        except Exception:
            fc = moving_average_forecast(df, horizon_days)
    else:
        fc = moving_average_forecast(df, horizon_days)
    return fc

def add_safety_and_risk(fc, margin_percent, current_stock):
    fc = fc.copy()
    fc["Suggested_Inventory"] = (fc["yhat"] * (1 + margin_percent / 100.0)).round()
    fc["Current_Stock"] = current_stock
    fc["Stockout_Risk"] = fc["Suggested_Inventory"] > fc["Current_Stock"]
    return fc

st.title("🇬🇲 Gambia AI Inventory Forecast")

uploaded = st.file_uploader("Upload Sales CSV (Date, Product, Units_Sold, Current_Stock optional)", type=["csv", "xlsx"])

horizon_days = st.number_input("Forecast horizon (days)", min_value=7, max_value=90, value=30)
margin = st.slider("Safety margin (%)", min_value=0, max_value=200, value=20, step=5)

if uploaded:
    try:
        df = parse_uploaded_csv(uploaded)
        df = ensure_sales_format(df)
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

    st.success("✅ Data loaded successfully")
    st.write(df.head())

    products = df["Product"].unique()
    all_results = []

    for prod in products:
        prod_df = df[df["Product"] == prod]
        forecast = forecast_product(prod_df, horizon_days)
        stock = prod_df["Current_Stock"].iloc[-1] if not prod_df.empty else 0
        forecast = add_safety_and_risk(forecast, margin, stock)
        forecast["Product"] = prod
        all_results.append(forecast)

    results = pd.concat(all_results)
    st.write("### Forecast Results", results.head())

    st.download_button("📥 Download full forecast CSV", data=results.to_csv(index=False).encode("utf-8"), file_name="forecast.csv", mime="text/csv")
else:
    st.info("Upload a CSV file to get started.")
