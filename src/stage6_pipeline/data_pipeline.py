#xử lý dữ liệu
import pandas as pd
from datetime import datetime
from src.stage6_pipeline.session_store import get_session_status

DATA_FILE = "data/data_events.csv"


def send_event(user_id, event):
    status = get_session_status(user_id)

    print(f"[PIPELINE] User={user_id} | Status={status}")

    if status not in ["ALLOW", "OTP_VERIFIED"]:
        print("⛔ Data blocked by security policy")
        return False

    df = pd.read_csv(DATA_FILE)

    df = pd.concat([
        df,
        pd.DataFrame([{
            "user_id": user_id,
            "event": event,
            "timestamp": datetime.now().isoformat()
        }])
    ], ignore_index=True)

    df.to_csv(DATA_FILE, index=False)
    print("✅ Data accepted")
    return True
