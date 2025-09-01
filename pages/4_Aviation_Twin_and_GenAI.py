import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from PIL import Image

st.set_page_config(layout="wide")

# ---- Logo ----
logo = Image.open("assets/S-P-Jain_Final_logo_color.jpg")
st.image(logo, width=220)

st.title("Aviation – Turnaround Digital Twin & GenAI Maintenance")
st.markdown("> Executive view: reduce aircraft turnaround time and prevent technical delays using a simple digital twin for ground ops + a GenAI maintenance aide for anomalies.")

# ====== Turnaround Digital Twin (Gate Ops) ======
st.subheader("Turnaround Digital Twin (Gate Operations)")
simple = st.sidebar.toggle("Presentation mode (simple)", value=True, key="av_simple")

# Controls
if simple:
    pax = st.sidebar.slider("Passengers boarding", 80, 220, 180)
    cleaners = st.sidebar.slider("Cleaners on duty", 2, 8, 4)
    fuel_qty = st.sidebar.slider("Fuel uplift (tons)", 1, 20, 8)
    tech_checks = 1
else:
    pax = st.sidebar.slider("Passengers boarding", 80, 220, 180)
    cleaners = st.sidebar.slider("Cleaners on duty", 1, 12, 5)
    fuel_qty = st.sidebar.slider("Fuel uplift (tons)", 1, 25, 10)
    tech_checks = st.sidebar.slider("Tech inspection steps", 0, 3, 1)

# Simple model
board_rate = 22  # pax/min per door
doors = 2
boarding_min = np.ceil(pax / (board_rate * doors))
cleaning_min = max(12, 40 - 3 * cleaners)
fuel_min = 8 + 0.8 * fuel_qty
tech_min = 10 + 7 * tech_checks

turnaround_min = int(boarding_min + cleaning_min + fuel_min + tech_min)
target_min = 45
slack_min = target_min - turnaround_min

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Boarding (min)", int(boarding_min))
c2.metric("Cleaning (min)", int(cleaning_min))
c3.metric("Fueling (min)", int(fuel_min))
c4.metric("Tech checks (min)", int(tech_min))

c5, c6 = st.columns(2)
c5.metric("Total Turnaround (min)", turnaround_min, delta=None)
c6.metric("Slack vs Target (min)", slack_min, delta="OK" if slack_min>=0 else "Shortfall")

# Summary and chart
st.markdown("**Executive Summary**")
bullets = [
    f"Turnaround estimated **{turnaround_min} min** vs target **{target_min} min** → {'feasible' if slack_min>=0 else 'shortfall'}",
    f"Biggest lever: {'cleaning crew' if cleaning_min>fuel_min and cleaning_min>boarding_min else 'fuel planning' if fuel_min>cleaning_min else 'boarding flow'}",
    "Scenario knobs: crew levels, boarding doors, fuel quantity, inspection steps"
]
st.markdown("- " + "\n- ".join(bullets))

timeline = pd.DataFrame({
    "Step": ["Boarding", "Cleaning", "Fueling", "Tech checks"],
    "Minutes": [boarding_min, cleaning_min, fuel_min, tech_min]
})
st.bar_chart(timeline.set_index("Step"))

st.caption("MBA lens: aligns on-time performance to resource decisions at the gate; simple ‘what-if’ builds intuition quickly.")

st.divider()

# ====== GenAI-like Maintenance Aide (non-LLM heuristic for demo) ======
st.subheader("Maintenance Aide – Quick Anomaly Read (Demo)")

# Toy sensor window
now = datetime.now()
ts = pd.date_range(now - timedelta(minutes=60), now, freq="5min")
n = len(ts)
df = pd.DataFrame({
    "timestamp": ts,
    "engine_vibration": np.clip(np.random.normal(5.5, 0.8, n), 3.5, 9.5),
    "egt": np.clip(np.random.normal(560, 30, n), 480, 650),  # Exhaust Gas Temp
    "fault_code": np.where(np.random.rand(n)>0.9, "E42", "OK")
})

st.dataframe(df.tail(8), use_container_width=True)

# Heuristic assessment
avg_vib = df["engine_vibration"].tail(12).mean()
avg_egt = df["egt"].tail(12).mean()
has_fault = (df["fault_code"].tail(12) == "E42").any()

risk, actions = [], []
if avg_vib > 7.0: 
    risk.append("Vibration high – potential fan/LP spool imbalance.")
    actions.append("Run borescope if persists; balance check on next ground slot.")
if avg_egt > 620: 
    risk.append("EGT trending hot – check bleed/FADEC trims.")
    actions.append("Verify cooling/bleed; calibrate sensors in line with MEL.")
if has_fault:
    risk.append("Fault E42 observed – transient drive anomaly.")
    actions.append("Pull quick access recorder; inspect harness/connector.")

if not risk:
    risk.append("No critical anomaly in last hour.")
    actions.append("Continue normal ops; set alert thresholds Vib>7.0, EGT>620°C.")

st.markdown("**Assessment**\n- " + "\n- ".join(risk))
st.markdown("**Next 1–2 Actions**\n- " + "\n- ".join(actions))
st.caption("Success metrics: shorter MTTR, fewer tech-caused delays, higher aircraft availability (utilization).")
