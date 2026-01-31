# src/common/context_collector.py

from datetime import datetime
import random

# USER BEHAVIOR PROFILE
USER_PROFILES = {
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


def collect_context(user_id, scenario=None, demo_mode=False):
    """
    Thu thập context đăng nhập

    demo_mode = True:
        scenario = normal | suspicious | attack (ép để demo)

    demo_mode = False:
        hệ thống tự suy luận (chưa triển khai, để mở rộng)
    """

    profile = USER_PROFILES.get(user_id)

    # ===== USER CHƯA TỒN TẠI =====
    if profile is None:
        return {
            "ip_address": "10.0.79.225",
            "device_id": "Unknown_Device",
            "login_hour": datetime.now().hour,
            "note": "new_user"
        }

    # ===== DEMO MODE =====
    if demo_mode:
        if scenario == "normal":
            return {
                "ip_address": random.choice(profile["known_ips"]),
                "device_id": random.choice(profile["known_devices"]),
                "login_hour": random.choice(list(profile["active_hours"])),
                "note": "normal_behavior"
            }

        if scenario == "suspicious":
            return {
                "ip_address": random.choice(profile["known_ips"]),
                "device_id": "Safari_iPhone_14",   # thiết bị lạ
                "login_hour": 23,                  # giờ muộn
                "note": "unusual_device_or_time"
            }

        if scenario == "attack":
            return {
                "ip_address": "10.0.79.225",       # IP lạ
                "device_id": "Unknown_Device",
                "login_hour": 2,                   # rạng sáng
                "note": "high_risk_attack"
            }

    # ===== SYSTEM MODE (CHƯA DEMO) =====
    # Tạm thời fallback = hành vi quen
    return {
        "ip_address": random.choice(profile["known_ips"]),
        "device_id": random.choice(profile["known_devices"]),
        "login_hour": random.choice(list(profile["active_hours"])),
        "note": "auto_inferred"
    }