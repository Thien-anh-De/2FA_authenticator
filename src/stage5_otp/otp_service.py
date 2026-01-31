import os
import random
import pandas as pd
from datetime import datetime, timedelta

OTP_FILE = "data/otp_store.csv"
OTP_EXPIRE_SECONDS = 60


def _ensure_otp_file():
    if not os.path.exists(OTP_FILE) or os.path.getsize(OTP_FILE) == 0:
        with open(OTP_FILE, "w", encoding="utf-8") as f:
            f.write("user_id,otp,created_at\n")


def generate_otp(user_id):
    _ensure_otp_file()

    otp = str(random.randint(100000, 999999))
    now = datetime.now().isoformat()

    df = pd.read_csv(OTP_FILE, dtype=str)
    df = df[df["user_id"] != str(user_id)]

    df.loc[len(df)] = [str(user_id), otp, now]
    df.to_csv(OTP_FILE, index=False)

    print(f"📩 OTP for {user_id}: {otp}")
    print(f"⏱️ OTP valid for {OTP_EXPIRE_SECONDS} seconds")

    return otp


def verify_otp(user_id, user_input):
    _ensure_otp_file()

    user_input = str(user_input).strip()
    if not user_input.isdigit():
        return False

    df = pd.read_csv(OTP_FILE, dtype=str)
    row = df[df["user_id"] == str(user_id)]
    if row.empty:
        return False

    stored_otp = row.iloc[0]["otp"]
    created_at = datetime.fromisoformat(row.iloc[0]["created_at"])

    if datetime.now() - created_at > timedelta(seconds=OTP_EXPIRE_SECONDS):
        print("⏰ OTP expired")
        return False

    return user_input == stored_otp