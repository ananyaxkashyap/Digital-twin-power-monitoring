import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import urllib.request
import os
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Smart Room Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f7f5ef;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #18251d;
}

.metric-card {
    background: #ffffff;
    padding: 18px;
    border-radius: 15px;
    border: 1px solid #e4e1d8;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.04);
}

.status-normal {
    background: #dff4e4;
    color: #17652d;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 600;
}

.status-warning {
    background: #fff0c7;
    color: #8a5a00;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 600;
}

.status-danger {
    background: #ffe0e0;
    color: #a32929;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 600;
}

.info-box {
    background: #edf5ef;
    padding: 15px;
    border-radius: 12px;
    border-left: 5px solid #4d805b;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA DOWNLOAD
# ============================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

ZIP_PATH = DATA_DIR / "uci_power.zip"
TXT_PATH = DATA_DIR / "household_power_consumption.txt"

UCI_URL = (
    "https://archive.ics.uci.edu/static/public/235/"
    "individual+household+electric+power+consumption.zip"
)


@st.cache_data(show_spinner=True)
def download_uci_dataset():

    if not TXT_PATH.exists():

        st.info(
            "Downloading the UCI Individual Household Electric Power "
            "Consumption dataset. This is a large file and may take a while."
        )

        urllib.request.urlretrieve(
            UCI_URL,
            ZIP_PATH
        )

        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(DATA_DIR)

    return str(TXT_PATH)


# ============================================================
# LOAD ONLY NOVEMBER 2010
# ============================================================

@st.cache_data
def load_latest_month():

    file_path = download_uci_dataset()

    chunks = []

    for chunk in pd.read_csv(
        file_path,
        sep=";",
        na_values="?",
        low_memory=False,
        chunksize=100000
    ):

        chunk["Date"] = pd.to_datetime(
            chunk["Date"],
            dayfirst=True,
            errors="coerce"
        )

        november = chunk[
            (chunk["Date"].dt.year == 2010) &
            (chunk["Date"].dt.month == 11)
        ]

        if not november.empty:
            chunks.append(november)

    df = pd.concat(chunks, ignore_index=True)

    # Combine date and time
    df["Datetime"] = pd.to_datetime(
        df["Date"].dt.strftime("%Y-%m-%d")
        + " "
        + df["Time"].astype(str),
        errors="coerce"
    )

    # Rename columns
    df = df.rename(columns={
        "Global_active_power": "Power_kW",
        "Global_reactive_power": "Reactive_kW",
        "Voltage": "Voltage_V",
        "Global_intensity": "Current_A"
    })

    # Numeric conversion
    numeric_cols = [
        "Power_kW",
        "Reactive_kW",
        "Voltage_V",
        "Current_A",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "Datetime",
            "Power_kW",
            "Voltage_V",
            "Current_A"
        ]
    )

    # Power in Watts
    df["Power_W"] = df["Power_kW"] * 1000

    # Energy consumed during each 1-minute interval
    df["Energy_Wh"] = df["Power_kW"] * (1 / 60) * 1000

    # Cumulative energy
    df["Cumulative_Energy_kWh"] = (
        df["Energy_Wh"].cumsum() / 1000
    )

    return df


df = load_latest_month()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚡ Smart Room")

st.sidebar.markdown(
    """
    **Digital Twin Energy Management**

    Reference dataset:
    **UCI Individual Household Electric Power Consumption**

    Period:
    **November 2010**
    """
)

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "📊 Behaviour Analysis",
        "🧠 Digital Twin",
        "🎛️ Control & Alerts",
        "📱 Remote Monitoring"
    ]
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Software validation using real-world reference data. "
    "Live ESP32 sensor data will replace this dataset during hardware integration."
)

# ============================================================
# COMMON VALUES
# ============================================================

latest = df.iloc[-1]

current_power = latest["Power_W"]
current_voltage = latest["Voltage_V"]
current_current = latest["Current_A"]

average_power = df["Power_W"].mean()
peak_power = df["Power_W"].max()

total_energy = df["Energy_Wh"].sum() / 1000

# Expected behaviour
expected_mean = df["Power_W"].rolling(
    window=60,
    min_periods=1
).mean()

expected_power = expected_mean.iloc[-1]

deviation = (
    abs(current_power - expected_power)
    / max(expected_power, 1)
) * 100

# ============================================================
# PAGE 1 — HOME
# ============================================================

