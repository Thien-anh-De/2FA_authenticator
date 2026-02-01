import sys
import os
import csv
import random
from datetime import datetime, timedelta

# FIX IMPORT PATH
sys.path.append(os.path.abspath("."))

from src.common.config import DATA_PATH


# USERS
USERS = {
    "nguyen.hoang.thienanh": {
        "known_ips": ["113.190.45.23", "113.190.45.24"],  # Hà Nội
        "known_devices": ["Chrome_Windows_10", "Edge_Windows_10"],
        "active_hours": range(8, 22)
    },
    "cao.viet.bac": {
        "known_ips": ["27.72.88.101"],  # HCM
        "known_devices": ["Chrome_Android", "Samsung_Internet"],
        "active_hours": range(9, 23)
    },
    "nguyen.viet.anh": {
        "known_ips": ["14.162.12.88"],  # Đà Nẵng
        "known_devices": ["Firefox_Linux", "Chrome_Linux"],
        "active_hours": range(7, 21)
    }
}

FIELDS = [
    "login_id",
    "user_id",
    "ip_address",
    "device_id",
    "login_time",
    "login_result",
    "risk_score",
    "decision"
]


def random_time_for_user(user):
    now = datetime.now()
    hour = random.choice(list(USERS[user]["active_hours"]))
    return now.replace(hour=hour, minute=random.randint(0, 59)) - timedelta(days=random.randint(0, 3))


def pick_ip(user):
    if random.random() < 0.8:
        return random.choice(USERS[user]["known_ips"])
    return f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}"  # IP lạ


def pick_device(user):
    if random.random() < 0.8:
        return random.choice(USERS[user]["known_devices"])
    return random.choice([
        "Safari_iPhone_14",
        "Chrome_Windows_11",
        "Chrome_Android"
    ])


def generate(num_records=150):
    with open(DATA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)

        login_id = 1
        for _ in range(num_records):
            user = random.choice(list(USERS.keys()))
            login_time = random_time_for_user(user)

            writer.writerow([
                login_id,
                user,
                pick_ip(user),
                pick_device(user),
                login_time.isoformat(),
                random.random() > 0.15,  # 85% login success
                0,
                "PENDING"
            ])
            login_id += 1


if __name__ == "__main__":
    generate()
    print("✅ login_history.csv generated with REALISTIC users (Stage 3)")
