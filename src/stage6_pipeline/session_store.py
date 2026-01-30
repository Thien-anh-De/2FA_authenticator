#lưu trạng thái user
import pandas as pd
from datetime import datetime

SESSION_FILE = "data/session_store.csv"


def update_session(user_id, status):
    df = pd.read_csv(SESSION_FILE)

    df = df[df["user_id"] != user_id]

    df = pd.concat([
        df,
        pd.DataFrame([{
            "user_id": user_id,
            "status": status,
            "last_update": datetime.now().isoformat()
        }])
    ], ignore_index=True)

    df.to_csv(SESSION_FILE, index=False)


def get_session_status(user_id):
    df = pd.read_csv(SESSION_FILE)
    row = df[df["user_id"] == user_id]

    if row.empty:
        return None

    return row.iloc[0]["status"]
