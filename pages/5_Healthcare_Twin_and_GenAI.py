import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from PIL import Image

st.set_page_config(layout="wide")

# ---- Logo ----
logo = Image.open("assets/S-P-Jain_Final_logo_color.jpg")
st.image(logo, width=220)

st.title("Healthcare – Patient-Flow Digital Twin & GenAI Equipment Maintenance")
st.markdown("> Executive view: cut waiting time and keep critical equipment up by simulating ER flow and triaging equipment anomalies.")

# ====== Patient-Flow Digital Twin (ER/ICU) ======
st.subheader("Patient-Flow Digital Twin (ER)")
simple = st.sidebar.toggle("Presentation mode (simple)", value=True, key="hc_simple")

# Controls
if simple:
    arrivals_hr = st.sidebar.slider("Avg arrivals per hour", 6, 30, 15)
    triage_nurses = st.sidebar.slider("Triage nurses", 1, 6, 3)
    doctors = st.sidebar.slider("Doctors on shift", 1, 8, 4)
    beds = 20
else:
    arrivals_hr = st.sidebar.slider("Avg arrivals per hour", 4, 40, 18)
    triage_nurses = st.sidebar.slider("Triage nurses", 1, 10, 3)
    doctors = st.sidebar.slider("Doctors on shift", 1, 12, 5)
    beds = st.sidebar.slider("ER beds", 10, 40, 22)

# Simple M/M/c style approximation (very rough, for pedagogy)
triage_rate = triage_nurses * 12    # patients/hr triage capacity
doctor_rate = doctors * 6           # patients/hr treatment capacity
bottleneck_rate = min(triage_rate, doctor_rate)
throughput_hr = min(arrivals_hr, bottleneck_rate)

# Queue proxy: if arrivals exceed capacity, waiting grows
wait_growth = max(0, arrivals_hr - bottleneck_rate)
avg_wait_min = 10 + 6 * wait_growth    # pedagogical proxy
bed_util = min(1.0, throughput_hr / (beds * 1.5))  # crude occupancy fraction

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Throughput (patients/hr)", int(throughput_hr))
c2.metric("Est. Avg Wait (min)", int(avg_wait_min), delta="High" if avg_wait_min>30 else "OK")
c3.metric("Bed Utilization", f"{bed_util*100:.0f}%")

st.markdown("**Executive Summary**")
bullets = [
    f"Arrival rate **{arrivals_hr}/hr** vs bottleneck capacity **{bottleneck_rate}/hr**",
    f"Estimated waiting time **{avg_wait_min:.0f} min**; major lever: {'triage' if triage_rate<bottleneck_rate else 'doctors'}",
    f"Bed utilization ~ **{bed_util*100:.0f}%** (watch saturation >85%)"
]
st.markdown("- " + "\n- ".join(bullets))

chart = pd.DataFrame({
    "Stage": ["Arrivals", "Triage cap", "Doctor cap", "Throughput"],
    "Patients/hr": [arrivals_hr, triage_rate, doctor_rate, throughput_hr]
})
st.bar_chart(chart.set_index("Stage"))

st.caption("MBA lens: ties staffing decisions to patient experience (wait time) and cost/productivity (utilization).")

st.divider()

# ====== GenAI-like Equipment Maintenance (non-LLM heuristic for demo) ======
st.subheader("Equipment Maintenance Aide – Quick Scan (MRI example)")

# Toy sensor window
now = datetime.now()
ts = pd.date_range(now - timedelta(minutes=90), now, freq="5min")
n = len(ts)
df = pd.DataFrame({
    "timestamp": ts,
    "magnet_temp": np.clip(np.random.normal(4.2, 0.25, n), 3.6, 5.2),         # Kelvin
    "helium_level": np.clip(np.random.normal(82, 4, n), 65, 95),              # %
    "fault_code": np.where(np.random.rand(n)>0.92, "CRYO_WARN", "OK")
})

st.dataframe(df.tail(10), use_container_width=True)

# Heuristic assessment
avg_temp = df["magnet_temp"].tail(18).mean()
avg_he = df["helium_level"].tail(18).mean()
has_fault = (df["fault_code"].tail(18) == "CRYO_WARN").any()

risk, actions = [], []
if avg_temp > 4.6:
    risk.append("Magnet temp trending high (cooling efficiency risk).")
    actions.append("Check cryo-cooler and room HVAC; inspect chiller loop.")
if avg_he < 75:
    risk.append("Helium level trending low (quench risk if ignored).")
    actions.append("Plan top-up; verify boil-off rate and seals.")
if has_fault:
    risk.append("CRYO_WARN observed – intermittent cryo warning.")
    actions.append("Run OEM diagnostics; validate sensor calibration.")

if not risk:
    risk.append("No critical anomaly in last 90 minutes.")
    actions.append("Continue monitoring; alerts at Temp>4.6 K, He<75%.")

st.markdown("**Assessment**\n- " + "\n- ".join(risk))
st.markdown("**Next 1–2 Actions**\n- " + "\n- ".join(actions))
st.caption("Success metrics: higher equipment uptime, fewer cancellations, lower patient wait due to device outages.")
