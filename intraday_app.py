import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import json

# --------------------------- Helper Functions ---------------------------

def fetch_nifty_data():
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d", interval="1d")
        latest = hist.iloc[-2]  # Use previous day's data
        return {
            "high": round(latest["High"], 2),
            "low": round(latest["Low"], 2),
            "close": round(latest["Close"], 2),
            "date": latest.name.strftime("%Y-%m-%d")
        }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_pivots(high, low, close):
    pp = round((high + low + close) / 3, 2)
    r1 = round((2 * pp) - low, 2)
    r2 = round(pp + (high - low), 2)
    r3 = round(r1 + (high - low), 2)
    s1 = round((2 * pp) - high, 2)
    s2 = round(pp - (high - low), 2)
    s3 = round(s1 - (high - low), 2)

    lb = round((high + low) / 2, 2)
    ub = round(pp + (pp - lb), 2)

    width_ub = round(((ub - pp) / pp) * 100, 2)
    width_lb = round(((pp - lb) / pp) * 100, 2)

    return {
        "Central Pivot (CP)": pp,
        "Upper Boundary (UB)": ub,
        "Lower Boundary (LB)": lb,
        "R1": r1, "R2": r2, "R3": r3,
        "S1": s1, "S2": s2, "S3": s3,
        "UB%": width_ub,
        "LB%": width_lb
    }

def save_daily_log(data, date):
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{date}.json", "w") as f:
        json.dump(data, f, indent=4)

def load_previous_logs():
    if not os.path.exists("logs"):
        return []
    files = sorted(os.listdir("logs"), reverse=True)
    return [f.replace(".json", "") for f in files]

# --------------------------- Streamlit UI ---------------------------

st.set_page_config(page_title="📊 Intraday Pivot Action Plan", layout="wide")
st.title("📊💰 Intraday Trading Action Plan")

today = datetime.now().strftime("%Y-%m-%d")
st.markdown(f"### 📅 Today's Date: `{today}`")

data = fetch_nifty_data()
if data:
    st.success(f"✅ Auto-Fetched Data for {data['date']}")
    st.write(f"**High:** {data['high']} | **Low:** {data['low']} | **Close:** {data['close']}")
else:
    st.stop()

# --------------------------- Pivot & CPR ---------------------------

pivots = calculate_pivots(data["high"], data["low"], data["close"])

st.markdown("### 📐 Pivot Points & CPR Levels")
df = pd.DataFrame([
    ["Central Pivot (CP)", pivots["Central Pivot (CP)"]],
    ["Upper Boundary (UB)", pivots["Upper Boundary (UB)"]],
    ["Lower Boundary (LB)", pivots["Lower Boundary (LB)"]],
    ["R1", pivots["R1"]],
    ["R2", pivots["R2"]],
    ["R3", pivots["R3"]],
    ["S1", pivots["S1"]],
    ["S2", pivots["S2"]],
    ["S3", pivots["S3"]],
    ["% from PP to UB", f"{pivots['UB%']}%"],
    ["% from PP to LB", f"{pivots['LB%']}%"]
], columns=["Level", "Value"])
st.dataframe(df, use_container_width=True)

# --------------------------- CPR Interpretation ---------------------------

st.markdown("### 🔍 CPR Bias Interpretation")
if pivots["UB%"] < 0.3 and pivots["LB%"] < 0.3:
    st.warning("⚠️ Narrow CPR - Trend Day Likely")
elif pivots["UB%"] > 0.6 or pivots["LB%"] > 0.6:
    st.info("🔄 Wide CPR - Range-Bound Day Possible")
else:
    st.success("📉 Moderate CPR - Balanced Movement")

# --------------------------- Candlestick Chart ---------------------------

st.markdown("### 📊 Nifty50 Candlestick Chart with CPR & Pivot Overlay")

candles = yf.download("^NSEI", period="5d", interval="1d").reset_index()
candles["Date"] = candles["Date"].dt.strftime("%Y-%m-%d")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=candles["Date"],
    open=candles["Open"],
    high=candles["High"],
    low=candles["Low"],
    close=candles["Close"],
    name="Nifty50"
))

# CPR zone
fig.add_shape(type="rect",
              x0=data["date"], x1=today,
              y0=pivots["Lower Boundary (LB)"], y1=pivots["Upper Boundary (UB)"],
              line=dict(color="orange", width=1),
              fillcolor="rgba(255, 165, 0, 0.2)",
              layer="below")

# Add levels
def add_level(y, name, color):
    fig.add_hline(y=y, line_dash="dash", line_color=color, annotation_text=name, annotation_position="right")

add_level(pivots["Central Pivot (CP)"], "Central Pivot (CP)", "orange")
add_level(pivots["R1"], "R1", "green")
add_level(pivots["R2"], "R2", "green")
add_level(pivots["R3"], "R3", "green")
add_level(pivots["S1"], "S1", "red")
add_level(pivots["S2"], "S2", "red")
add_level(pivots["S3"], "S3", "red")
add_level(data["high"], "Prev High", "blue")
add_level(data["low"], "Prev Low", "blue")
add_level(data["close"], "Prev Close", "gray")

fig.update_layout(
    title="📈 Nifty50 Candlestick with CPR & Pivots",
    yaxis_title="Price",
    xaxis_title="Date",
    height=600
)
st.plotly_chart(fig, use_container_width=True)

# --------------------------- Checklist & Notes ---------------------------

st.markdown("### ✅ Pre-Market Checklist")
checklist = {
    "global_sentiment": st.checkbox("🌍 Global Market Sentiment Checked"),
    "economic_events": st.checkbox("📰 Key Economic Events Reviewed"),
    "previous_levels": st.checkbox("📏 Previous Day's High/Low Plotted"),
    "pivot_marked": st.checkbox("📍 Pivot Points & CPR Marked"),
    "vwap_plotted": st.checkbox("📈 VWAP Plotted on Chart"),
    "bias_made": st.checkbox("🧭 Bias (Bullish/Bearish/Neutral) Identified"),
    "trade_planned": st.checkbox("📝 Trade Plan Finalized")
}

st.markdown("### 🧠 Trade Notes")
notes = st.text_area("✍️ Write your intraday trade notes here...", height=200)

if st.button("💾 Save Today's Plan"):
    log_data = {
        "date": today,
        "pivots": pivots,
        "checklist": checklist,
        "notes": notes
    }
    save_daily_log(log_data, today)
    st.success("✅ Plan Saved Successfully!")

# --------------------------- Load Past Logs ---------------------------

st.markdown("### 📂 View Previous Logs")
logs = load_previous_logs()
if logs:
    selected_day = st.selectbox("📅 Select a Date", logs)
    if selected_day:
        with open(f"logs/{selected_day}.json", "r") as f:
            st.json(json.load(f))

