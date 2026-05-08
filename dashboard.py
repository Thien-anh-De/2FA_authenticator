"""
dashboard.py – 2FA Authenticator Live Monitoring Dashboard
Run with:  streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="2FA Admin Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp { background: #0a0e1a; color: #e2e8f0; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #0d1424; border-right: 1px solid #1e3a5f; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f1c33, #162240);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] { color: #67e8f9 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }

    /* DataFrames */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .dataframe thead tr th {
        background: #162240 !important;
        color: #67e8f9 !important;
    }

    /* Section headers */
    h1 { color: #67e8f9 !important; }
    h2 { color: #93c5fd !important; border-bottom: 1px solid #1e3a5f; padding-bottom: 8px; }
    h3 { color: #a5b4fc !important; }

    /* Badge pills */
    .badge-allow  { background:#052e16; color:#86efac; border:1px solid #16a34a;
                    padding:2px 10px; border-radius:9999px; font-size:0.8em; font-weight:600; }
    .badge-otp    { background:#422006; color:#fcd34d; border:1px solid #d97706;
                    padding:2px 10px; border-radius:9999px; font-size:0.8em; font-weight:600; }
    .badge-block  { background:#450a0a; color:#fca5a5; border:1px solid #dc2626;
                    padding:2px 10px; border-radius:9999px; font-size:0.8em; font-weight:600; }

    /* Card box */
    .info-card {
        background: linear-gradient(135deg, #0f1c33, #162240);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }

    /* Divider */
    hr { border-color: #1e3a5f !important; }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADERS ─────────────────────────────────────────────────────────────

def load_login_history():
    path = "data/login_history.csv"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=[
            "timestamp", "user_id", "ip_address", "device_id",
            "login_hour", "risk_score", "decision", "result"
        ])
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce")
    return df


def load_sessions():
    path = "data/session_store.csv"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=["user_id", "login_time", "last_activity", "status"])
    df = pd.read_csv(path)
    df["last_activity"] = pd.to_datetime(df["last_activity"])
    return df


def load_data_events():
    path = "data/data_events.csv"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=["user_id", "event", "timestamp"])
    return pd.read_csv(path)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def decision_badge(d):
    if d == "ALLOW":
        return '<span class="badge-allow">✅ ALLOW</span>'
    elif d == "OTP":
        return '<span class="badge-otp">🔐 OTP</span>'
    elif d == "BLOCK":
        return '<span class="badge-block">⛔ BLOCK</span>'
    return d


def result_icon(r):
    icons = {
        "SUCCESS":     "✅ SUCCESS",
        "OTP_SUCCESS": "🔐 OTP OK",
        "BLOCKED":     "⛔ BLOCKED",
        "OTP_FAILED":  "❌ OTP FAIL",
    }
    return icons.get(r, r)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔐 2FA Auth Monitor")
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    auto_refresh = st.toggle("Auto Refresh (2s)", value=True)
    user_filter  = st.text_input("Filter by username", placeholder="e.g. nguyen.hoang...")
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
df_login   = load_login_history()
df_session = load_sessions()
df_events  = load_data_events()

if user_filter:
    df_login   = df_login[df_login["user_id"].str.contains(user_filter, na=False)]
    df_session = df_session[df_session["user_id"].str.contains(user_filter, na=False)]

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# 🔐 2FA Authentication — Live Dashboard")
st.markdown("Real-time monitoring of all authentication events, risk decisions, and active sessions.")
st.divider()

# ── METRIC CARDS ──────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total        = len(df_login)
allow_count  = len(df_login[df_login["decision"] == "ALLOW"])  if total else 0
otp_count    = len(df_login[df_login["decision"] == "OTP"])    if total else 0
block_count  = len(df_login[df_login["decision"] == "BLOCK"])  if total else 0
avg_risk     = round(df_login["risk_score"].mean(), 1)          if total else 0

col1.metric("📋 Total Events",  total)
col2.metric("✅ Allowed",        allow_count)
col3.metric("🔐 OTP Required",  otp_count)
col4.metric("⛔ Blocked",        block_count)
col5.metric("📊 Avg Risk Score", f"{avg_risk}/100")

st.divider()

# ── CHARTS ────────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("## 📊 Decision Distribution")
    if total:
        decision_counts = df_login["decision"].value_counts().reset_index()
        decision_counts.columns = ["Decision", "Count"]
        st.bar_chart(decision_counts.set_index("Decision"), color="#67e8f9", use_container_width=True)
    else:
        st.info("No data yet.")

with chart_col2:
    st.markdown("## 📈 Risk Score Over Time")
    if total:
        chart_data = df_login[["timestamp", "risk_score"]].set_index("timestamp")
        st.line_chart(chart_data, color="#a78bfa", use_container_width=True)
    else:
        st.info("No data yet.")

st.divider()

# ── LOGIN HISTORY TABLE ───────────────────────────────────────────────────────
st.markdown("## 📋 Login History")

if total:
    display_df = df_login.copy()
    display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Color-coded risk score column
    def highlight_risk(row):
        score = row["risk_score"]
        if score >= 70:
            return ["background-color: #450a0a"] * len(row)
        elif score >= 40:
            return ["background-color: #422006"] * len(row)
        else:
            return ["background-color: #052e16"] * len(row)

    styled = display_df.style.apply(highlight_risk, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.info("No login records found. Start the console and try logging in!")

st.divider()

# ── ACTIVE SESSIONS ───────────────────────────────────────────────────────────
st.markdown("## 🟢 Active Sessions")

if not df_session.empty:
    now = datetime.now()
    df_session["last_activity"] = pd.to_datetime(df_session["last_activity"])
    df_session["idle_sec"] = (now - df_session["last_activity"]).dt.seconds
    df_session["status_display"] = df_session["status"].map({
        "ALLOW":        "✅ Active",
        "OTP_VERIFIED": "🔐 Verified",
        "BLOCK":        "⛔ Blocked",
        "LOGOUT":       "🚪 Logged Out",
        "EXPIRED":      "⏰ Expired",
        "OTP_FAILED":   "❌ OTP Failed",
    }).fillna(df_session["status"])

    cols_to_show = ["user_id", "login_time", "last_activity", "idle_sec", "status_display"]
    st.dataframe(df_session[cols_to_show], use_container_width=True, hide_index=True)
else:
    st.info("No active sessions.")

st.divider()

# ── BEHAVIORAL PROFILES ───────────────────────────────────────────────────────
st.markdown("## 👤 User Behavior Profiles")

if total:
    users = df_login["user_id"].unique()
    tabs = st.tabs([f"  {u}  " for u in users])

    for tab, user in zip(tabs, users):
        with tab:
            user_df = df_login[df_login["user_id"] == user]
            pcol1, pcol2, pcol3 = st.columns(3)
            pcol1.metric("Total Logins",  len(user_df))
            pcol2.metric("Avg Risk",      f"{round(user_df['risk_score'].mean(), 1)}/100")
            pcol3.metric("Success Rate",  f"{round(len(user_df[user_df['result'].isin(['SUCCESS','OTP_SUCCESS'])]) / len(user_df) * 100, 0):.0f}%")

            sub1, sub2 = st.columns(2)
            with sub1:
                st.markdown("**Known IPs**")
                for ip in user_df["ip_address"].unique():
                    st.code(ip)
            with sub2:
                st.markdown("**Known Devices**")
                for dev in user_df["device_id"].unique():
                    st.code(dev)
else:
    st.info("No user data yet.")

st.divider()

# ── DATA EVENTS ───────────────────────────────────────────────────────────────
st.markdown("## 📦 Data Events")

if not df_events.empty:
    st.dataframe(df_events, use_container_width=True, hide_index=True)
else:
    st.info("No data events recorded yet.")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🔐 2FA Adaptive Authentication System — Admin Dashboard | Built with Streamlit")

# ── AUTO REFRESH (must be LAST, after all rendering) ─────────────────────────
if auto_refresh:
    time.sleep(2)
    st.rerun()
