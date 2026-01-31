from src.stage5_otp.login_flow import login
from src.stage6_pipeline.data_pipeline import send_event
from src.common.context_collector import collect_context
from src.stage6_pipeline.session_store import (
    update_session,
    is_session_expired
)

from src.stage4_risk_engine.risk_engine import (
    load_history,
    successful_login_count
)

DEMO_MODE = True


def choose_demo_scenario():
    print("\nChoose demo scenario:")
    print("1. Normal login (ALLOW)")
    print("2. Suspicious login (OTP)")
    print("3. Attack login (BLOCK)")

    choice = input("Scenario: ")
    return {
        "1": "normal",
        "2": "suspicious",
        "3": "attack"
    }.get(choice, "normal")


def login_ui():
    print("\n==============================")
    print("🔐 AUTHENTICATION SYSTEM")
    print("==============================")

    user_id = input("Username: ")

    # ==================================================
    # 1️⃣ CHECK USER TRƯỚC (KHÔNG DEMO)
    # ==================================================
    base_context = collect_context(
        user_id=user_id,
        demo_mode=False
    )

    # ==================================================
    # USER MỚI → AUTO OTP
    # ==================================================
    if base_context.get("note") == "new_user":
        print("\n[System detected]")
        print("User status : NEW USER")
        print("Action      : OTP required")

        return {
            "user_id": user_id,
            "ip_address": base_context["ip_address"],
            "device_id": base_context["device_id"],
            "login_hour": base_context["login_hour"],
            "note": "unusual_device_or_time"
        }

    # ==================================================
    # 2️⃣ USER CŨ → KIỂM TRA TRUST
    # ==================================================
    df = load_history()
    success_count = successful_login_count(df, user_id)

    # ==================================================
    # USER ĐÃ TRUST → KHÔNG DEMO, KHÔNG NOTE
    # ==================================================
    if success_count >= 3:
        context = collect_context(
            user_id=user_id,
            demo_mode=False
        )

        print("\n[System detected]")
        print("User status : TRUSTED USER")
        print(f"IP      : {context['ip_address']}")
        print(f"Device  : {context['device_id']}")
        print(f"Hour    : {context['login_hour']}")
        print("Note    : (ignored – trusted user)")

        return {
            "user_id": user_id,
            "ip_address": context["ip_address"],
            "device_id": context["device_id"],
            "login_hour": context["login_hour"]
        }

    # ==================================================
    # 3️⃣ USER CHƯA TRUST → CHO CHỌN DEMO SCENARIO
    # ==================================================
    scenario = choose_demo_scenario()

    context = collect_context(
        user_id=user_id,
        scenario=scenario,
        demo_mode=True
    )

    print("\n[System detected]")
    print(f"User status : UNTRUSTED USER ({success_count}/3)")
    print(f"IP      : {context['ip_address']}")
    print(f"Device  : {context['device_id']}")
    print(f"Hour    : {context['login_hour']}")
    print(f"Note    : {context.get('note')}")

    return {
        "user_id": user_id,
        "ip_address": context["ip_address"],
        "device_id": context["device_id"],
        "login_hour": context["login_hour"],
        "note": context.get("note")
    }


def main():
    current_user = None

    while True:
        # ===============================
        # AUTO SESSION TIMEOUT
        # ===============================
        if current_user and is_session_expired(current_user):
            print("\n⛔ SESSION TIMEOUT")
            print("👉 Your session has expired. Please login again.\n")
            update_session(current_user, "EXPIRED")
            current_user = None

        print("\n========== MENU ==========")

        if current_user is None:
            print("1. Login")
        else:
            print("1. Logout")

        print("2. Send data event")
        print("0. Exit")

        choice = input("Choose: ")

        # ===============================
        # LOGIN / LOGOUT
        # ===============================
        if choice == "1":
            if current_user is None:
                login_request = login_ui()
                success = login(login_request)

                if success:
                    current_user = login_request["user_id"]
                    print(f"\n✅ Logged in as {current_user}\n")
            else:
                update_session(current_user, "LOGOUT")
                print(f"\n👋 User {current_user} logged out\n")
                current_user = None

        # ===============================
        # SEND EVENT
        # ===============================
        elif choice == "2":
            if not current_user:
                print("⚠ Please login first")
                continue

            event = input("Event name: ")
            success = send_event(current_user, event)

            if success is False:
                current_user = None

        elif choice == "0":
            print("Bye 👋")
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()