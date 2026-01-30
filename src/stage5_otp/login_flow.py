from src.stage4_risk_engine.risk_engine import (
    calculate_risk,
    decision_from_risk
)
from src.stage5_otp.otp_service import (
    generate_otp,
    verify_otp
)
from src.stage6_pipeline.session_store import update_session


def login(user_login: dict) -> bool:
    """
    Core authentication logic.
    user_login must include:
      - user_id
      - ip_address
      - device_id
      - login_hour
    """

    print("\n=== LOGIN ATTEMPT ===")
    print(f"User: {user_login['user_id']}")
    print(f"IP: {user_login['ip_address']}")
    print(f"Device: {user_login['device_id']}")
    print(f"Hour: {user_login['login_hour']}")

    risk = calculate_risk(user_login)
    decision = decision_from_risk(risk)

    print(f"Risk score: {risk}")
    print(f"Decision: {decision}")

    # ===== ALLOW =====
    if decision == "ALLOW":
        update_session(user_login["user_id"], "ALLOW")
        print("✅ Login success (no OTP)")
        return True

    # ===== BLOCK =====
    if decision == "BLOCK":
        update_session(user_login["user_id"], "BLOCK")
        print("⛔ Login blocked")
        return False

    # ===== OTP =====
    if decision == "OTP":
        print("🔐 OTP required")

        generate_otp(user_login["user_id"])

        user_input = input("Enter OTP: ")

        if verify_otp(user_login["user_id"], user_input):
            update_session(user_login["user_id"], "OTP_VERIFIED")
            print("✅ Login success after OTP")
            return True
        else:
            update_session(user_login["user_id"], "OTP_REQUIRED")
            print("❌ Login failed")
            return False
