import csv
import os
from datetime import datetime, timedelta

SESSION_PATH = "data/session_store.csv"
SESSION_TIMEOUT_SECONDS = 60 # 1 phút


def _ensure_file():
    if not os.path.exists(SESSION_PATH) or os.path.getsize(SESSION_PATH) == 0:
        with open(SESSION_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "user_id",
                "login_time",
                "last_activity",
                "status"
            ])


def update_session(user_id, status="ACTIVE"):
    _ensure_file()
    now = datetime.now().isoformat()

    with open(SESSION_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    updated = False
    for row in rows:
        if row["user_id"] == user_id:
            row["last_activity"] = now
            row["status"] = status
            updated = True

    if not updated:
        rows.append({
            "user_id": user_id,
            "login_time": now,
            "last_activity": now,
            "status": status
        })

    with open(SESSION_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["user_id", "login_time", "last_activity", "status"]
        )
        writer.writeheader()
        writer.writerows(rows)


def get_last_session(user_id):
    if not os.path.exists(SESSION_PATH):
        return None

    with open(SESSION_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["user_id"] == user_id:
                return row
    return None


#  HÀM DÙNG CHO PIPELINE
def get_session_status(user_id):
    session = get_last_session(user_id)
    if not session:
        return None
    return session.get("status")


def is_session_expired(user_id) -> bool:
    session = get_last_session(user_id)
    if not session:
        return True

    last_time = datetime.fromisoformat(session["last_activity"])
    return datetime.now() - last_time > timedelta(
        seconds=SESSION_TIMEOUT_SECONDS
    )