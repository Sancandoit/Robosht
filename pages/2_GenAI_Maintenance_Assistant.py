import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.title("GenAI Maintenance Assistant")
st.markdown("> What this page answers: Can we meet plan within shift, at what energy cost, and where is the risk?")
st.caption("DSN-aligned: Sense (logs), Collaborate (clear insights), Respond (next actions)")

@st.cache_data
def load_logs():
    import os, pandas as pd
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

st.markdown("### Recent Signals")
st.dataframe(df.tail(10), use_container_width=True)

st.markdown("### Ask the Assistant")
prompt = st.text_area("Describe the issue or paste new log lines here:", 
                      value="Vibration spike on Station 2; temps rising from 75→92°C within 20 min. Error E42 occurred twice.")

use_llm = st.toggle("Use OpenAI (if API key set)", value=False)

def rule_based_advice(df_slice, user_prompt):
    v = df_slice["vibration"].tail(20).mean()
    t = df_slice["temperature"].tail(20).mean()
    errors = df_slice["error_code"].tail(50).value_counts()
    risk = []
    actions = []
    eta = "N/A"

    if v > 7:
        risk.append("Possible bearing wear or misalignment (high vibration).")
        actions.append("Schedule bearing inspection within next 24–48 hours; reduce RPM by 10% temporarily.")
        eta = "Likely failure within 3–5 days if untreated."
    if t > 85:
        risk.append("Thermal stress risk (elevated operating temperature).")
        actions.append("Check cooling flow, filters; verify ambient airflow; consider load balancing.")
        if eta == "N/A":
            eta = "Heat-related degradation possible in 1–2 weeks if persistent."
    if "E42" in df_slice["error_code"].values:
        risk.append("Repeat fault E42 (drive anomaly) detected.")
        actions.append("Run diagnostic on drive controller; check power quality and cables.")
    if not risk:
        risk.append("No critical anomalies in the last window; continue normal monitoring.")
        actions.append("Maintain routine checks; set alert thresholds for vibration >7 and temp >85°C.")
        eta = "No imminent failure indicated."

    msg = "**Assessment:**\n- " + "\n- ".join(risk)
    msg += "\n\n**Recommended Actions (next 24–48h):**\n- " + "\n- ".join(actions)
    msg += f"\n\n**Estimated Time-to-Attention:** {eta}"
    msg += "\n\n**Notes:** Map this to a maintenance playbook and capture fix as a reusable component."
    return msg

def llm_advice(user_prompt, df_slice):
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or OpenAI is None:
        return "OpenAI mode not configured; falling back to rule-based assistant."
    client = OpenAI(api_key=key)
    summary = df_slice.tail(20)[["timestamp","station","vibration","temperature","error_code"]].to_csv(index=False)
    sys = ("You are a maintenance engineer. Summarize anomalies from the data, estimate risk and time-to-failure, "
           "and propose concrete next actions. Be concise and actionable. Use bullet points.")
    user = f"User prompt: {user_prompt}\n\nRecent data:\n{summary}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":sys},{"role":"user","content":user}],
        temperature=0.2,
        max_tokens=400
    )
    return resp.choices[0].message.content

window_minutes = st.slider("Analysis window (minutes)", 10, 240, 60, step=10)
end_time = df["timestamp"].max()
start_time = end_time - timedelta(minutes=window_minutes)
window_df = df[(df["timestamp"]>=start_time) & (df["timestamp"]<=end_time)]

if st.button("Analyze"):
    with st.spinner("Analyzing signals..."):
        if use_llm:
            out = llm_advice(prompt, window_df)
        else:
            out = rule_based_advice(window_df, prompt)
        st.markdown(out)

st.caption("MBA note: This operationalizes DSN’s Sense→Respond loop for front-line teams, tied to Bosch’s DTE roles.")
