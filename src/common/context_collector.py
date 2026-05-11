from datetime import datetime
import random

# USER BEHAVIOR PROFILE
# Đồng bộ với CLEAN_PROFILES trong reseed_system.py:
# mỗi user chỉ có DUY NHẤT 1 IP + 1 Device để AI học được "vùng an toàn" rõ nét.
USER_PROFILES = {
    "nguyen.hoang.thienanh": {
        "known_ips":     ["113.190.45.24"],   # IP nhà riêng, cố định
        "known_devices": ["Edge_Windows_10"], # Laptop văn phòng, cố định
        "active_hours":  range(8, 21),
    },
    "cao.viet.bac": {
        "known_ips":     ["27.72.88.101"],        # IP văn phòng, cố định
        "known_devices": ["Samsung_Internet"],    # Điện thoại quen thuộc, cố định
        "active_hours":  range(9, 22),
    },
    "nguyen.viet.anh": {
        "known_ips":     ["14.162.12.88"],   # IP nhà riêng, cố định
        "known_devices": ["Firefox_Linux"],  # Máy trạm quen thuộc, cố định
        "active_hours":  range(7, 20),
    },
}


def collect_context(user_id, scenario=None, demo_mode=False):
    """
    Chỉ thu thập context – KHÔNG quyết định OTP
    """

    profile = USER_PROFILES.get(user_id)

    # USER MỚI
    if profile is None:
        return {
            "ip_address": "10.0.79.225",
            "device_id": "Unknown_Device",
            "login_hour": datetime.now().hour,
            "note": "new_user"
        }

    # DEMO MODE
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
                "device_id": "MacBook_Pro_M3_Unknown",
                "login_hour": 23,
                "note": "unusual_device_or_time"
            }

        if scenario == "attack":
            return {
                "ip_address": "10.0.79.225",
                "device_id": "Unknown_Device",
                "login_hour": 2,
                "note": "high_risk_attack"
            }

        if scenario == "coffee_shop":
            return {
                "ip_address": "172.16.0.100", # Fixed IP for demo consistency (Learning)
                "device_id": random.choice(profile["known_devices"]), # Trusted device
                "login_hour": 15,
                "note": "new_location_trusted_device"
            }

    # SYSTEM MODE
    return {
        "ip_address": random.choice(profile["known_ips"]),
        "device_id": random.choice(profile["known_devices"]),
        "login_hour": random.choice(list(profile["active_hours"]))
        # ❌ KHÔNG NOTE
    }
