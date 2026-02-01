files = {
    "data/login_history.csv":
        "timestamp,user_id,ip_address,device_id,login_hour,risk_score,decision,result\n",
    "data/otp_store.csv":
        "user_id,otp,created_at\n",
    "data/session_store.csv":
        "user_id,login_time,last_activity,status\n",
    "data/data_events.csv":
        "user_id,event,timestamp\n"
}

for path, header in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)