if page == "🏠 Home":

    st.title("⚡ Smart Room Energy Dashboard")

    st.markdown(
        """
        ### Welcome 👋

        Monitor room energy consumption, appliance behaviour and
        Digital Twin status from one place.
        """
    )

    st.markdown(
        """
        <div class="info-box">
        <b>Reference Mode:</b> The current dashboard is using real-world
        electrical measurements from the UCI Individual Household Electric
        Power Consumption dataset for software validation.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # -------------------------
    # KPI CARDS
    # -------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Voltage",
        f"{current_voltage:.1f} V"
    )

    c2.metric(
        "Current",
        f"{current_current:.2f} A"
    )

    c3.metric(
        "Current Power",
        f"{current_power:.1f} W"
    )

    c4.metric(
        "Energy Consumed",
        f"{total_energy:.2f} kWh"
    )

    st.write("")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Average Power",
        f"{average_power:.1f} W"
    )

    c2.metric(
        "Peak Power",
        f"{peak_power:.1f} W"
    )

    c3.metric(
        "Data Period",
        "Nov 2010"
    )

    st.subheader("📈 Power Consumption")

    chart_df = df[
        ["Datetime", "Power_W"]
    ].set_index("Datetime")

    st.line_chart(
        chart_df,
        y="Power_W",
        height=350
    )

    st.subheader("🔋 Cumulative Energy Consumption")

    energy_chart = df[
        ["Datetime", "Cumulative_Energy_kWh"]
    ].set_index("Datetime")

    st.line_chart(
        energy_chart,
        y="Cumulative_Energy_kWh",
        height=300
    )

    st.subheader("🌡️ Room Conditions")

    c1, c2, c3 = st.columns(3)

    c1.info("🌡️ Temperature\n\nHardware integration pending")

    c2.info("👤 Occupancy\n\nPIR sensor integration pending")

    c3.success("⚡ Electrical Data\n\nAvailable from reference dataset")

# ============================================================
# PAGE 2 — BEHAVIOUR ANALYSIS
# ============================================================

elif page == "📊 Behaviour Analysis":

    st.title("📊 Appliance Behaviour Analysis")

    st.write(
        "The system compares observed power behaviour with an expected "
        "operating pattern to identify deviations."
    )

    # Resample to hourly data for clearer graph
    hourly = (
        df.set_index("Datetime")["Power_W"]
        .resample("1h")
        .mean()
        .dropna()
    )

    expected = (
        hourly
        .rolling(
            window=6,
            min_periods=1
        )
        .mean()
    )

    behaviour = pd.DataFrame({
        "Actual Power (W)": hourly,
        "Expected Power (W)": expected
    })

    st.subheader("Actual vs Expected Power Behaviour")

    st.line_chart(
        behaviour,
        height=400
    )

    latest_actual = hourly.iloc[-1]
    latest_expected = expected.iloc[-1]

    deviation = (
        abs(latest_actual - latest_expected)
        / max(latest_expected, 1)
    ) * 100

    st.write("")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Actual Power",
        f"{latest_actual:.1f} W"
    )

    c2.metric(
        "Expected Power",
        f"{latest_expected:.1f} W"
    )

    c3.metric(
        "Deviation",
        f"{deviation:.1f}%"
    )

    if deviation < 15:

        st.markdown(
            '<div class="status-normal">'
            '🟢 Behaviour Status: NORMAL'
            '</div>',
            unsafe_allow_html=True
        )

    elif deviation < 30:

        st.markdown(
            '<div class="status-warning">'
            '🟠 Behaviour Status: DEVIATION DETECTED'
            '</div>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<div class="status-danger">'
            '🔴 Behaviour Status: HIGH DEVIATION'
            '</div>',
            unsafe_allow_html=True
        )

    st.subheader("🔎 Behaviour Statistics")

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            f"**Average Power:** {hourly.mean():.2f} W"
        )

        st.write(
            f"**Maximum Power:** {hourly.max():.2f} W"
        )

    with c2:

        st.write(
            f"**Minimum Power:** {hourly.min():.2f} W"
        )

        st.write(
            f"**Standard Deviation:** {hourly.std():.2f} W"
        )

# ============================================================
# PAGE 3 — DIGITAL TWIN
# ============================================================

elif page == "🧠 Digital Twin":

    st.title("🧠 Digital Twin")

    st.write(
        "Virtual representation of the monitored room and its connected "
        "appliances."
    )

    # -------------------------
    # ROOM REPRESENTATION
    # -------------------------

    st.subheader("🏠 Virtual Room")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown("### 🌀 Appliance")

        st.success("Electrical Load Detected")

        st.metric(
            "Power",
            f"{current_power:.1f} W"
        )

    with c2:

        st.markdown("### 👤 Occupancy")

        st.info(
            "PIR Sensor\n\n"
            "Hardware integration pending"
        )

    with c3:

        st.markdown("### 🌡️ Temperature")

        st.info(
            "DS18B20\n\n"
            "Hardware integration pending"
        )

    st.write("")

    st.subheader("Twin Synchronisation")

    twin_status = "SYNCHRONISED"

    st.markdown(
        f"""
        <div class="status-normal">
        🟢 Digital Twin Status: {twin_status}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Voltage",
        f"{current_voltage:.1f} V"
    )

    c2.metric(
        "Current",
        f"{current_current:.2f} A"
    )

    c3.metric(
        "Power",
        f"{current_power:.1f} W"
    )

    c4.metric(
        "Energy",
        f"{total_energy:.2f} kWh"
    )

    st.subheader("Physical → Virtual Representation")

    st.markdown(
        """
        **Physical Room**

        ↓

        **ACS712 + ZMPT101B + DS18B20 + PIR**

        ↓

        **ESP32 Data Acquisition**

        ↓

        **Digital Twin**

        ↓

        **Expected vs Actual Behaviour**

        ↓

        **Monitoring / Alerts / Control**
        """
    )

