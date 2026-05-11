import csv
import os
import time
from datetime import datetime

from src.stage4_risk_engine.ml_engine import calculate_risk as calculate_risk_ml, update_model as update_ml_model
from src.stage5_otp.biometric_service import simulate_biometric_verification, show_biometric_success
from src.stage6_pipeline.session_store import update_session

# ── Rich UI ─────────────────────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

LOGIN_HISTORY_PATH = "data/login_history.csv"

def write_login_history_v2(user_login, risk, decision, result):
    file_exists = os.path.exists(LOGIN_HISTORY_PATH)
    
    # We add a new column 'engine_version' for V2
    headers = ["timestamp", "user_id", "ip_address", "device_id", "login_hour", "risk_score", "decision", "result", "engine_version"]

    with open(LOGIN_HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(LOGIN_HISTORY_PATH) == 0:
            writer.writerow(headers)
        
        writer.writerow([
            datetime.now().isoformat(),
            user_login["user_id"],
            user_login["ip_address"],
            user_login["device_id"],
            user_login["login_hour"],
            risk,
            decision,
            result,
            "V2_ML"
        ])

def _print_risk_analysis_v2(risk, decision):
    if risk < 30:
        color = "green"
        label = "LOW (ML)"
    elif risk < 65:
        color = "yellow"
        label = "MEDIUM (ML)"
    else:
        color = "red"
        label = "HIGH (ML)"

    decision_style = {
        "ALLOW": "[bold green]✅  ALLOW (Passwordless)[/bold green]",
        "BIOMETRIC": "[bold yellow]📱  BIOMETRIC REQUIRED[/bold yellow]",
        "BLOCK": "[bold red]⛔  BLOCKED (Anomaly Detected)[/bold red]"
    }.get(decision, decision)

    filled = int(risk / 100 * 20)
    bar = f"[{color}]" + "█" * filled + "[/]" + "░" * (20 - filled)

    content = (
        f"[bold white]ML Anomaly Score:[/bold white] [{color}]{risk}/100[/{color}] [dim]({label})[/dim]\n"
        f"[bold white]Confidence Gauge:[/bold white] {bar}\n\n"
        f"[bold white]Action          :[/bold white] {decision_style}"
    )

    console.print(Panel(
        content,
        title="[bold white]🤖 ISOLATION FOREST ANALYSIS[/bold white]",
        border_style=color,
        padding=(0, 2)
    ))

def login_v2(user_login: dict) -> bool:
    console.print(Panel(
        f"[bold white]Initiating V2 Secure Login Pipeline[/bold white]\n"
        f"[dim]Features: Isolation Forest Anomaly Detection + Passwordless Biometrics[/dim]",
        border_style="blue"
    ))

    with console.status("[bold cyan]Running ML Inference...[/bold cyan]", spinner="bouncingBar"):
        time.sleep(1.2)
        risk = calculate_risk_ml(user_login)
        
        if risk < 30:
            decision = "ALLOW"
        elif risk < 65:
            decision = "BIOMETRIC"
        else:
            decision = "BLOCK"

    _print_risk_analysis_v2(risk, decision)

    if decision == "ALLOW":
        update_session(user_login["user_id"], "ALLOW")
        write_login_history_v2(user_login, risk, decision, "SUCCESS")
        update_ml_model(user_login)  # Hành vi an toàn → học bình thường
        console.print("[bold green]✅ ML verified your identity automatically. No password or OTP needed![/bold green]")
        return True

    if decision == "BLOCK":
        update_session(user_login["user_id"], "BLOCK")
        write_login_history_v2(user_login, risk, decision, "BLOCKED")
        return False

    if decision == "BIOMETRIC":
        if simulate_biometric_verification(user_login["user_id"]):
            update_session(user_login["user_id"], "OTP_VERIFIED")
            write_login_history_v2(user_login, risk, decision, "BIOMETRIC_SUCCESS")
            show_biometric_success()

            # Secure Learning: chỉ học nếu rủi ro ban đầu không quá cao.
            # Nếu risk >= 55, đây có thể là kẻ tấn công vượt qua Biometric
            # → KHÔNG cập nhật mô hình để tránh bị "đầu độc" (Model Poisoning).
            if risk < 55:
                update_ml_model(user_login)
                console.print(
                    f"[bold green]✨ Adaptive Engine learned this behavior![/bold green]\n"
                    f"[dim]IP {user_login['ip_address']} is now trusted for future logins.[/dim]"
                )
            else:
                console.print(
                    "[dim]⚠️  High-risk bypass detected. "
                    "Session granted but behavior NOT learned.[/dim]"
                )

            return True
        else:
            update_session(user_login["user_id"], "OTP_FAILED")
            write_login_history_v2(user_login, risk, decision, "BIOMETRIC_FAILED")
            console.print("[bold red]❌ Biometric verification failed or denied.[/bold red]")
            return False
