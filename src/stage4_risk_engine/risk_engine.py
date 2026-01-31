import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath("."))

from src.common.config import DATA_PATH

# ===============================
# LOAD LOGIN HISTORY
# ===============================
def load_history():
    if not os.path.exists(DATA_PATH) or os.path.getsize(DATA_PATH) == 0:
        return pd.DataFrame()
    return pd.read_csv(DATA_PATH)


# ===============================
# CHECK FUNCTIONS
# ===============================
def is_new_ip(df, user, ip):
    if df.empty:
        return True
    return ip not in df[df["user_id"] == user]["ip_address"].unique()


def is_new_device(df, user, device):
    if df.empty:
        return True
    return device not in df[df["user_id"] == user]["device_id"].unique()


def is_unusual_time(df, user, login_hour):
    if df.empty:
        return False

    if "login_hour" in df.columns:
        hours = df[df["user_id"] == user]["login_hour"]
    elif "login_time" in df.columns:
        hours = pd.to_datetime(
            df[df["user_id"] == user]["login_time"]
        ).dt.hour
    else:
        return False

    if hours.empty:
        return False

    return abs(hours.mean() - login_hour) > 6


def too_many_fails(df, user):
    if df.empty or "result" not in df.columns:
        return False

    recent = df[df["user_id"] == user].tail(5)
    return (recent["result"] == "OTP_FAILED").sum() >= 3


def successful_login_count(df, user):
    """
    Đếm số lần login thành công
    (SUCCESS + OTP_SUCCESS đều được tính)
    """
    if df.empty or "result" not in df.columns:
        return 0

    user_rows = df[df["user_id"] == user]

    return user_rows["result"].isin(
        ["SUCCESS", "OTP_SUCCESS"]
    ).sum()


# ===============================
# RISK ENGINE CORE
# ===============================
def calculate_risk(login_event):
    df = load_history()
    user = login_event["user_id"]

    # ===============================
    # 0️⃣ DEMO OVERRIDE (CHỈ CHO USER CHƯA TRUST)
    # ===============================
    success_count = successful_login_count(df, user)
    note = login_event.get("note")

    if success_count < 3:
        if note == "high_risk_attack":
            return 90        # BLOCK
        if note == "unusual_device_or_time":
            return 50        # OTP

    risk = 0

    # ===============================
    # 1️⃣ RISK TỪ HÀNH VI
    # ===============================
    if is_new_ip(df, user, login_event["ip_address"]):
        risk += 40

    if is_new_device(df, user, login_event["device_id"]):
        risk += 40

    if is_unusual_time(df, user, login_event["login_hour"]):
        risk += 20

    if too_many_fails(df, user):
        risk += 30

    # ===============================
    # 2️⃣ TRUST ACCUMULATION
    # ===============================
    if success_count >= 3:
        risk = max(0, risk - 40)

    return risk


def decision_from_risk(risk):
    if risk < 40:
        return "ALLOW"
    elif risk < 70:
        return "OTP"
    return "BLOCK"