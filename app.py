import streamlit as st
import random
import time

# ---- Title ----
st.title("Digital Twin - Power Monitoring System")

# ---- Expected Values (Digital Twin Model) ----
EXPECTED_VOLTAGE = 230
EXPECTED_CURRENT = 0.3

# ---- Simulated Data Function ----
def get_data():
    voltage = random.uniform(210, 240)
    current = random.uniform(0.2, 0.5)
    power = voltage * current
    return voltage, current, power

# ---- Digital Twin Logic ----
def check_status(voltage, current):
    if abs(voltage - EXPECTED_VOLTAGE) > 20:
        return "⚠️ Voltage Issue"
    elif abs(current - EXPECTED_CURRENT) > 0.2:
        return "⚠️ Current Issue"
    else:
        return "✅ Normal"

# ---- Main Loop ----
placeholder = st.empty()

for _ in range(100):
    voltage, current, power = get_data()
    status = check_status(voltage, current)

    with placeholder.container():
        st.subheader("Live Data")
        st.write(f"Voltage: {voltage:.2f} V")
        st.write(f"Current: {current:.2f} A")
        st.write(f"Power: {power:.2f} W")
        st.write(f"Status: {status}")

    time.sleep(1)