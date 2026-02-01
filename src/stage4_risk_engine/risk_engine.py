import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath("."))

# PATH CONFIG
RAW_HISTORY_PATH = "data/raw/login_history.csv"    
RUNTIME_HISTORY_PATH = "data/login_history.csv"      


# LOAD HISTORY
def load_raw_history():
    if not os.path.exists(RAW_HISTORY_PATH) or os.path.getsize(RAW_HISTORY_PATH) == 0:
        return pd.DataFrame()
    return pd.read_csv(RAW_HISTORY_PATH)


def load_runtime_history():
    if not os.path.exists(RUNTIME_HISTORY_PATH) or os.path.getsize(RUNTIME_HISTORY_PATH) == 0:
        return pd.DataFrame()
    return pd.read_csv(RUNTIME_HISTORY_PATH)


# CHECK FUNCTIONS 
def is_new_ip(df_raw, user, ip):
    if df_raw.empty:
        return True
    return ip not in df_raw[df_raw["user_id"] == user]["ip_address"].unique()


def is_new_device(df_raw, user, device):
    if df_raw.empty:
        return True
    return device not in df_raw[df_raw["user_id"] == user]["device_id"].unique()


def is_unusual_time(df_raw, user, login_hour):
    if df_raw.empty:
        return False

    if "login_hour" in df_raw.columns:
        hours = df_raw[df_raw["user_id"] == user]["login_hour"]
    elif "login_time" in df_raw.columns:
        hours = pd.to_datetime(
            df_raw[df_raw["user_id"] == user]["login_time"]
        ).dt.hour
    else:
        return False

    if hours.empty:
        return False

    return abs(hours.mean() - login_hour) > 6


# CHECK FUNCTIONS
def too_many_fails(df_runtime, user):
    if df_runtime.empty or "result" not in df_runtime.columns:
        return False

    recent = df_runtime[df_runtime["user_id"] == user].tail(5)
    return (recent["result"] == "OTP_FAILED").sum() >= 3


def successful_login_count(df_runtime, user):
    """
    Đếm số lần login thành công (SUCCESS + OTP_SUCCESS)
    """
    if df_runtime.empty or "result" not in df_runtime.columns:
        return 0

    user_rows = df_runtime[df_runtime["user_id"] == user]
    return user_rows["result"].isin(
        ["SUCCESS", "OTP_SUCCESS"]
    ).sum()


# RISK ENGINE CORE 
def calculate_risk(login_event):
    df_raw = load_raw_history()          # baseline behavior
    df_runtime = load_runtime_history()  # trust & otp history

    user = login_event["user_id"]
    note = login_event.get("note")

    success_count = successful_login_count(df_runtime, user)

    # TRUSTED USER (>= 3 SUCCESS)
    if success_count >= 3:
        # chỉ OTP nhẹ nếu spam fail
        if too_many_fails(df_runtime, user):
            return 30
        return 0

    # DEMO OVERRIDE (CHỈ DÙNG KHI DEMO)
    if note == "high_risk_attack":
        return 90          # BLOCK (demo)

    if note == "unusual_device_or_time":
        return 50          # OTP (demo)

    # USER CHƯA TRUST → TÍNH RISK TỪ RAW
    risk = 0

    if is_new_ip(df_raw, user, login_event["ip_address"]):
        risk += 40

    if is_new_device(df_raw, user, login_event["device_id"]):
        risk += 40

    if is_unusual_time(df_raw, user, login_event["login_hour"]):
        risk += 20

    if too_many_fails(df_runtime, user):
        risk += 30

    # USER CHƯA TRUST → KHÔNG BAO GIỜ BLOCK
    risk = min(risk, 50)   # trần OTP

    return risk


def decision_from_risk(risk):
    if risk < 40:
        return "ALLOW"
    elif risk < 70:
        return "OTP"
    return "BLOCK"
