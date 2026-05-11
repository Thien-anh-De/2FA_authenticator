"""
dashboard_v2.py – 2FA Authenticator V2 Comparison Dashboard
Run with:  streamlit run dashboard_v2.py
"""
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="2FA V2 Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] { background: #1e1b4b; border-right: 1px solid #4c1d95; }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1b4b, #312e81);
        border: 1px solid #6d28d9;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] { color: #a78bfa !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #c4b5fd !important; }

    h1 { color: #a78bfa !important; }
    h2 { color: #818cf8 !important; border-bottom: 1px solid #312e81; padding-bottom: 8px; }
    h3 { color: #c4b5fd !important; }

    .badge-v1 { background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6;
                padding:3px 12px; border-radius:9999px; font-size:0.8em; font-weight:600; }
    .badge-v2 { background:#2e1065; color:#c4b5fd; border:1px solid #7c3aed;
                padding:3px 12px; border-radius:9999px; font-size:0.8em; font-weight:600; }
    .badge-allow  { background:#052e16; color:#86efac; border:1px solid #16a34a;
                    padding:2px 10px; border-radius:9999px; font-size:0.8em; }
    .badge-block  { background:#450a0a; color:#fca5a5; border:1px solid #dc2626;
                    padding:2px 10px; border-radius:9999px; font-size:0.8em; }
    hr { border-color: #312e81 !important; }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADER ───────────────────────────────────────────────────────────────
def load_login_history():
    path = "data/login_history.csv"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=[
            "timestamp", "user_id", "ip_address", "device_id",
            "login_hour", "risk_score", "decision", "result", "engine_version"
        ])
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0)
    # Normalize engine_version: V1 rows may have NaN
    if "engine_version" not in df.columns:
        df["engine_version"] = "V1_Rule"
    df["engine_version"] = df["engine_version"].fillna("V1_Rule")
    return df

def load_sessions():
    path = "data/session_store.csv"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=["user_id", "login_time", "last_activity", "status"])
    df = pd.read_csv(path)
    df["last_activity"] = pd.to_datetime(df["last_activity"])
    return df

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 2FA V2 Monitor")
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    auto_refresh = st.toggle("Auto Refresh (3s)", value=True)
    user_filter = st.text_input("Filter by username")
    st.markdown("---")
    st.markdown("### 📁 Data Files")
    for fname in ["login_history.csv", "session_store.csv", "otp_store.csv", "data_events.csv"]:
        path = f"data/{fname}"
        exists = os.path.exists(path)
        icon = "🟢" if exists else "🔴"
        size = f"{os.path.getsize(path)} B" if exists else "missing"
        st.markdown(f"{icon} `{fname}` — {size}")
    st.markdown("---")
    st.caption(f"Last load: {datetime.now().strftime('%H:%M:%S')}")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df_all    = load_login_history()
df_session = load_sessions()

if user_filter:
    df_all     = df_all[df_all["user_id"].str.contains(user_filter, na=False)]
    df_session = df_session[df_session["user_id"].str.contains(user_filter, na=False)]

df_v1 = df_all[df_all["engine_version"] == "V1_Rule"]
df_v2 = df_all[df_all["engine_version"] == "V2_ML"]

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# 🤖 2FA Adaptive Auth — V2 Comparison Dashboard")
st.markdown("Real-time comparison of **Legacy Rule Engine (V1)** vs **AI Isolation Forest (V2)**.")
st.divider()

# ── TOP METRICS ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("📋 Total Logins", len(df_all))
c2.metric("🔵 V1 Events", len(df_v1))
c3.metric("🟣 V2 Events", len(df_v2))
c4.metric("✅ Total ALLOW", len(df_all[df_all["decision"] == "ALLOW"]))
c5.metric("⛔ Total BLOCK", len(df_all[df_all["decision"] == "BLOCK"]))
avg_v1 = round(df_v1["risk_score"].mean(), 1) if not df_v1.empty else "N/A"
avg_v2 = round(df_v2["risk_score"].mean(), 1) if not df_v2.empty else "N/A"
c6.metric("📊 Avg Risk V1/V2", f"{avg_v1} / {avg_v2}")

st.divider()

# ── COMPARISON CHARTS ─────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown("## 📊 Decision Distribution — V1 (Rule-Based)")
    if not df_v1.empty:
        dec_v1 = df_v1["decision"].value_counts().reset_index()
        dec_v1.columns = ["Decision", "Count"]
        st.bar_chart(dec_v1.set_index("Decision"), color="#3b82f6", use_container_width=True)
    else:
        st.info("No V1 data yet. Run `python system_console.py`.")

with ch2:
    st.markdown("## 📊 Decision Distribution — V2 (AI-Powered)")
    if not df_v2.empty:
        dec_v2 = df_v2["decision"].value_counts().reset_index()
        dec_v2.columns = ["Decision", "Count"]
        st.bar_chart(dec_v2.set_index("Decision"), color="#7c3aed", use_container_width=True)
    else:
        st.info("No V2 data yet. Run `python system_console_v2.py`.")

st.divider()

# ── RISK SCORE COMPARISON ─────────────────────────────────────────────────────
st.markdown("## 📈 Risk Score Over Time (V1 🔵 vs V2 🟣)")
if not df_all.empty:
    risk_pivot = df_all.pivot_table(
        index="timestamp", columns="engine_version",
        values="risk_score", aggfunc="mean"
    )
    st.line_chart(risk_pivot, use_container_width=True)
else:
    st.info("No data yet.")

st.divider()

# ── UNIFIED LOG TABLE ─────────────────────────────────────────────────────────
st.markdown("## 📋 Unified Login Log (V1 + V2)")

if not df_all.empty:
    display = df_all.copy().sort_values("timestamp", ascending=False)
    display["timestamp"] = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    def highlight_engine(row):
        if row.get("engine_version") == "V2_ML":
            return ["background-color: #1e1b4b"] * len(row)
        return ["background-color: #0f1c33"] * len(row)

    styled = display.style.apply(highlight_engine, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.info("No login records found. Start the consoles and try logging in!")

st.divider()

# ── ACTIVE SESSIONS ───────────────────────────────────────────────────────────
st.markdown("## 🟢 Active Sessions")
if not df_session.empty:
    now = datetime.now()
    df_session["idle_sec"] = (now - df_session["last_activity"]).dt.seconds
    df_session["status_display"] = df_session["status"].map({
        "ALLOW": "✅ Active", "OTP_VERIFIED": "🔐 Verified",
        "BLOCK": "⛔ Blocked", "LOGOUT": "🚪 Logged Out",
        "EXPIRED": "⏰ Expired", "OTP_FAILED": "❌ OTP Failed",
    }).fillna(df_session["status"])
    st.dataframe(
        df_session[["user_id", "login_time", "last_activity", "idle_sec", "status_display"]],
        use_container_width=True, hide_index=True
    )
else:
    st.info("No active sessions.")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🤖 2FA Adaptive Authentication V2 Dashboard — Powered by Isolation Forest ML | Built with Streamlit")

# ── AUTO REFRESH ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(3)
    st.rerun()
