"""
Acadlabs CLI - Main Entry Point

AI-powered coding assistant CLI dengan Agentic Loop.
Supports interactive chat, authentication, and configuration management.

Redesigned with Claude Code-style interface.
"""
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box

from acadlabs_cli import __version__
from acadlabs_cli.commands import auth_app, chat_app, config_app
from acadlabs_cli import ui

console = Console()

# ═══════════════════════════════════════════════════════════════════════════
# Main App
# ═══════════════════════════════════════════════════════════════════════════

# NOTE: No emojis in help= strings! They crash on Windows cp1252 console.
# Use emojis only inside rich console.print() calls.

HELP_TEXT = """\b
AcadLabs CLI - AI-Powered Coding Assistant

Interact with AI coding assistant langsung dari terminal kamu.
Mendukung agentic loop (ReAct pattern), tools execution, dan
integrasi dengan platform AcadLabs.

\b
Quick Start:
  1. acadlabs login              Login ke akun AcadLabs
  2. acadlabs config init        Setup API keys
  3. acadlabs chat               Mulai sesi chat dengan AI

\b
Shortcuts (langsung tanpa subcommand):
  acadlabs login                 = acadlabs auth login
  acadlabs login-google          = acadlabs auth login-google
  acadlabs chat                  = acadlabs chat start

\b
Docs:   https://acadlabs.fun/docs
GitHub: https://github.com/Acadgacor/acadlabs-cli
"""

