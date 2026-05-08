# 🔐 2FA Adaptive Authentication System

An intelligent, context-aware 2-Factor Authentication (2FA) system that balances high security with a frictionless user experience. 

Instead of statically requiring an OTP (One-Time Password) for every login, this system uses a **Dynamic Risk Engine** to analyze the user's context (IP Address, Device, Time) and determines the appropriate security action: `ALLOW` (pass), `OTP` (verify), or `BLOCK` (prevent).

---

## ✨ Key Features

*   **🧠 Dynamic Risk Engine**: Calculates a risk score based on historical baseline behavior (`raw_history`) and current context.
*   **🤝 Trust Building System**: Automatically learns user habits. If a new device is verified via OTP successfully 3 times, it becomes a "Trusted Device" and no longer requires OTP.
*   **🛡️ Adaptive Security Actions**:
    *   **Low Risk (<40)**: Instant access (`ALLOW`).
    *   **Medium Risk (40-69)**: Step-up authentication (`OTP`).
    *   **High Risk (≥70)**: Immediate access denial (`BLOCK`).
*   **💻 Rich Terminal UI (TUI)**: A beautiful, interactive console interface built with the `rich` library, featuring animated risk analysis and color-coded panels.
*   **📊 Live Admin Dashboard**: A real-time web dashboard built with `Streamlit` to monitor login events, risk distribution, active sessions, and behavioral profiles.

---

## 🛠️ Prerequisites

Ensure you have Python 3.8+ installed. You will need the following libraries:

```bash
pip install pandas rich streamlit
```

---

## 🚀 Installation & Usage

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd 2FA_Authenticator
   ```

2. **Reset the database** (Optional, to start with a clean slate):
   ```bash
   python reset_csv.py
   ```

3. **Run the Live Admin Dashboard**:
   Open a terminal and run the Streamlit app. It will automatically open in your web browser.
   ```bash
   streamlit run dashboard.py
   ```

4. **Run the Interactive Login Console**:
   Open a *second* terminal and run the main application to simulate user logins.
   ```bash
   python system_console.py
   ```

---

## 📂 Project Structure

```text
2FA_Authenticator/
├── data/                       # CSV databases acting as the system's memory
│   ├── raw/
│   │   └── login_history.csv   # Baseline behavioral data (known IPs, devices)
│   ├── data_events.csv         # Post-login activity logs
│   ├── login_history.csv       # Runtime login attempts and decisions
│   ├── otp_store.csv           # Temporary OTP storage
│   └── session_store.csv       # Active session management
├── src/
│   ├── common/
│   │   └── context_collector.py # Simulates collecting IP, Device, and Time
│   ├── stage4_risk_engine/
│   │   └── risk_engine.py       # Core logic: calculates risk scores and decisions
│   ├── stage5_otp/
│   │   ├── login_flow.py        # Orchestrates the login steps (Risk -> Decision -> OTP)
│   │   └── otp_service.py       # Generates and verifies 6-digit OTPs
│   └── stage6_pipeline/
│       ├── data_pipeline.py     # Records events for authenticated users
│       └── session_store.py     # Manages session timeouts and states
├── dashboard.py                # Streamlit Web Dashboard (Admin God-View)
├── system_console.py           # Main Entry Point (Rich Terminal UI)
└── reset_csv.py                # Utility to wipe data and reset the system
```

---

## 🎬 Demo Scenarios

When running `system_console.py`, you can test various scenarios:

1.  **Normal Login**: System recognizes a trusted user/device -> Grants immediate access.
2.  **Suspicious Login**: System detects an unknown device -> Requests OTP -> Grants access upon correct entry.
3.  **Attack Login**: System detects high-risk context -> Blocks access immediately to protect the account.
4.  **Trust Building**: Successfully log in with OTP 3 times on a new device. On the 4th attempt, the system will recognize it as trusted and grant access without OTP.

---

## 📝 License
This project was created for educational and demonstration purposes.
