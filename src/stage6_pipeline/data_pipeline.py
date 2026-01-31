import csv
import os
from datetime import datetime

from src.stage6_pipeline.session_store import (
    is_session_expired,
    get_session_status,
    update_session
)

DATA_EVENTS_PATH = "data/data_events.csv"


def send_event(user_id, event_name):
    """
    Ghi event sau khi login
    """

    # ⛔ Session timeout
    if is_session_expired(user_id):
        print("\n⛔ SESSION TIMEOUT")
        print("👉 Your session has expired. Please login again.\n")
        update_session(user_id, "EXPIRED")
        return False

    status = get_session_status(user_id)
    if status not in ["ALLOW", "OTP_VERIFIED"]:
        print("⛔ Invalid session state.")
        return False

    file_exists = os.path.exists(DATA_EVENTS_PATH)

    with open(DATA_EVENTS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists or os.path.getsize(DATA_EVENTS_PATH) == 0:
            writer.writerow(["user_id", "event", "timestamp"])

        writer.writerow([
            user_id,
            event_name,
            datetime.now().isoformat()
        ])

    print("📦 Event recorded successfully")
    return True