app = typer.Typer(
    name="acadlabs",
    help=HELP_TEXT,
    add_completion=True,
    no_args_is_help=True,
    pretty_exceptions_enable=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(
            f"  [{ui.Theme.ACCENT}]{ui.ICON_BRAND} AcadLabs CLI[/{ui.Theme.ACCENT}] "
            f"[{ui.Theme.DIM}]v{__version__}[/{ui.Theme.DIM}]"
        )
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Tampilkan versi AcadLabs CLI.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    AcadLabs CLI - AI-Powered Coding Assistant.
    """
    pass


# ═══════════════════════════════════════════════════════════════════════════
# Register Sub-command Groups
# ═══════════════════════════════════════════════════════════════════════════

# Auth group: acadlabs auth <command>
auth_app.info.help = (
    "Authentication & session management.\n\n"
    "Kelola login, logout, dan status akun kamu.\n\n"
    "\b\n"
    "Commands:\n"
    "  login          Login dengan email/password\n"
    "  login-google   Login dengan Google OAuth (buka browser)\n"
    "  logout         Logout dari akun\n"
    "  status         Cek status login saat ini\n"
)
app.add_typer(auth_app, name="auth")

# Config group: acadlabs config <command>
config_app.info.help = (
    "Configuration management.\n\n"
    "Setup dan kelola konfigurasi API keys, model, dan Supabase.\n\n"
    "\b\n"
    "Commands:\n"
    "  init           Setup konfigurasi awal (API keys, dll)\n"
    "  show           Tampilkan konfigurasi saat ini (keys di-mask)\n"
)
app.add_typer(config_app, name="config")

# Chat group: acadlabs chat <command>
# invoke_without_command=True is set in chat.py so 'acadlabs chat' runs 'start'
chat_app.info.help = (
    "Interactive AI chat session.\n\n"
    "Mulai sesi chat interaktif dengan AI menggunakan Agentic Loop.\n"
    "Ketik 'acadlabs chat' langsung untuk memulai.\n\n"
    "\b\n"
    "Commands:\n"
    "  start          Mulai sesi chat baru (default jika tanpa subcommand)\n\n"
    "\b\n"
    "In-Chat Slash Commands:\n"
    "  /help          Show available commands\n"
    "  /tools         List available tools\n"
    "  /status        Show token usage & cost\n"
    "  /clear         Clear chat context\n"
    "  /exit          End session\n"
)
app.add_typer(chat_app, name="chat")


# ═══════════════════════════════════════════════════════════════════════════
# Top-level Shortcut Commands
# These let users type 'acadlabs login' instead of 'acadlabs auth login'
# ═══════════════════════════════════════════════════════════════════════════

from acadlabs_cli.commands.auth import login, login_google, logout, status as auth_status

# Direct shortcuts (appear in main help)
app.command(
    name="login",
    help="Login ke akun AcadLabs dengan email dan password (shortcut: auth login).",
    hidden=False,
)(login)

app.command(
    name="login-google",
    help="Login dengan Google OAuth, akan membuka browser (shortcut: auth login-google).",
    hidden=False,
)(login_google)

app.command(
    name="logout",
    help="Logout dari akun AcadLabs (shortcut: auth logout).",
    hidden=False,
)(logout)

app.command(
    name="status",
    help="Cek status login saat ini (shortcut: auth status).",
    hidden=False,
)(auth_status)


# ═══════════════════════════════════════════════════════════════════════════
# Help Command (rich-formatted via ui module)
# ═══════════════════════════════════════════════════════════════════════════

@app.command(name="help", hidden=True)
def show_help():
    """Tampilkan bantuan lengkap tentang semua command yang tersedia."""
    console.print()

    # ── Brand Header ──
    console.print(
        f"  [{ui.Theme.ACCENT}]{ui.ICON_BRAND} AcadLabs CLI[/{ui.Theme.ACCENT}] "
        f"[{ui.Theme.DIM}]v{__version__}[/{ui.Theme.DIM}]"
        f"  [{ui.Theme.DIMMER}]AI-Powered Coding Assistant[/{ui.Theme.DIMMER}]"
    )
    console.print()

    # ── Quick Start ──
    console.print(f"  [{ui.Theme.TEXT}]Quick Start[/{ui.Theme.TEXT}]")
    console.print(f"  [{ui.Theme.BORDER}]{'─' * 44}[/{ui.Theme.BORDER}]")
    steps = [
        ("1", "acadlabs login", "Login ke akun"),
        ("2", "acadlabs config init", "Setup API keys"),
        ("3", "acadlabs chat", "Mulai chat dengan AI"),
    ]
    for num, cmd, desc in steps:
        console.print(
            f"  [{ui.Theme.DIM}]{num}.[/{ui.Theme.DIM}] "
            f"[{ui.Theme.TOOL_SAFE}]{cmd:<26}[/{ui.Theme.TOOL_SAFE}] "
            f"[{ui.Theme.DIM}]{desc}[/{ui.Theme.DIM}]"
        )
    console.print()

    # ── All Commands ──
    console.print(f"  [{ui.Theme.TEXT}]Commands[/{ui.Theme.TEXT}]")
    console.print(f"  [{ui.Theme.BORDER}]{'─' * 44}[/{ui.Theme.BORDER}]")
    
    sections = [
        ("Authentication", [
            ("acadlabs login", "Login email/password"),
            ("acadlabs login-google", "Login Google OAuth"),
            ("acadlabs logout", "Logout"),
            ("acadlabs status", "Cek status login"),
        ]),
        ("AI Chat", [
            ("acadlabs chat", "Mulai sesi chat interaktif"),
        ]),
        ("Configuration", [
            ("acadlabs config init", "Setup konfigurasi awal"),
            ("acadlabs config show", "Lihat konfigurasi"),
        ]),
    ]

    for section_name, commands in sections:
        console.print(f"\n  [{ui.Theme.AI_NAME}]{section_name}[/{ui.Theme.AI_NAME}]")
        for cmd, desc in commands:
            console.print(
                f"    [{ui.Theme.TOOL_SAFE}]{cmd:<28}[/{ui.Theme.TOOL_SAFE}] "
                f"[{ui.Theme.DIM}]{desc}[/{ui.Theme.DIM}]"
            )
    
    console.print()

    # ── In-Chat Slash Commands ──
    console.print(f"  [{ui.Theme.TEXT}]In-Chat Slash Commands[/{ui.Theme.TEXT}]")
    console.print(f"  [{ui.Theme.BORDER}]{'─' * 44}[/{ui.Theme.BORDER}]")
    
    slash_cmds = [
        ("/help", "Show available commands"),
        ("/tools", "List tools AI can use"),
        ("/status", "Token usage & cost"),
        ("/clear", "Clear chat context"),
        ("/compact", "Toggle compact output"),
        ("/exit", "End session"),
    ]
    for cmd, desc in slash_cmds:
        console.print(
            f"    [{ui.Theme.TOOL_SAFE}]{cmd:<12}[/{ui.Theme.TOOL_SAFE}] "
            f"[{ui.Theme.DIM}]{desc}[/{ui.Theme.DIM}]"
        )
    console.print()

    # ── Global Options ──
    console.print(f"  [{ui.Theme.TEXT}]Options[/{ui.Theme.TEXT}]")
    console.print(f"  [{ui.Theme.BORDER}]{'─' * 44}[/{ui.Theme.BORDER}]")
    console.print(
        f"    [{ui.Theme.TOOL_SAFE}]--help, -h   [/{ui.Theme.TOOL_SAFE}] "
        f"[{ui.Theme.DIM}]Show help for any command[/{ui.Theme.DIM}]"
    )
    console.print(
        f"    [{ui.Theme.TOOL_SAFE}]--version, -V[/{ui.Theme.TOOL_SAFE}] "
        f"[{ui.Theme.DIM}]Show version[/{ui.Theme.DIM}]"
    )
    console.print()

    # ── Resources ──
    console.print(
        f"  [{ui.Theme.DIMMER}]Web: https://acadlabs.fun[/{ui.Theme.DIMMER}]  "
        f"[{ui.Theme.DIMMER}]GitHub: github.com/Acadgacor/acadlabs-cli[/{ui.Theme.DIMMER}]"
    )
    console.print()


if __name__ == "__main__":
    app()