# ============================================================
# PAGE 4 — CONTROL & ALERTS
# ============================================================

elif page == "🎛️ Control & Alerts":

    st.title("🎛️ Control & Alerts")

    st.write(
        "Smart-room style interface for appliance status, alerts and control."
    )

    # -------------------------
    # APPLIANCE CONTROL
    # -------------------------

    st.subheader("Appliance Control")

    appliance_state = st.toggle(
        "🌀 Appliance Power",
        value=True
    )

    if appliance_state:

        st.success("🟢 Appliance is ON")

    else:

        st.warning("⚪ Appliance is OFF")

    st.write("")

    st.subheader("🚨 System Alerts")

    # Generate demo logic from actual reference values
    if current_power > average_power * 1.5:

        st.error(
            f"🔴 High Power Consumption Detected — "
            f"{current_power:.1f} W"
        )

    elif deviation > 30:

        st.warning(
            f"🟠 Behaviour deviation detected — "
            f"{deviation:.1f}%"
        )

    else:

        st.success(
            "🟢 System operating within expected range."
        )

    st.subheader("Alert Categories")

    c1, c2, c3 = st.columns(3)

    c1.info(
        "⚡ High Power\n\n"
        "Triggered when power exceeds expected limits."
    )

    c2.warning(
        "📈 Behaviour Deviation\n\n"
        "Triggered when actual behaviour differs from expected behaviour."
    )

    c3.error(
        "🔴 Potential Fault\n\n"
        "Reserved for abnormal sensor behaviour during hardware integration."
    )

# ============================================================
# PAGE 5 — REMOTE MONITORING
# ============================================================

elif page == "📱 Remote Monitoring":

    st.title("📱 Remote Monitoring")

    st.write(
        "The dashboard is designed as a browser-based interface so that "
        "the same system can be accessed from a laptop, tablet or mobile."
    )

    c1, c2, c3 = st.columns(3)

    c1.success(
        "💻 Laptop\n\n"
        "Full dashboard access"
    )

    c2.success(
        "📱 Mobile\n\n"
        "Responsive browser access"
    )

    c3.success(
        "🌐 Web Interface\n\n"
        "Remote monitoring"
    )

    st.subheader("Current System Status")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Power",
        f"{current_power:.1f} W"
    )

    c2.metric(
        "Voltage",
        f"{current_voltage:.1f} V"
    )

    c3.metric(
        "Current",
        f"{current_current:.2f} A"
    )

    c4.metric(
        "Energy",
        f"{total_energy:.2f} kWh"
    )

    st.subheader("Remote Monitoring Architecture")

    st.markdown(
        """
        **Room Appliance**

        ↓

        **ACS712 + ZMPT101B + PIR + DS18B20**

        ↓

        **ESP32 + Wi-Fi**

        ↓

        **Data Processing / Digital Twin**

        ↓

        **Web Dashboard**

        ↙                 ↘

        **Laptop**        **Mobile**
        """
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Reference data: Hebrail, G. & Berard, A. (2006), "
    "Individual Household Electric Power Consumption, "
    "UCI Machine Learning Repository, DOI: 10.24432/C58K54."
)