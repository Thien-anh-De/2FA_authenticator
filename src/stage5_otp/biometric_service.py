import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def simulate_biometric_verification(user_id):
    """
    Simulates a biometric (FaceID/Fingerprint) verification flow.
    Returns True if 'approved', False otherwise.
    """
    console.print()
    console.print(Panel(
        f"[bold cyan]📱 BIOMETRIC VERIFICATION[/bold cyan]\n"
        f"[dim]Sending authentication request to registered device for [white]{user_id}[/white]...[/dim]",
        border_style="cyan",
        padding=(0, 2)
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold yellow]  Waiting for Biometric Approval on Mobile...[/bold yellow]"),
        console=console,
        transient=True
    ) as progress:
        progress.add_task("biometric", total=None)
        time.sleep(2.0) # Simulate network delay

    console.print("[bold yellow]🔔 Push Notification Received on Phone![/bold yellow]")
    
    # In a real app, this would be a WebAuthn response. 
    # Here we simulate the user action on the phone via a console prompt.
    choice = console.input("[bold green]  [Phone Simulator][/bold green] Approve this login? (y/n): ").strip().lower()
    
    if choice == 'y':
        with console.status("[bold green]Verifying cryptographic signature...[/bold green]"):
            time.sleep(1.5)
        return True
    else:
        return False

def show_biometric_success():
    console.print(Panel(
        "[bold green]✅  BIOMETRIC AUTHENTICATED[/bold green]\n"
        "[dim]Cryptographic identity confirmed via FIDO2/WebAuthn simulation.[/dim]",
        border_style="green",
        padding=(0, 2)
    ))
