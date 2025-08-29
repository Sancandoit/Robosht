import streamlit as st

from PIL import Image

# ---- Logo ----
logo = Image.open("assets/S-P-Jain_Final_logo_color.jpg")
st.image(logo, width=220)

st.set_page_config(layout="wide")
st.title("DSN & ROI – Cultural Enablement and Reuse Multiplier")
st.markdown("> What this page answers: Are we building future delivery capacity, and how much ROI scales via replication across plants?")

with st.container():
    left, right = st.columns(2)

    with left:
        st.subheader("Cultural Enablement Dashboard (Leading Indicators)")
        l2 = st.slider("Level 2 Coverage of workforce (%)", 0, 100, 61)
        sa = st.slider("Active Solution Advocates (% of nominated)", 0, 100, 45)
        t2 = st.slider("Median Time-to-Level 2 (days)", 10, 180, 60)

        # Capability score (weighted to leading indicators)
        # 40% L2 coverage + 40% SA activation + 20% speed (faster -> higher score)
        capability_score = 0.4*l2 + 0.4*sa + 0.2*(180 - t2)/1.8  # -> 0..100
        st.metric("Capability Score (0–100)", f"{capability_score:.1f}")
        st.caption("Interpretation: >75 indicates strong forward capacity to deliver DX. <50 suggests investment in skills & SA activation.")

    with right:
        st.subheader("Network ROI via Reuse")
        plants = st.slider("Plants replicating this year (#)", 0, 10, 2)
        rep_time = st.slider("Median replication time (months)", 1, 12, 6)
        base_roi = st.number_input("Base ROI at origin plant ($)", min_value=10000, max_value=5000000, value=120000, step=10000)

        # Reuse multiplier: more plants and faster replication => larger multiplier
        reuse_multiplier = max(1.0, plants * (12/rep_time))
        network_roi = base_roi * reuse_multiplier

        c1, c2 = st.columns(2)
        c1.metric("Reuse Multiplier", f"{reuse_multiplier:.2f}")
        c2.metric("Estimated Network ROI", f"${network_roi:,.0f}")
        st.caption("MBA note: replication velocity compounds value across the Digital Supply Network. Faster median replication time → higher multiplier.")

st.divider()
st.markdown("**How this maps to TDSC / DSN:** Leading indicators (L2, SA, Time-to-L2) reflect *Sense/Collaborate* capability; reuse multiplier reflects *Respond* at network scale.")
