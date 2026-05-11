import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
from datetime import datetime

# PATH CONFIG
RAW_HISTORY_PATH = "data/raw/login_history.csv"
MODEL_PATH = "data/ml_model.joblib"

class MLRiskEngine:
    def __init__(self):
        self.model = None
        self.user_data_stats = {} # Cache for user profiles
        self.live_events = [] # Stores events captured during the current session
        self.train_model()

    def _prepare_data(self, df):
        """
        Prepares data for Isolation Forest.
        Features: login_hour, is_new_ip, is_new_device
        Note: We calculate 'is_new' relative to the user's history in the training set.
        """
        processed_data = []
        
        # Group by user to understand their baseline
        for user_id, group in df.groupby("user_id"):
            known_ips = set()
            known_devices = set()
            
            # Sort by time to simulate history
            group = group.sort_values("login_time")
            
            for _, row in group.iterrows():
                # For training, we calculate if it WAS new at that time
                is_new_ip = 1 if row["ip_address"] not in known_ips else 0
                is_new_device = 1 if row["device_id"] not in known_devices else 0
                
                # Add to features
                processed_data.append([
                    pd.to_datetime(row["login_time"]).hour,
                    is_new_ip,
                    is_new_device
                ])
                
                # Update knowledge for next rows
                known_ips.add(row["ip_address"])
                known_devices.add(row["device_id"])
            
            # Save final stats for inference
            self.user_data_stats[user_id] = {
                "known_ips": known_ips,
                "known_devices": known_devices
            }
            
        return np.array(processed_data)

    def train_model(self):
        if not os.path.exists(RAW_HISTORY_PATH):
            print("⚠️ No raw history found for ML training.")
            return

        df = pd.read_csv(RAW_HISTORY_PATH)
        
        # Merge with live events for re-training
        if self.live_events:
            live_df = pd.DataFrame(self.live_events)
            # Ensure column consistency
            live_df["login_time"] = datetime.now().isoformat()
            df = pd.concat([df, live_df], ignore_index=True)

        X = self._prepare_data(df)
        
        if len(X) == 0:
            return

        # Isolation Forest: contamination is the expected % of anomalies
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.model.fit(X)
        
        # Save model
        joblib.dump(self.model, MODEL_PATH)
        # print("✅ ML Model (Isolation Forest) trained and saved.")

    def update_model(self, new_event):
        """
        Adds a new successful login event to the training set and re-trains.
        This is what makes the model 'learn' during the demo.
        """
        user_id = new_event["user_id"]
        
        # Update internal stats
        if user_id not in self.user_data_stats:
            self.user_data_stats[user_id] = {"known_ips": set(), "known_devices": set()}
        
        self.user_data_stats[user_id]["known_ips"].add(new_event["ip_address"])
        self.user_data_stats[user_id]["known_devices"].add(new_event["device_id"])
        
        # PERSISTENT LEARNING: Append to the raw history file so it survives restarts
        if os.path.exists(RAW_HISTORY_PATH):
            import csv
            # We only need the core features for the ML model to learn
            with open(RAW_HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    999, # login_id (dummy)
                    user_id,
                    new_event["ip_address"],
                    new_event["device_id"],
                    datetime.now().isoformat(),
                    "True",
                    0,
                    "ALLOW"
                ])

        # Add to live events buffer for re-training
        self.live_events.append(new_event)
        
        # Re-train model with combined data
        self.train_model()

    def calculate_risk_ml(self, login_event):
        """
        Hybrid Risk Scoring: AI Score + Security Penalties

        Layer 1 (AI - Isolation Forest):
          Phát hiện các bất thường tinh vi trong hành vi dài hạn.

        Layer 2 (Rules - Security Penalties):
          Cộng điểm phạt cứng khi có nhiều yếu tố rủi ro xuất hiện đồng thời.
          Đây là phương pháp Hybrid được dùng bởi Google Identity & Auth0.

        Returns: Score 0-100 (cao = nguy hiểm hơn)
        """
        if self.model is None:
            return 50  # Fallback nếu model chưa sẵn sàng

        user_id = login_event["user_id"]
        stats   = self.user_data_stats.get(user_id)

        if stats is None:
            return 45  # User mới → trigger Biometric

        hour          = login_event["login_hour"]
        is_new_ip     = 1 if login_event["ip_address"] not in stats["known_ips"]     else 0
        is_new_device = 1 if login_event["device_id"]  not in stats["known_devices"] else 0

        # ── Layer 1: AI Base Score ───────────────────────────────────────────
        X_input  = np.array([[hour, is_new_ip, is_new_device]])
        raw_score = self.model.decision_function(X_input)[0]

        if raw_score >= 0.05:
            ai_score = 10
        elif raw_score >= 0:
            ai_score = 10 + (0.05 - raw_score) / 0.05 * 15
        else:
            # New locations/behaviors should start at 30+ to trigger BIOMETRIC
            ai_score = 30 + (abs(raw_score) / 0.2) * 70

        # Cap AI score tai 50: AI chi la lop nhan dien xu huong (Base),
        # khong du quyen BLOCK mot minh. Penalty Rules moi la lop quyet dinh.
        ai_score = max(0, min(50, ai_score))

        # ── Layer 2: Security Penalties (Hybrid Rules) ───────────────────────
        # Các luật cứng này đảm bảo các kịch bản tấn công rõ ràng luôn bj BLOCK
        # dù AI có điểm thấp do dữ liệu lịch sử hạn chế.
        penalty = 0

        if is_new_device:
            penalty += 10   # Thiet bi la = nghi ngo, can xac thuc them (BIOMETRIC)

        if hour < 6:
            penalty += 30   # Dang nhap 0h-5h sang = tan cong khi ngu (gio gioi nghiem cuc doan)

        if is_new_ip and is_new_device:
            penalty += 20   # Ca IP la lan Device la cung luc = tan cong tu xa (combo nguy hiem)

        final_score = ai_score + penalty

        # ── Layer 3: Trust Bonus ─────────────────────────────────────────────
        # High trust only if BOTH IP and Device are known and verified.
        # If IP is new (even if device is known), we still want BIOMETRIC.
        if not is_new_ip and not is_new_device:
            final_score -= 20
        # Removed partial trust bonus to ensure new IPs are properly challenged

        final_score = int(max(0, min(100, final_score)))
        return final_score

# Singleton instance
engine = MLRiskEngine()

def calculate_risk(login_event):
    return engine.calculate_risk_ml(login_event)

def update_model(login_event):
    engine.update_model(login_event)
