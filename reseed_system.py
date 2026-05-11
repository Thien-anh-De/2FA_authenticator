"""
reseed_system.py
────────────────
Script dọn dẹp và tái tạo toàn bộ dữ liệu baseline cho hệ thống.

Mục đích:
  - Xóa dữ liệu cũ bị nhiễu (IP lạ / device lạ trong baseline)
  - Tạo mới 150 bản ghi sạch: mỗi user CHỈ dùng đúng 1 IP và 1 Device quen thuộc
  - Đảm bảo AI học được "vùng an toàn" rõ nét trước khi demo

Chạy một lần duy nhất trước khi demo:
  python reseed_system.py
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ── Đường dẫn file ──────────────────────────────────────────────────────────
RAW_HISTORY_PATH   = "data/raw/login_history.csv"
RUNTIME_HISTORY_PATH = "data/login_history.csv"
OTP_STORE_PATH     = "data/otp_store.csv"
SESSION_STORE_PATH = "data/session_store.csv"
DATA_EVENTS_PATH   = "data/data_events.csv"

# ── Baseline Profile (Sạch & Ổn định) ───────────────────────────────────────
# Mỗi user chỉ có DUY NHẤT 1 IP + 1 Device để AI học được "vùng an toàn" rõ nét.
# Điều này phản ánh đúng thực tế: người dùng thông thường dùng thiết bị quen thuộc.
CLEAN_PROFILES = {
    "nguyen.hoang.thienanh": {
        "ip":           "113.190.45.24",
        "device":       "Edge_Windows_10",
        "active_hours": range(8, 21),   # 8h - 21h
    },
    "cao.viet.bac": {
        "ip":           "27.72.88.101",
        "device":       "Samsung_Internet",
        "active_hours": range(9, 22),   # 9h - 22h
    },
    "nguyen.viet.anh": {
        "ip":           "14.162.12.88",
        "device":       "Firefox_Linux",
        "active_hours": range(7, 20),   # 7h - 20h
    },
}

FIELDS = [
    "login_id", "user_id", "ip_address", "device_id",
    "login_time", "login_result", "risk_score", "decision"
]


def _make_login_time(active_hours: range) -> str:
    """Tạo timestamp ngẫu nhiên trong khung giờ an toàn của user."""
    hour = random.choice(list(active_hours))
    base = datetime.now() - timedelta(days=random.randint(1, 30))
    return base.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    ).isoformat()


def _reset_runtime_files():
    """Xoa sach cac file runtime (session, OTP, login history thoi gian thuc)."""
    runtime_files = {
        RUNTIME_HISTORY_PATH: "timestamp,user_id,ip_address,device_id,login_hour,risk_score,decision,result,engine_version\n",
        OTP_STORE_PATH:        "user_id,otp,created_at\n",
        SESSION_STORE_PATH:    "user_id,login_time,last_activity,status\n",
        DATA_EVENTS_PATH:      "user_id,event,timestamp\n",
    }
    for path, header in runtime_files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
    print("  [OK] Runtime files cleared.")


def _generate_clean_baseline(num_records: int = 150):
    """
    Tao moi baseline sach:
    - Moi user CHI dung IP va Device co dinh trong profile.
    - Phan bo deu cho 3 user (50 ban ghi moi nguoi).
    - Khong co bat ky IP la hay Device la nao trong training set.
    """
    users = list(CLEAN_PROFILES.keys())
    os.makedirs(os.path.dirname(RAW_HISTORY_PATH), exist_ok=True)

    with open(RAW_HISTORY_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)

        for login_id in range(1, num_records + 1):
            user    = users[(login_id - 1) % len(users)]
            profile = CLEAN_PROFILES[user]

            writer.writerow([
                login_id,
                user,
                profile["ip"],
                profile["device"],
                _make_login_time(profile["active_hours"]),
                True,
                0,
                "ALLOW",
            ])

    print(f"  [OK] Clean baseline generated: {num_records} records, 0% noise.")


def reseed():
    print("\n[RESEED] Khoi dong lai du lieu baseline...\n")

    print("[1/3] Xoa runtime files...")
    _reset_runtime_files()

    print("[2/3] Tao baseline sach...")
    _generate_clean_baseline(num_records=150)

    # Xoa model cu de AI huan luyen lai tu dau voi du lieu sach
    model_path = "data/ml_model.joblib"
    if os.path.exists(model_path):
        os.remove(model_path)
        print("  [OK] Old ML model removed -- will retrain on next launch.")

    print("\n[DONE] RESEED HOAN TAT!")
    print("   -> Chay lai system_console_v2.py de bat dau demo.\n")


if __name__ == "__main__":
    reseed()
