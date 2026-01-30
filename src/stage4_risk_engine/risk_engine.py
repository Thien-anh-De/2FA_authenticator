# src/stage4_risk_engine/risk_engine.py

import sys
import os
import pandas as pd
from datetime import datetime

# FIX PATH
sys.path.append(os.path.abspath("."))

from src.common.config import DATA_PATH

# -------------------------
# LOAD LOGIN HISTORY
# -------------------------
def load_history():
    return pd.read_csv(DATA_PATH)

# -------------------------
# CHECK FUNCTIONS
# -------------------------
def is_new_ip(df, user, ip):
    return ip not in df[df["user_id"] == user]["ip_address"].unique()

def is_new_device(df, user, device):
    return device not in df[df["user_id"] == user]["device_id"].unique()

def is_unusual_time(df, user, login_hour):
    hours = pd.to_datetime(
        df[df["user_id"] == user]["login_time"]
    ).dt.hour

    if hours.empty:
        return False

    return abs(hours.mean() - login_hour) > 6

def too_many_fails(df, user):
    recent = df[df["user_id"] == user].tail(5)
    return (recent["login_result"] == False).sum() >= 3

# -------------------------
# RISK ENGINE CORE
# -------------------------
def calculate_risk(login_event):
    df = load_history()
    user = login_event["user_id"]

    risk = 0

    if is_new_ip(df, user, login_event["ip_address"]):
        risk += 40

    if is_new_device(df, user, login_event["device_id"]):
        risk += 40

    if is_unusual_time(df, user, login_event["login_hour"]):
        risk += 20

    if too_many_fails(df, user):
        risk += 30

    return risk

def decision_from_risk(risk):
    if risk < 40:
        return "ALLOW"
    elif risk < 70:
        return "OTP"
    return "BLOCK"

# -------------------------
# TEST LOGIN
# -------------------------
if __name__ == "__main__":
    new_login = {
        "user_id": "user_1",
        "ip_address": "10.0.0.99",
        "device_id": "device_X9",
        "login_hour": datetime.now().hour
    }

    risk = calculate_risk(new_login)
    decision = decision_from_risk(risk)

    print("🔐 Login attempt")
    print("Risk score:", risk)
    print("Decision:", decision)
