import streamlit as st
from PIL import Image

present_mode = st.sidebar.toggle("Presentation mode (simple)", value=True)
st.session_state["present_mode"] = present_mode

st.set_page_config(
    page_title="Bosch Changsha – DSN Demo",
    page_icon="🛠️",
    layout="wide"
)

# ---- Logo ----
logo = Image.open("assets/S-P-Jain_Final_logo_color.jpg")
st.image(logo, width=220)

# ---- App Title ----
st.title("Bosch Changsha – DSN Demo")
st.subheader("Digital Twin & GenAI Maintenance Assistant")

st.markdown("""
This demo showcases two DSN-aligned tools:
- **Digital Twin**: What-if simulation for an engine test line (throughput, energy, overrun risk)
- **GenAI Maintenance Assistant**: Summarizes anomalies and proposes next actions (rule-based or OpenAI)
- **DSN & ROI**: Capability dashboard and reuse multiplier for cultural adoption

**TDSC / DSN lens**  
- **Sense**: shop-floor signals (machine state, power draw, logs)  
- **Collaborate**: actionable insights for Solution Advocates and line leaders  
- **Optimize / Respond**: schedule tweaks, maintenance steps, risk reduction
""")

st.info("Use the sidebar to open each module.")
st.markdown("**Group 2 | SP Jain | Technology & Digitisation of Supply Chains**")
