
import streamlit as st

st.set_page_config(
    page_title="Bosch Changsha – DSN Demo",
    page_icon="🛠️",
    layout="wide"
)

st.title("Bosch Changsha – DSN Demo")
st.subheader("Digital Twin & GenAI Maintenance Assistant")
st.markdown("""
This demo showcases two DSN-aligned tools:
- **Digital Twin**: What-if simulation for an engine test line (throughput, energy, overrun risk)
- **GenAI Maintenance Assistant**: Summarizes anomalies and proposes next actions (rule-based or OpenAI)

**TDSC Control Tower / DSN lens**  
- **Sense**: shop-floor signals (machine state, power draw, logs)  
- **Collaborate**: actionable insights for Solution Advocates and line leaders  
- **Optimize / Respond**: schedule tweaks, maintenance steps, risk reduction
""")

st.info("Use the sidebar to open each module.")
st.markdown("**Group 4 | SP Jain | Technology & Digitisation of Supply Chain Management**")
