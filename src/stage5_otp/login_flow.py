from datetime import datetime
import csv
import os
import time

from src.stage4_risk_engine.risk_engine import (
    calculate_risk,
    decision_from_risk
)
from src.stage5_otp.otp_service import (
    generate_otp,
    verify_otp
)
from src.stage6_pipeline.session_store import update_session

# ── Rich UI ─────────────────────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

console = Console()
# ─────────────────────────────────────────────────────────────────────────────

LOGIN_HISTORY_PATH = "data/login_history.csv"


def write_login_history(user_login, risk, decision, result):
    file_exists = os.path.exists(LOGIN_HISTORY_PATH)

    with open(LOGIN_HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists or os.path.getsize(LOGIN_HISTORY_PATH) == 0:
            writer.writerow([
                "timestamp",
                "user_id",
                "ip_address",
                "device_id",
                "login_hour",
                "risk_score",
                "decision",
                "result"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            user_login["user_id"],
            user_login["ip_address"],
            user_login["device_id"],
            user_login["login_hour"],
            risk,
            decision,
            result
        ])


def _print_login_attempt(user_login):
    """Render the login attempt info card."""
    info_table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="dim",
        show_header=False,
        padding=(0, 2)
    )
    info_table.add_column("Field", style="dim white", width=12)
    info_table.add_column("Value", style="bold white", width=28)

    info_table.add_row("User ID",    f"[bold cyan]{user_login['user_id']}[/bold cyan]")
    info_table.add_row("IP Address", user_login['ip_address'])
    info_table.add_row("Device",     user_login['device_id'])
    info_table.add_row("Hour",       f"{user_login['login_hour']}:00")

    console.print(Panel(
        info_table,
        title="[bold white]🔐 LOGIN ATTEMPT[/bold white]",
        border_style="cyan",
        padding=(0, 1)
    ))


def _print_risk_analysis(user_login, risk, decision):
    """Render the risk score analysis card with visual progress bar."""

    # Determine color based on risk
    if risk < 40:
        risk_color = "green"
        risk_label = "LOW RISK"
    elif risk < 70:
        risk_color = "yellow"
        risk_label = "MEDIUM RISK"
    else:
        risk_color = "red"
        risk_label = "HIGH RISK"

    # Decision badge
    decision_style = {
        "ALLOW": "[bold green]✅  ALLOW[/bold green]",
        "OTP":   "[bold yellow]🔐  OTP REQUIRED[/bold yellow]",
        "BLOCK": "[bold red]⛔  BLOCKED[/bold red]"
    }.get(decision, decision)

    # Risk bar (visual)
    filled = int(risk / 100 * 20)
    bar = f"[{risk_color}]" + "█" * filled + "[/]" + "░" * (20 - filled)

    risk_content = (
        f"[bold white]Risk Score :[/bold white]  "
        f"[bold {risk_color}]{risk}/100[/bold {risk_color}]  [{risk_color}]({risk_label})[/{risk_color}]\n"
        f"[bold white]Gauge      :[/bold white]  {bar}\n\n"
        f"[bold white]Decision   :[/bold white]  {decision_style}"
    )

    console.print()
    console.print(Panel(
        risk_content,
        title="[bold white]🧠 RISK ENGINE ANALYSIS[/bold white]",
        border_style=risk_color,
        padding=(0, 2)
    ))


def login(user_login: dict) -> bool:
    _print_login_attempt(user_login)

    with console.status(
        "[bold cyan]Running risk analysis...[/bold cyan]",
        spinner="dots12"
    ):
        time.sleep(1.0)
        risk = calculate_risk(user_login)
        decision = decision_from_risk(risk)

    _print_risk_analysis(user_login, risk, decision)

    # ── ALLOW ──────────────────────────────────────────────────────────────
    if decision == "ALLOW":
        update_session(user_login["user_id"], "ALLOW")
        write_login_history(user_login, risk, decision, "SUCCESS")

        console.print(Panel(
            "[bold green]✅  Login successful![/bold green]\n"
            "[dim]No additional verification required.[/dim]",
            border_style="green",
            padding=(0, 2)
        ))
        return True

    # ── BLOCK ──────────────────────────────────────────────────────────────
    if decision == "BLOCK":
        update_session(user_login["user_id"], "BLOCK")
        write_login_history(user_login, risk, decision, "BLOCKED")

        console.print(Panel(
            "[bold red]⛔  Access denied![/bold red]\n"
            "[dim]This request has been flagged as a potential attack.[/dim]",
            border_style="red",
            padding=(0, 2)
        ))
        return False

    # ── OTP ────────────────────────────────────────────────────────────────
    if decision == "OTP":
        console.print()
        console.print(Panel(
            "[bold yellow]🔐  Two-Factor Authentication Required[/bold yellow]\n"
            "[dim]A one-time password has been sent to your registered device.[/dim]",
            border_style="yellow",
            padding=(0, 2)
        ))

        otp_secret = generate_otp(user_login["user_id"])

        # Countdown visual
        console.print()
        with Progress(
            TextColumn("[bold yellow]  OTP valid for[/bold yellow]"),
            BarColumn(bar_width=30, style="yellow", complete_style="green"),
            TextColumn("[cyan]{task.fields[remaining]}s remaining[/cyan]"),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("otp", total=60, remaining=60)
            for _ in range(3):  # Show 3-second countdown then let user type
                time.sleep(1)
                progress.update(task, advance=1, remaining=60 - _ - 1)

        user_input = Prompt.ask("[bold yellow]  Enter OTP[/bold yellow]")

        if verify_otp(user_login["user_id"], user_input):
            update_session(user_login["user_id"], "OTP_VERIFIED")
            write_login_history(user_login, risk, decision, "OTP_SUCCESS")

            console.print(Panel(
                "[bold green]✅  OTP Verified! Login successful.[/bold green]\n"
                "[dim]Your identity has been confirmed.[/dim]",
                border_style="green",
                padding=(0, 2)
            ))
            return True
        else:
            update_session(user_login["user_id"], "OTP_FAILED")
            write_login_history(user_login, risk, decision, "OTP_FAILED")

            console.print(Panel(
                "[bold red]❌  OTP verification failed.[/bold red]\n"
                "[dim]Wrong or expired OTP. Please try again.[/dim]",
                border_style="red",
                padding=(0, 2)
            ))
            return False