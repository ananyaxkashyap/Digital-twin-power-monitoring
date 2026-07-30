import streamlit as st
import random

st.set_page_config(page_title="Digital Twin Dashboard", layout="wide")

st.title("⚡ Digital Twin Power Monitoring System")

# Expected values (digital twin model)
EXPECTED_VOLTAGE = 230
EXPECTED_CURRENT = 0.3

# Simulated input
voltage = random.uniform(210, 250)
current = random.uniform(0.2, 0.6)
power = voltage * current

# Status check
def check_status(v, i):
    if abs(v - EXPECTED_VOLTAGE) > 15:
        return "⚠️ Voltage Issue", "red"
    elif abs(i - EXPECTED_CURRENT) > 0.2:
        return "⚠️ Current Issue", "orange"
    else:
        return "✅ Normal", "green"

status, color = check_status(voltage, current)

# Layout
col1, col2, col3 = st.columns(3)

col1.metric("Voltage (V)", f"{voltage:.2f}")
col2.metric("Current (A)", f"{current:.2f}")
col3.metric("Power (W)", f"{power:.2f}")

st.markdown(f"### Status: :{color}[{status}]")