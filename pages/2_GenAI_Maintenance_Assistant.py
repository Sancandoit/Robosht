import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta

st.set_page_config(layout="wide")
st.title("GenAI Maintenance Assistant")
st.markdown("> What this page answers: What’s going wrong, how risky is it, and what should technicians do next?")

# -------- Data loader with fallback --------
@st.cache_data
def load_logs():
    path = "data/sensor_logs.csv"
    if not os.path.exists(path):
        df = pd.DataFrame({
            "timestamp": pd.date_range("2025-08-29 08:00", periods=16, freq="5min"),
            "station": [1,2,2,2,1,2,3,2,1,3,2,1,3,2,1,3],
            "vibration": [4.1,5.0,7.5,7.2,4.8,7.9,5.5,7.1,4.2,5.8,7.6,4.0,5.4,7.3,4.3,5.6],
            "temperature": [74,78,86,88,80,90,82,89,76,83,92,75,81,91,77,82],
            "error_code": ["OK","OK","E42","OK","OK","E42","OK","OK","OK","OK","OK","OK","OK","OK","OK","OK"]
        })
    else:
        df = pd.read_csv(path, parse_dates=["timestamp"])
    return df

df = load_logs()

# -------- Recent signals table --------
st.subheader("Recent Signals")
st.dataframe(df.tail(12), use_container_width=True)

# -------- Preset prompts --------
st.subheader("Describe the issue")
preset_col1, preset_col2, preset_col3 = st.columns(3)
if "prompt" not in st.session_state:
    st.session_state.prompt = "Vibration spike on Station 2; temps rising from 75→92°C within 20 min. Error E42 occurred twice."

if preset_col1.button("Thermal issue"):
    st.session_state.prompt = "Temperature trending above 85°C on Station 2; cooling possibly impaired."
if preset_col2.button("Vibration issue"):
    st.session_state.prompt = "Vibration above 7.0 on Station 2; potential bearing wear or misalignment."
if preset_col3.button("Drive fault"):
    st.session_state.prompt = "Repeated fault E42 on Station 2; suspected drive anomaly or power quality issue."

prompt = st.text_area("Issue / new log lines", value=st.session_state.prompt, height=100)

# -------- Heuristic risk + RUL estimate --------
window_minutes = st.slider("Analysis window (minutes)", 10, 240, 60, step=10)
end_time = df["timestamp"].max()
start_time = end_time - timedelta(minutes=window_minutes)
window_df = df[(df["timestamp"]>=start_time) & (df["timestamp"]<=end_time)]

avg_v = window_df["vibration"].tail(20).mean()
avg_t = window_df["temperature"].tail(20).mean()
rul_days = max(1, 7 - int((avg_v>7)*3 + (avg_t>85)*2))  # toy model for demo

m1, m2 = st.columns(2)
m1.metric("Estimated RUL (days)", rul_days)
m2.metric("Risk signals (last window)", f"Vib>{avg_v:.1f}, Temp>{avg_t:.0f}°C")

# -------- Advice (rule-based, fast) --------
def rule_based_advice(df_slice, user_prompt):
    v = df_slice["vibration"].tail(20).mean()
    t = df_slice["temperature"].tail(20).mean()
    errors = df_slice["error_code"].tail(50).value_counts()

    risk, actions = [], []
    eta = "N/A"

    if v > 7:
        risk.append("High vibration indicates possible bearing wear/misalignment.")
        actions.append("Reduce RPM by 10%, schedule bearing inspection in 24–48h.")
        eta = "Likely failure within 3–5 days if untreated."
    if t > 85:
        risk.append("Thermal stress risk (elevated temperature).")
        actions.append("Check coolant/airflow; clean filters; consider load balancing.")
        if eta == "N/A":
            eta = "Heat-related degradation possible in 1–2 weeks if persistent."
    if "E42" in df_slice["error_code"].values:
        risk.append("Repeat fault E42 (drive anomaly).")
        actions.append("Run drive diagnostics; verify power quality and cable integrity.")
    if not risk:
        risk.append("No critical anomalies in the window.")
        actions.append("Continue normal monitoring; set alert thresholds Vib>7, Temp>85°C.")
        eta = "No imminent failure indicated."

    msg = "**Assessment**\n- " + "\n- ".join(risk)
    msg += "\n\n**Recommended Actions (next 24–48h)**\n- " + "\n- ".join(actions)
    msg += f"\n\n**Estimated Time-to-Attention**: {eta}"
    msg += "\n\n**Notes**: Capture fix as a reusable component and add to playbook."
    return msg

use_llm = st.toggle("Use OpenAI (if `OPENAI_API_KEY` set in Secrets)", value=False)

# -------- LLM advice (module-level API; works across SDK versions) --------
def llm_advice(user_prompt, df_slice):
    try:
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            return "OpenAI key not configured; using rule-based advice instead."

        import openai
        openai.api_key = key

        summary = df_slice.tail(20)[["timestamp","station","vibration","temperature","error_code"]].to_csv(index=False)
        sys_msg = ("You are a maintenance engineer. Summarize anomalies from the data, estimate risk and time-to-failure, "
                   "and propose concrete next actions. Be concise and actionable. Use bullet points.")
        user_msg = f"User prompt: {user_prompt}\n\nRecent data (CSV):\n{summary}"

        # Try modern v1.x call
        try:
            resp = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":sys_msg},
                          {"role":"user","content":user_msg}],
                temperature=0.2,
                max_tokens=400
            )
            return resp.choices[0].message.content
        except AttributeError:
            # Fallback for older 0.x SDKs
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":sys_msg},
                          {"role":"user","content":user_msg}],
                temperature=0.2,
                max_tokens=400
            )
            return resp.choices[0].message["content"]

    except Exception as e:
        return f"LLM call failed ({e}); using rule-based advice instead."

# -------- Run analysis (single block) --------
concise = st.toggle("3-sentence summary (presentation)", value=True, key="concise_toggle")

def make_concise(text):
    if not concise:
        return text
    lines = [l for l in text.splitlines() if l.strip()]
    keep = []
    for l in lines:
        if l.lstrip().startswith(("-", "•")):
            keep.append(l)
        if len(keep) == 3:
            break
    if not keep:
        keep = lines[:3]
    return "**Top-line Summary**\n" + "\n".join(keep)

if st.button("Analyze", key="analyze_btn"):
    with st.spinner("Analyzing signals..."):
        raw = llm_advice(prompt, window_df) if use_llm else rule_based_advice(window_df, prompt)
        st.markdown(make_concise(raw))
        if concise:
            st.caption("Full details hidden in presentation mode.")
        else:
            with st.expander("Full recommendation"):
                st.markdown(raw)

# -------- Export as maintenance ticket --------
import io
if st.button("Export as maintenance ticket (CSV)"):
    ticket = pd.DataFrame([{"issue": prompt, "rul_days": rul_days}])
    csv = ticket.to_csv(index=False).encode("utf-8")
    st.download_button("Download ticket", csv, "maintenance_ticket.csv", "text/csv")

st.caption("MBA note: This operationalizes the DSN Sense→Respond loop for front-line teams, aligned to DTE roles.")
