from datetime import datetime
import csv
import os

from src.stage4_risk_engine.risk_engine import (
    calculate_risk,
    decision_from_risk
)
from src.stage5_otp.otp_service import (
    generate_otp,
    verify_otp
)
from src.stage6_pipeline.session_store import update_session

LOGIN_HISTORY_PATH = "data/login_history.csv"


def write_login_history(user_login, risk, decision, result):
    file_exists = os.path.exists(LOGIN_HISTORY_PATH)

    with open(LOGIN_HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists or os.path.getsize(LOGIN_HISTORY_PATH) == 0:
            writer.writerow([
                "timestamp",
                "user_id",
                "ip_address",
                "device_id",
                "login_hour",
                "risk_score",
                "decision",
                "result"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            user_login["user_id"],
            user_login["ip_address"],
            user_login["device_id"],
            user_login["login_hour"],
            risk,
            decision,
            result
        ])


def login(user_login: dict) -> bool:
    print("\n=== LOGIN ATTEMPT ===")
    print(f"User   : {user_login['user_id']}")
    print(f"IP     : {user_login['ip_address']}")
    print(f"Device : {user_login['device_id']}")
    print(f"Hour   : {user_login['login_hour']}")

    risk = calculate_risk(user_login)
    decision = decision_from_risk(risk)

    print(f"Risk score: {risk}")
    print(f"Decision  : {decision}")

    # ===============================
    # ALLOW
    # ===============================
    if decision == "ALLOW":
        update_session(user_login["user_id"], "ALLOW")

        write_login_history(
            user_login, risk, decision, "SUCCESS"
        )

        print("✅ Login success (no OTP)")
        return True

    # ===============================
    # BLOCK
    # ===============================
    if decision == "BLOCK":
        update_session(user_login["user_id"], "BLOCK")

        write_login_history(
            user_login, risk, decision, "BLOCKED"
        )

        print("⛔ Login blocked")
        return False

    # ===============================
    # OTP
    # ===============================
    if decision == "OTP":
        print("🔐 OTP required")

        generate_otp(user_login["user_id"])
        user_input = input("Enter OTP: ")

        if verify_otp(user_login["user_id"], user_input):
            update_session(user_login["user_id"], "OTP_VERIFIED")

            write_login_history(
                user_login, risk, decision, "OTP_SUCCESS"
            )

            print("✅ Login success after OTP")
            return True
        else:
            update_session(user_login["user_id"], "OTP_FAILED")

            write_login_history(
                user_login, risk, decision, "OTP_FAILED"
            )

            print("❌ Login failed (wrong or expired OTP)")
            return False