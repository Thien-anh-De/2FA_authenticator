# system_console.py

from datetime import datetime

from src.stage5_otp.login_flow import login
from src.stage6_pipeline.data_pipeline import send_event
from src.common.context_collector import collect_context

# ===============================
# DEMO CONFIG
# ===============================
DEMO_MODE = True   # ← khi nộp có thể để True


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

    if DEMO_MODE:
        scenario = choose_demo_scenario()
        context = collect_context(
            user_id=user_id,
            scenario=scenario,
            demo_mode=True
        )
    else:
        context = collect_context(
            user_id=user_id,
            demo_mode=False
        )

    print("\n[System detected]")
    print(f"IP      : {context['ip_address']}")
    print(f"Device  : {context['device_id']}")
    print(f"Hour    : {context['login_hour']}")
    print(f"Note    : {context.get('note')}")

    return {
        "user_id": user_id,
        "ip_address": context["ip_address"],
        "device_id": context["device_id"],
        "login_hour": context["login_hour"]
    }


def main():
    current_user = None

    while True:
        print("\n========== MENU ==========")
        print("1. Login")
        print("2. Send data event")
        print("0. Exit")

        choice = input("Choose: ")

        if choice == "1":
            login_request = login_ui()
            success = login(login_request)

            if success:
                current_user = login_request["user_id"]

        elif choice == "2":
            if not current_user:
                print("⚠ Please login first")
                continue

            event = input("Event name: ")
            send_event(current_user, event)

        elif choice == "0":
            print("Bye 👋")
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()