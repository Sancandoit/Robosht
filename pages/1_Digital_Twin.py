import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

st.title("Digital Twin – Engine Test Line (What-If Scheduling)")
st.caption("DSN-aligned: Sense (signals), Optimize (simulate), Respond (reschedule)")

@st.cache_data
def load_schedule():
    df = pd.read_csv("data/line_schedule.csv", parse_dates=["start_time"])
    df["end_time"] = df["start_time"] + pd.to_timedelta(df["planned_minutes"], unit="m")
    return df

df = load_schedule()

st.sidebar.header("Scenario Controls")
shift_hours = st.sidebar.slider("Shift length (hours)", 6, 12, 8)
test_time_min = st.sidebar.slider("Avg test duration per unit (min)", 10, 60, 30)
utilization = st.sidebar.slider("Target utilization (%)", 50, 95, 80)
power_factor = st.sidebar.slider("Energy load factor (0.8–1.5)", 0.8, 1.5, 1.05, step=0.01)
parallel_stations = st.sidebar.slider("Parallel test stations", 1, 6, 3)
downtime_buffer = st.sidebar.slider("Expected micro-stops per shift (min)", 0, 60, 15)

# Compute throughput & energy
shift_minutes = shift_hours * 60
effective_minutes = shift_minutes - downtime_buffer
cycle_with_buffer = test_time_min * (100/utilization)
units_capacity = int(np.floor(effective_minutes / cycle_with_buffer) * parallel_stations)
energy_per_unit_kwh = 2.0 * power_factor  # synthetic model
energy_total_kwh = units_capacity * energy_per_unit_kwh

# Overrun risk heuristic
planned_units = df["planned_units"].sum()
overrun_minutes = max(0, planned_units - units_capacity) * (cycle_with_buffer / parallel_stations)
overrun_flag = overrun_minutes > 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Planned Units (shift)", f"{planned_units}")
col2.metric("Capacity (units)", f"{units_capacity}")
col3.metric("Total Energy (kWh)", f"{energy_total_kwh:.1f}")
col4.metric("Overrun Risk (min)", f"{overrun_minutes:.0f}", delta="⚠️" if overrun_flag else "✅")

st.markdown("### Workload by Station (synthetic)")
df_vis = df.copy()
df_vis["station"] = (df_vis.index % parallel_stations) + 1
df_vis["actual_minutes"] = np.clip(df_vis["planned_minutes"] * (1 + (1-utilization/100)*0.2), 5, None)
fig = px.bar(df_vis, x="station", y="actual_minutes", color="station", title="Load per Station (min)")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Energy Profile (synthetic)")
time_axis = pd.date_range(df["start_time"].min(), periods=shift_minutes, freq="min")
base = np.sin(np.linspace(0, 6.283, len(time_axis))) * 0.1 + 1
energy_series = base * power_factor * parallel_stations
energy_df = pd.DataFrame({"time": time_axis, "kW": energy_series*10})
fig2 = px.line(energy_df, x="time", y="kW", title="Energy Load (kW) across Shift")
st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Recommendations")
recs = []
if overrun_flag:
    recs.append("Reduce test duration by 5–10% via standardized steps or pre-checks (tech illustrator playbook).")
    recs.append("Increase parallel stations by 1 or add micro-shift (+30 min) to eliminate overrun.")
if power_factor > 1.2:
    recs.append("Shift energy-intensive tests away from peak windows to flatten the load curve (AI energy optimizer).")
if downtime_buffer > 30:
    recs.append("Investigate micro-stops root causes; deploy quick kaizen with Solution Advocates.")
if not recs:
    recs.append("Plan is feasible within shift. Consider piloting shorter cycles to create buffer for variability.")
for r in recs:
    st.write("•", r)

st.caption("MBA note: This is a DSN control-tower-lite view—tying capture→simulate→decide into a single loop.")
