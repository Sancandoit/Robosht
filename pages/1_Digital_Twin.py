import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Digital Twin – Engine Test Line (What-If Scheduling)")
st.markdown("> What this page answers: Can we meet plan within the shift, at what energy cost, and where is the overrun risk?")

@st.cache_data
def load_schedule():
    import os
    path = "data/line_schedule.csv"
    if not os.path.exists(path):
        # Fallback synthetic schedule so the app never breaks
        df = pd.DataFrame({
            "start_time": pd.date_range("2025-08-29 08:00", periods=8, freq="30min"),
            "planned_minutes": [30]*8,
            "planned_units": [8]*8
        })
    else:
        df = pd.read_csv(path, parse_dates=["start_time"])
    df["end_time"] = df["start_time"] + pd.to_timedelta(df["planned_minutes"], unit="m")
    return df

df = load_schedule()

# ---------- Controls ----------
simple = st.session_state.get("present_mode", True)

st.sidebar.header("Scenario Controls")
if simple:
    # Minimal controls for class
    shift_hours = st.sidebar.slider("Shift length (h)", 6, 12, 8)
    test_time_min = st.sidebar.slider("Avg test time (min)", 10, 60, 30)
    utilization = st.sidebar.slider("Utilization (%)", 50, 95, 80)
    parallel_stations = st.sidebar.slider("Stations", 1, 6, 3)
    power_factor = 1.05
    downtime_buffer = 15
    peak_tariff = 0.12
else:
    # Full controls for Q&A
    shift_hours = st.sidebar.slider("Shift length (h)", 6, 12, 8)
    test_time_min = st.sidebar.slider("Avg test time (min)", 10, 60, 30)
    utilization = st.sidebar.slider("Utilization (%)", 50, 95, 80)
    power_factor = st.sidebar.slider("Energy load factor", 0.8, 1.5, 1.05, step=0.01)
    parallel_stations = st.sidebar.slider("Stations", 1, 6, 3)
    downtime_buffer = st.sidebar.slider("Micro-stops (min)", 0, 60, 15)
    peak_tariff = st.sidebar.slider("Tariff ($/kWh)", 0.05, 0.25, 0.12)

# Quick presets (one click)
cA, cB, cC = st.columns(3)
if cA.button("Preset: Baseline"): utilization, power_factor, downtime_buffer = 80, 1.05, 15
if cB.button("Preset: Energy-save"): utilization, power_factor, downtime_buffer = 75, 0.92, 15
if cC.button("Preset: Rush order"): utilization, power_factor, downtime_buffer = 90, 1.10, 10

# ---------- Computation ----------
shift_minutes = shift_hours * 60
effective_minutes = shift_minutes - downtime_buffer
cycle_with_buffer = test_time_min * (100/utilization)
units_capacity = int(np.floor(effective_minutes / cycle_with_buffer) * parallel_stations)

energy_per_unit_kwh = 2.0 * power_factor     # simple synthetic model
energy_total_kwh = units_capacity * energy_per_unit_kwh
energy_cost = energy_total_kwh * peak_tariff

planned_units = df["planned_units"].sum()
overrun_minutes = max(0, planned_units - units_capacity) * (cycle_with_buffer / parallel_stations)
overrun_flag = overrun_minutes > 0
feasible = "Yes" if not overrun_flag else "No"

# ---------- KPI Row ----------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Planned Units", f"{planned_units}")
c2.metric("Capacity (units)", f"{units_capacity}")
c3.metric("Overrun Risk (min)", f"{overrun_minutes:.0f}", delta="⚠️" if overrun_flag else "✅")
c4.metric("Energy (kWh)", f"{energy_total_kwh:.1f}")
c5.metric("Est. Energy Cost ($)", f"{energy_cost:,.2f}")

# traffic-light helper
def badge(txt, color):
    st.markdown(f"<div style='display:inline-block;padding:6px 10px;border-radius:8px;background:{color};color:#000;font-weight:600;margin-right:6px;'>{txt}</div>", unsafe_allow_html=True)

st.subheader("Executive Summary")
colA, colB = st.columns([2,1])

with colA:
    bullet1 = f"Capacity {units_capacity} vs plan {planned_units} → {'feasible' if not overrun_flag else 'shortfall'}"
    bullet2 = f"Energy ≈ {energy_total_kwh:.1f} kWh (≈ ${energy_cost:,.0f})"
    bullet3 = "Main lever: " + ("reduce cycle or +1 station" if overrun_flag else "lock plan; trial shorter cycles")
    st.markdown(f"- {bullet1}\n- {bullet2}\n- {bullet3}")
with colB:
    if overrun_flag: badge("Overrun risk", "#FADBD8")
    else: badge("On plan", "#D5F5E3")
    if power_factor > 1.2: badge("High energy load", "#FDEDEC")
    if downtime_buffer > 30: badge("Micro-stops high", "#FDEBD0")


# ---------- Charts ----------
st.subheader("Workload by Station")
df_vis = df.copy()
df_vis["station"] = (df_vis.index % parallel_stations) + 1
df_vis["actual_minutes"] = np.clip(df_vis["planned_minutes"] * (1 + (1-utilization/100)*0.2), 5, None)
fig = px.bar(df_vis, x="station", y="actual_minutes", color="station", title="Load per Station (min)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Energy Profile (Synthetic)")
time_axis = pd.date_range(df["start_time"].min(), periods=shift_minutes, freq="min")
base = np.sin(np.linspace(0, 6.283, len(time_axis))) * 0.1 + 1
energy_series = base * power_factor * parallel_stations
energy_df = pd.DataFrame({"time": time_axis, "kW": energy_series*10})
fig2 = px.line(energy_df, x="time", y="kW", title="Energy Load (kW) across Shift")
st.plotly_chart(fig2, use_container_width=True)

# ---------- Scenario save/compare ----------
st.subheader("Scenario Compare")
if "scenarios" not in st.session_state:
    st.session_state.scenarios = {}
name = st.text_input("Save scenario as (e.g., Baseline, +1 Station)")
if st.button("Save scenario") and name:
    st.session_state.scenarios[name] = dict(
        planned=planned_units, capacity=units_capacity, overrun=overrun_minutes,
        kwh=float(f"{energy_total_kwh:.2f}"), cost=float(f"{energy_cost:.2f}")
    )
if st.session_state.scenarios:
    st.dataframe(pd.DataFrame(st.session_state.scenarios).T)

# ---------- Recommendations ----------
st.subheader("Recommendations")
recs = []
if overrun_flag:
    recs.append("Reduce cycle time by 5–10% via standardised pre-checks or add micro-shift (+30 min).")
    recs.append("Consider +1 parallel station if demand persists.")
if power_factor > 1.2:
    recs.append("Shift energy-intensive tests off-peak or sequence for flatter load.")
if downtime_buffer > 30:
    recs.append("Investigate micro-stops; deploy quick kaizen with Solution Advocates.")
if not recs:
    recs.append("Plan is feasible. Pilot shorter cycles to create variability buffer.")
for r in recs:
    st.write("•", r)

st.caption("MBA note: DSN control-tower-lite — capture → simulate → decide on one page.")
