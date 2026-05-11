from src.stage5_otp.login_flow import login
from src.stage6_pipeline.data_pipeline import send_event
from src.common.context_collector import collect_context
from src.stage6_pipeline.session_store import (
    update_session,
    is_session_expired
)

# IMPORT RUNTIME HISTORY
from src.stage4_risk_engine.risk_engine import (
    load_runtime_history,
    successful_login_count
)

# ── Rich UI ─────────────────────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich import box
import time

console = Console()

# ─────────────────────────────────────────────────────────────────────────────


def print_banner():
    banner = Text()
    banner.append("  ██████╗ ███████╗ █████╗      ██████╗ ", style="bold cyan")
    banner.append("  ██╔══██╗██╔════╝██╔══██╗    ██╔═══██╗", style="bold cyan")
    banner.append("\n  ╚════██╗██████╗ ███████║    ██║   ██║ ", style="bold cyan")
    banner.append("  ██║   ██║   ╚══════╝╝██╔══██╗    ██║   ██║", style="bold cyan")
    banner.append("\n  ██████╔╝██╔════╝██╔══██║    ╚██████╔╝", style="bold cyan")
    banner.append("  ╚═════╝ ╚═════╝╚═╝  ╚═╝     ╚═════╝ ", style="bold cyan")

    console.print(Panel(
        "[bold cyan]🔐  2FA ADAPTIVE AUTHENTICATION SYSTEM[/bold cyan]\n"
        "[dim]Risk-Based Engine  •  OTP Verification  •  Session Management[/dim]",
        border_style="cyan",
        padding=(1, 4),
        title="[bold white]SECURE LOGIN PORTAL[/bold white]",
        title_align="center"
    ))


def choose_demo_scenario():
    console.print()
    table = Table(
        title="[bold yellow]⚡ DEMO SCENARIO SELECTOR[/bold yellow]",
        box=box.ROUNDED,
        border_style="yellow",
        show_header=True,
        header_style="bold white"
    )
    table.add_column("Option", style="bold cyan", width=8)
    table.add_column("Scenario", style="bold white", width=20)
    table.add_column("Expected Risk", style="bold", width=16)
    table.add_column("Decision", style="bold", width=12)

    table.add_row("  [1]", "🟢  Normal Login",    "[green]Low  (0–39)[/green]",  "[green]ALLOW[/green]")
    table.add_row("  [2]", "🟡  Suspicious Login", "[yellow]Mid  (40–69)[/yellow]", "[yellow]OTP[/yellow]")
    table.add_row("  [3]", "🔴  Attack Login",     "[red]High (70+)[/red]",      "[red]BLOCK[/red]")
    table.add_row("  [4]", "☕  Coffee Shop",      "[yellow]Mid  (40–69)[/yellow]", "[yellow]OTP[/yellow]")

    console.print(table)

    choice = Prompt.ask(
        "[bold cyan]Select scenario[/bold cyan]",
        choices=["1", "2", "3", "4"],
        default="1"
    )
    return {"1": "normal", "2": "suspicious", "3": "attack", "4": "coffee_shop"}[choice]


