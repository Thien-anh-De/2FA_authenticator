import time
from src.v2.login_flow_v2 import login_v2
from src.stage6_pipeline.data_pipeline import send_event
from src.common.context_collector import collect_context
from src.stage6_pipeline.session_store import (
    update_session,
    is_session_expired
)
from src.stage4_risk_engine.risk_engine import (
    load_runtime_history,
    successful_login_count
)

# Rich UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich import box

console = Console()

def print_banner_v2():
    console.print(Panel(
        "[bold cyan]🔐  2FA ADAPTIVE AUTHENTICATION — VERSION 2.0[/bold cyan]\n"
        "[bold magenta]🤖 Machine Learning Powered (Isolation Forest)[/bold magenta]  •  [bold yellow]📱 Passwordless Biometrics[/bold yellow]",
        border_style="magenta",
        padding=(1, 4),
        title="[bold white]MODERN SECURE PORTAL[/bold white]",
        title_align="center"
    ))

def choose_demo_scenario():
    console.print()
    table = Table(
        title="[bold yellow]⚡ ML DEMO SCENARIO SELECTOR[/bold yellow]",
        box=box.ROUNDED,
        border_style="yellow",
        show_header=True,
        header_style="bold white"
    )
    table.add_column("Option", style="bold cyan", width=8)
    table.add_column("Scenario", style="bold white", width=20)
    table.add_column("ML Expected", style="bold", width=16)
    table.add_column("Action", style="bold", width=12)

    table.add_row("  [1]", "🟢  Usual Activity",   "[green]Low (Inlier)[/green]",  "[green]ALLOW[/green]")
    table.add_row("  [2]", "🟡  Minor Anomaly",    "[yellow]Mid (Suspect)[/yellow]", "[yellow]BIOMETRIC[/yellow]")
    table.add_row("  [3]", "🔴  Major Anomaly",    "[red]High (Outlier)[/red]",    "[red]BLOCK[/red]")
    table.add_row("  [4]", "☕  Traveling (New IP)", "[cyan]Adaptive Learner[/cyan]", "[cyan]LEARN/ALLOW[/cyan]")

    console.print(table)
    choice = Prompt.ask("[bold cyan]Select scenario[/bold cyan]", choices=["1", "2", "3", "4"], default="1")
    return {"1": "normal", "2": "suspicious", "3": "attack", "4": "coffee_shop"}[choice]

def login_ui_v2():
    console.print()
    console.print(Panel(
        "[bold white]Passwordless Portal: Enter Username only.[/bold white]",
        title="[bold magenta]🔑 MODERN AUTH[/bold magenta]",
        border_style="magenta",
        padding=(0, 2)
    ))

    user_id = ""
    while not user_id.strip():
        user_id = Prompt.ask("[bold cyan]  Username[/bold cyan]")
    
    # NEW USER CHECK (using context_collector)
    with console.status("[bold cyan]Analyzing user history...[/bold cyan]", spinner="dots"):
        time.sleep(0.6)
        base_context = collect_context(user_id=user_id, demo_mode=False)

    if base_context.get("note") == "new_user":
        console.print(Panel(
            f"[bold yellow]👤  NEW USER DETECTED[/bold yellow]\n"
            f"[dim]User '{user_id}' has no behavioral baseline yet.[/dim]\n\n"
            f"[yellow]Action → Initial ML Profiling (Biometric Required)[/yellow]",
            border_style="yellow",
            title="[bold yellow]AI PRE-ANALYSIS[/bold yellow]",
            padding=(0, 2)
        ))
        return {
            "user_id": user_id,
            "ip_address": base_context["ip_address"],
            "device_id": base_context["device_id"],
            "login_hour": base_context["login_hour"]
        }

    # EXISTING USER -> SCENARIO SELECTION
    scenario = choose_demo_scenario()

    with console.status("[bold cyan]Capturing high-fidelity context...[/bold cyan]", spinner="arc"):
        time.sleep(1.0)
        demo_context = collect_context(user_id=user_id, scenario=scenario, demo_mode=True)

    ctx_table = Table(box=box.SIMPLE_HEAVY, border_style="magenta")
    ctx_table.add_column("Context Attribute", style="bold white")
    ctx_table.add_column("Captured Value", style="dim white")
    ctx_table.add_row("User ID", user_id)
    ctx_table.add_row("IP Address", demo_context["ip_address"])
    ctx_table.add_row("Device ID", demo_context["device_id"])
    ctx_table.add_row("Login Hour", f"{demo_context['login_hour']}:00")
    
    console.print(ctx_table)

    if scenario == "coffee_shop":
        console.print(Panel(
            "[bold cyan]💡 PRESENTATION TIP:[/bold cyan]\n"
            "In [bold yellow]Version 1 (Rules)[/bold yellow], this would ALWAYS require OTP because the IP is unknown.\n"
            "In [bold magenta]Version 2 (AI)[/bold magenta], the model checks if this device + time is typical, even if the IP is new.",
            border_style="cyan",
            padding=(0, 1)
        ))
    
    return {
        "user_id": user_id,
        "ip_address": demo_context["ip_address"],
        "device_id": demo_context["device_id"],
        "login_hour": demo_context["login_hour"]
    }

def main_v2():
    current_user = None
    print_banner_v2()

    while True:
        if current_user and is_session_expired(current_user):
            console.print(Panel(
                f"[bold red]⛔  SESSION EXPIRED[/bold red]\n"
                f"[dim]Your V2 session for '{current_user}' has timed out.[/dim]",
                border_style="red",
                padding=(0, 2)
            ))
            update_session(current_user, "EXPIRED")
            current_user = None

        console.print()
        status = f"[bold green]● [V2] {current_user}[/bold green]" if current_user else "[dim]○ Not logged in[/dim]"
        menu = Table(box=box.ROUNDED, border_style="magenta", title=f"V2 DASHBOARD {status}")
        menu.add_column("Key", style="bold cyan")
        menu.add_column("Action", style="white")
        if not current_user:
            menu.add_row("1", "🔑 Login (ML + Passwordless)")
        else:
            menu.add_row("1", "🚪 Logout")
        menu.add_row("2", "📦 Send Data Event")
        menu.add_row("0", "❌ Exit")
        
        console.print(menu)
        choice = Prompt.ask("[bold cyan]Choice[/bold cyan]", choices=["0", "1", "2"])

        if choice == "1":
            if not current_user:
                request = login_ui_v2()
                if login_v2(request):
                    current_user = request["user_id"]
            else:
                update_session(current_user, "LOGOUT")
                current_user = None
        elif choice == "2":
            if not current_user:
                console.print("[red]Login first![/red]")
                continue
            event = Prompt.ask("[bold cyan]Event[/bold cyan]")
            success = send_event(current_user, event)
            if success is False:
                current_user = None
        elif choice == "0":
            break

if __name__ == "__main__":
    main_v2()
