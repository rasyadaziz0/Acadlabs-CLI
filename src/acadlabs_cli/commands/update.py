"""
Acadlabs CLI — Self-Update Command

Menjalankan `acadlabs update` untuk update ke versi terbaru dari GitHub.
"""
import subprocess
import sys
import shutil

import typer
from rich.console import Console

from acadlabs_cli import __version__
from acadlabs_cli import ui

console = Console(force_terminal=True, color_system="truecolor")

REPO_URL = "https://github.com/Acadgacor/acadlabs-cli.git"


def _get_install_method() -> str:
    """Detect whether acadlabs was installed via pipx or pip."""
    if shutil.which("pipx"):
        # Check if acadlabs lives inside a pipx venv
        try:
            result = subprocess.run(
                ["pipx", "list", "--short"],
                capture_output=True, text=True, timeout=15,
            )
            if "acadlabs" in result.stdout.lower():
                return "pipx"
        except Exception:
            pass
    return "pip"


def _run_update(method: str) -> bool:
    """Execute the actual update command. Returns True on success."""
    if method == "pipx":
        cmd = ["pipx", "upgrade", "acadlabs-cli"]
        # pipx upgrade may not work for git installs; use reinstall
        cmd = [
            "pipx", "install",
            f"git+{REPO_URL}",
            "--force",
        ]
    else:
        cmd = [
            sys.executable, "-m", "pip", "install",
            f"git+{REPO_URL}",
            "--force-reinstall",
            "--quiet",
        ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def _get_new_version() -> str:
    """Get the version of the freshly installed package."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "acadlabs_cli", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        # Try importlib as fallback
    except Exception:
        pass

    # More reliable: read from importlib.metadata
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version("acadlabs-cli")
    except Exception:
        return "unknown"


def update(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinstall meskipun versi sama.",
    ),
):
    """Update AcadLabs CLI ke versi terbaru dari GitHub."""
    console.print()

    current_version = __version__

    console.print(
        f"  [{ui.Theme.ACCENT}]{ui.ICON_BRAND} AcadLabs CLI Update[/{ui.Theme.ACCENT}]"
    )
    console.print(
        f"  [{ui.Theme.DIM}]Current version: v{current_version}[/{ui.Theme.DIM}]"
    )
    console.print()

    # Detect install method
    method = _get_install_method()
    console.print(
        f"  [{ui.Theme.DIM}]{ui.ICON_ARROW} Using {method} to update...[/{ui.Theme.DIM}]"
    )

    # Run update with spinner
    with console.status(
        f"  [{ui.Theme.DIMMER}]Downloading latest version...[/{ui.Theme.DIMMER}]",
        spinner="dots",
        spinner_style=ui.Theme.ACCENT,
    ):
        success = _run_update(method)

    if success:
        new_version = _get_new_version()

        if new_version != current_version:
            console.print(
                f"\n  [{ui.Theme.SUCCESS}]{ui.ICON_CHECK} Updated![/{ui.Theme.SUCCESS}] "
                f"[{ui.Theme.DIM}]v{current_version} -> v{new_version}[/{ui.Theme.DIM}]"
            )
        else:
            console.print(
                f"\n  [{ui.Theme.SUCCESS}]{ui.ICON_CHECK} Already up to date[/{ui.Theme.SUCCESS}] "
                f"[{ui.Theme.DIM}](v{current_version})[/{ui.Theme.DIM}]"
            )

        console.print(
            f"  [{ui.Theme.DIMMER}]Restart your terminal to use the new version.[/{ui.Theme.DIMMER}]"
        )
    else:
        console.print(
            f"\n  [{ui.Theme.DANGER}]{ui.ICON_CROSS} Update failed![/{ui.Theme.DANGER}]"
        )
        console.print(
            f"  [{ui.Theme.DIM}]Try manually:[/{ui.Theme.DIM}]"
        )
        console.print(
            f"  [{ui.Theme.TOOL_SAFE}]pip install git+{REPO_URL} --force-reinstall[/{ui.Theme.TOOL_SAFE}]"
        )

    console.print()