def login_ui():
    console.print()
    console.print(Panel(
        "[bold white]Please enter your credentials to proceed.[/bold white]",
        title="[bold cyan]🔑 AUTHENTICATION[/bold cyan]",
        border_style="cyan",
        padding=(0, 2)
    ))

    user_id = Prompt.ask("[bold cyan]  Username[/bold cyan]")

    # Animated context collection
    with console.status(
        "[bold cyan]Collecting system context...[/bold cyan]",
        spinner="dots"
    ):
        time.sleep(0.8)
        base_context = collect_context(user_id=user_id, demo_mode=False)

    # TRUST CHECK (RUNTIME HISTORY)
    with console.status(
        "[bold cyan]Checking trust history...[/bold cyan]",
        spinner="dots"
    ):
        time.sleep(0.6)
        df = load_runtime_history()
        success_count = successful_login_count(df, user_id)

    # TRUSTED USER (>= 3 SUCCESS)
    if success_count >= 3:
        console.print(Panel(
            f"[bold green]✅  TRUSTED USER DETECTED[/bold green]\n"
            f"[dim]Successful logins: {success_count}[/dim]\n\n"
            f"[green]Action → ALLOW (no OTP required)[/green]",
            border_style="green",
            title="[bold green]SYSTEM ANALYSIS[/bold green]",
            padding=(0, 2)
        ))
        return {
            "user_id": user_id,
            "ip_address": base_context["ip_address"],
            "device_id": base_context["device_id"],
            "login_hour": base_context["login_hour"]
        }

    # NEW USER → ADAPTIVE AUTH
    if base_context.get("note") == "new_user":
        console.print(Panel(
            f"[bold yellow]👤  NEW USER DETECTED[/bold yellow]\n"
            f"[dim]User '{user_id}' has no behavioral history.[/dim]\n\n"
            f"[yellow]Action → Adaptive Authentication Pipeline[/yellow]",
            border_style="yellow",
            title="[bold yellow]SYSTEM ANALYSIS[/bold yellow]",
            padding=(0, 2)
        ))
        return {
            "user_id": user_id,
            "ip_address": base_context["ip_address"],
            "device_id": base_context["device_id"],
            "login_hour": base_context["login_hour"]
        }

    # UNTRUSTED USER → DEMO SCENARIO
    scenario = choose_demo_scenario()

    with console.status(
        "[bold cyan]Simulating login context...[/bold cyan]",
        spinner="point"
    ):
        time.sleep(0.8)
        demo_context = collect_context(
            user_id=user_id,
            scenario=scenario,
            demo_mode=True
        )

    # Display context summary
    ctx_table = Table(
        title="[bold white]📡 CAPTURED LOGIN CONTEXT[/bold white]",
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan"
    )
    ctx_table.add_column("Field", style="bold white", width=16)
    ctx_table.add_column("Value", style="dim white", width=28)

    ctx_table.add_row("User ID",     f"[bold]{user_id}[/bold]")
    ctx_table.add_row("IP Address",  demo_context["ip_address"])
    ctx_table.add_row("Device",      demo_context["device_id"])
    ctx_table.add_row("Login Hour",  f"{demo_context['login_hour']}:00")
    ctx_table.add_row("Behavior",    demo_context.get("note", "—"))
    ctx_table.add_row("Trust Score", f"[yellow]{success_count}/3 logins[/yellow]")

    console.print()
    console.print(ctx_table)

    return {
        "user_id": user_id,
        "ip_address": demo_context["ip_address"],
        "device_id": demo_context["device_id"],
        "login_hour": demo_context["login_hour"],
        "note": demo_context.get("note")
    }


def print_menu(current_user):
    console.print()
    status_line = (
        f"[bold green]● Logged in as [cyan]{current_user}[/cyan][/bold green]"
        if current_user else
        "[dim]○ Not logged in[/dim]"
    )

    menu_table = Table(
        box=box.ROUNDED,
        border_style="blue",
        show_header=False,
        title=f"[bold blue]MAIN MENU[/bold blue]  {status_line}",
        padding=(0, 2)
    )
    menu_table.add_column("Option", style="bold cyan", width=6)
    menu_table.add_column("Action", style="white", width=24)

    if current_user is None:
        menu_table.add_row("[1]", "🔑  Login")
    else:
        menu_table.add_row("[1]", "🚪  Logout")

    menu_table.add_row("[2]", "📦  Send Data Event")
    menu_table.add_row("[0]", "❌  Exit")

    console.print(menu_table)


def main():
    current_user = None
    print_banner()

    while True:
        # Session expiry check
        if current_user and is_session_expired(current_user):
            console.print(Panel(
                f"[bold red]⛔  SESSION EXPIRED[/bold red]\n"
                f"[dim]Your session for '{current_user}' has timed out.[/dim]\n"
                f"[yellow]→ Please login again.[/yellow]",
                border_style="red",
                padding=(0, 2)
            ))
            update_session(current_user, "EXPIRED")
            current_user = None

        print_menu(current_user)
        choice = Prompt.ask("[bold cyan]Choose[/bold cyan]", choices=["0", "1", "2"])

        if choice == "1":
            if current_user is None:
                login_request = login_ui()
                success = login(login_request)

                if success:
                    current_user = login_request["user_id"]
                    console.print(Panel(
                        f"[bold green]✅  Welcome, [cyan]{current_user}[/cyan]![/bold green]\n"
                        f"[dim]Session started successfully.[/dim]",
                        border_style="green",
                        padding=(0, 2)
                    ))
            else:
                update_session(current_user, "LOGOUT")
                console.print(Panel(
                    f"[bold yellow]👋  Goodbye, [cyan]{current_user}[/cyan]![/bold yellow]\n"
                    f"[dim]You have been logged out.[/dim]",
                    border_style="yellow",
                    padding=(0, 2)
                ))
                current_user = None

        elif choice == "2":
            if not current_user:
                console.print(
                    Panel("[bold red]⚠ Please login first.[/bold red]",
                          border_style="red", padding=(0, 2))
                )
                continue

            event = Prompt.ask("[bold cyan]  Event name[/bold cyan]")
            success = send_event(current_user, event)

            if success is False:
                current_user = None

        elif choice == "0":
            console.print(Panel(
                "[bold cyan]👋  Goodbye! Stay secure.[/bold cyan]",
                border_style="cyan",
                padding=(0, 2)
            ))
            break


if __name__ == "__main__":
    main()
