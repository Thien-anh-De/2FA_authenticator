import uuid
import random
from datetime import datetime, timedelta
import pandas as pd

OTP_FILE = "data/otp_store.csv"


def generate_otp(user_id, ttl_seconds=120):
    otp_code = random.randint(100000, 999999)
    otp_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

    df = pd.read_csv(OTP_FILE)

    df = pd.concat([
        df,
        pd.DataFrame([{
            "otp_id": otp_id,
            "user_id": user_id,
            "otp_code": otp_code,
            "expires_at": expires_at.isoformat(),
            "verified": False
        }])
    ], ignore_index=True)

    df.to_csv(OTP_FILE, index=False)

    print(f"[OTP GENERATED] User={user_id} | OTP={otp_code} | Expires={expires_at}")
    return otp_id, otp_code


def verify_otp(user_id, otp_code):
    df = pd.read_csv(OTP_FILE)
    now = datetime.now()

    for idx, row in df.iterrows():
        if (
            row["user_id"] == user_id
            and int(row["otp_code"]) == int(otp_code)
            and not row["verified"]
            and datetime.fromisoformat(row["expires_at"]) > now
        ):
            df.at[idx, "verified"] = True
            df.to_csv(OTP_FILE, index=False)
            print("[OTP VERIFIED] Success")
            return True

    print("[OTP FAILED] Invalid / Expired")
    return False
