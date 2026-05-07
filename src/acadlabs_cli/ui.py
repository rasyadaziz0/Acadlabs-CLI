"""
AcadLabs CLI — UI Renderer

Central module untuk semua rendering terminal.
Menggunakan gaya Claude Code: clean, minimal, premium.
"""
import os
import sys
import shutil
from typing import Dict, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box


# ═══════════════════════════════════════════════════════════════════════════
# Windows UTF-8 Support
# ═══════════════════════════════════════════════════════════════════════════

def _setup_windows_console():
    """Enable UTF-8 output on Windows to support Unicode icons."""
    if os.name == "nt":
        try:
            # Try to set console output code page to UTF-8
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
            # Reconfigure stdout/stderr for UTF-8
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

_setup_windows_console()


# ═══════════════════════════════════════════════════════════════════════════
# Theme — Claude Code-inspired color palette
# ═══════════════════════════════════════════════════════════════════════════

class Theme:
    """Premium muted color palette."""
    ACCENT      = "#8B7CF6"   # soft indigo — brand
    ACCENT_DIM  = "#6C63FF"   # deeper indigo
    TEXT        = "#D4D4D8"   # zinc-300
    DIM         = "#71717A"   # zinc-500
    DIMMER      = "#52525B"   # zinc-600
    SUCCESS     = "#34D399"   # emerald-400
    WARNING     = "#FBBF24"   # amber-400
    DANGER      = "#F87171"   # red-400
    TOOL_SAFE   = "#60A5FA"   # blue-400
    TOOL_DANGER = "#FB923C"   # orange-400
    AI_NAME     = "#A78BFA"   # violet-400
    USER_NAME   = "#818CF8"   # indigo-400
    BORDER      = "#3F3F46"   # zinc-700
    BG_SUBTLE   = "#27272A"   # zinc-800


# Force Rich to use proper ANSI color output on Windows (not legacy Win32 API)
console = Console(force_terminal=True, color_system="truecolor")

# Icons — ASCII-safe versions that work on all Windows consoles (cp1252 + UTF-8)
ICON_BRAND   = "*"
ICON_ARROW   = ">"
ICON_PROMPT  = ">"
ICON_TOOL    = "~"
ICON_WRITE   = "+"
ICON_CHECK   = "+"
ICON_WARN    = "!"
ICON_DOT     = "-"
ICON_CROSS   = "x"
ICON_THINK   = "o"


# ═══════════════════════════════════════════════════════════════════════════
# Banner & Startup
# ═══════════════════════════════════════════════════════════════════════════

def render_banner(version: str, cwd: str = None, model: str = None):
    """Compact startup banner — 4 lines max."""
    if cwd is None:
        cwd = os.getcwd()
    
    # Shorten home path
    home = os.path.expanduser("~")
    display_cwd = cwd.replace(home, "~")
    
    # Shorten model name
    if model:
        short_model = model.split("/")[-1].split(":")[0]
    else:
        short_model = "default"
    
    # Get terminal width for clean border
    term_width = min(shutil.get_terminal_size().columns, 56)
    
    inner_w = term_width - 4  # padding for border chars
    
    lines = [
        f"  {ICON_BRAND} [bold {Theme.ACCENT}]AcadLabs CLI[/bold {Theme.ACCENT}]  [{Theme.DIM}]v{version}[/{Theme.DIM}]",
        f"  [{Theme.DIM}]{ICON_ARROW} {display_cwd}[/{Theme.DIM}]  [{Theme.DIMMER}]{ICON_DOT} {short_model}[/{Theme.DIMMER}]",
        "",
        f"  [{Theme.DIMMER}]Type [/{Theme.DIMMER}][{Theme.TOOL_SAFE}]/help[/{Theme.TOOL_SAFE}] [{Theme.DIMMER}]for slash commands[/{Theme.DIMMER}]",
    ]
    
    content = "\n".join(lines)
    
    console.print()
    console.print(Panel(
        content,
        border_style=Theme.BORDER,
        box=box.ROUNDED,
        padding=(0, 1),
        expand=False,
    ))
    console.print()


def render_welcome_tips():
    """First-run tips shown once."""
    tips = [
        f"[{Theme.DIM}]Tips:[/{Theme.DIM}]",
        f"  [{Theme.DIMMER}]{ICON_DOT}[/{Theme.DIMMER}] [{Theme.TEXT}]Describe your task in natural language[/{Theme.TEXT}]",
        f"  [{Theme.DIMMER}]{ICON_DOT}[/{Theme.DIMMER}] [{Theme.TEXT}]AI will read, analyze, and modify code for you[/{Theme.TEXT}]",
        f"  [{Theme.DIMMER}]{ICON_DOT}[/{Theme.DIMMER}] [{Theme.TEXT}]Dangerous actions always require your approval[/{Theme.TEXT}]",
    ]
    for tip in tips:
        console.print(tip)
    console.print()


# ═══════════════════════════════════════════════════════════════════════════
# Prompt
# ═══════════════════════════════════════════════════════════════════════════

def get_prompt_text() -> str:
    """Return the prompt prefix for input()."""
    return f"{ICON_PROMPT} "


def read_user_input() -> str:
    """Read user input with styled prompt. Returns stripped string."""
    try:
        # Print the styled prompt via Rich, then read raw input
        console.print(f"\n[{Theme.USER_NAME}]{ICON_PROMPT}[/{Theme.USER_NAME}] ", end="")
        raw = input()
        return raw.strip()
    except EOFError:
        return "/exit"


# ═══════════════════════════════════════════════════════════════════════════
# Tool Display — Compact one-liners
# ═══════════════════════════════════════════════════════════════════════════

def render_tool_call(tool_name: str, arguments: Dict, is_dangerous: bool = False):
    """Compact one-liner tool call display."""
    icon = ICON_WRITE if is_dangerous else ICON_TOOL
    color = Theme.TOOL_DANGER if is_dangerous else Theme.TOOL_SAFE
    
    # Build compact args string
    args_display = _format_args_compact(tool_name, arguments)
    
    console.print(
        f"\n  [{color}]{icon} {tool_name}[/{color}] [{Theme.DIM}]{args_display}[/{Theme.DIM}]"
    )


def render_tool_result(tool_name: str, result: str, approved: bool = True):
    """Compact, dimmed tool result."""
    if not approved:
        console.print(f"    [{Theme.DANGER}]{ICON_CROSS} blocked by user[/{Theme.DANGER}]")
        return
    
    # Truncate long results
    lines = result.strip().split("\n")
    if len(result) > 300 or len(lines) > 5:
        # Show summary
        summary = _summarize_result(tool_name, result)
        console.print(f"    [{Theme.DIM}]{ICON_ARROW} {summary}[/{Theme.DIM}]")
    else:
        # Show full result, indented and dimmed
        for line in lines[:5]:
            truncated = line[:100] + "..." if len(line) > 100 else line
            console.print(f"    [{Theme.DIMMER}]{truncated}[/{Theme.DIMMER}]")


def render_tool_confirmation(tool_name: str, arguments: Dict) -> bool:
    """Clean confirmation prompt for dangerous tools."""
    args_summary = _format_args_compact(tool_name, arguments)
    
    console.print(
        f"\n  [{Theme.WARNING}]{ICON_WARN} {tool_name}[/{Theme.WARNING}] "
        f"[{Theme.DIM}]{args_summary}[/{Theme.DIM}]"
    )
    
    try:
        console.print(f"    [{Theme.WARNING}]Allow? [y/N][/{Theme.WARNING}] ", end="")
        response = input()
        return response.strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ═══════════════════════════════════════════════════════════════════════════
# AI Response — Markdown rendered
# ═══════════════════════════════════════════════════════════════════════════

def render_ai_response(text: str):
    """Render AI response with Markdown formatting."""
    if not text:
        return
    
    console.print()
    console.print(
        f"  [{Theme.AI_NAME}]{ICON_BRAND} AcadLabs[/{Theme.AI_NAME}]"
    )
    
    # Render as Markdown
    md = Markdown(text, code_theme="monokai")
    
    # Print with left padding
    with console.capture() as capture:
        console.print(md, width=console.width - 6)
    
    rendered = capture.get()
    for line in rendered.split("\n"):
        console.print(f"  {line}", highlight=False)


def render_ai_thinking(iteration: int = None):
    """Subtle thinking indicator."""
    if iteration and iteration > 1:
        console.print(
            f"\n  [{Theme.DIMMER}]{ICON_THINK} Thinking... (iter {iteration})[/{Theme.DIMMER}]"
        )
    else:
        console.print(
            f"\n  [{Theme.DIMMER}]{ICON_THINK} Thinking...[/{Theme.DIMMER}]"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Summary — Compact one-liner
# ═══════════════════════════════════════════════════════════════════════════

def render_loop_summary(
    iterations: int,
    tools_called: int,
    blocked: int,
    errors: int,
    total_tokens: int,
    cost: float
):
    """Compact one-liner summary after agentic loop completes."""
    parts = []
    
    if iterations > 0:
        parts.append(f"{iterations} iter")
    if tools_called > 0:
        parts.append(f"{tools_called} tools")
    if blocked > 0:
        parts.append(f"[{Theme.WARNING}]{blocked} blocked[/{Theme.WARNING}]")
    if errors > 0:
        parts.append(f"[{Theme.DANGER}]{errors} errors[/{Theme.DANGER}]")
    
    # Format tokens
    if total_tokens >= 1000:
        token_str = f"~{total_tokens / 1000:.1f}k tokens"
    else:
        token_str = f"~{total_tokens} tokens"
    parts.append(token_str)
    
    if cost > 0:
        parts.append(f"${cost:.4f}")
    
    summary = " · ".join(parts)
    
    console.print(
        f"\n  [{Theme.SUCCESS}]{ICON_CHECK} Done[/{Theme.SUCCESS}] "
        f"[{Theme.DIM}]({summary})[/{Theme.DIM}]"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Slash Commands
# ═══════════════════════════════════════════════════════════════════════════

SLASH_COMMANDS = {
    "/help":    "Show this help",
    "/tools":   "List available tools",
    "/status":  "Show token usage & cost",
    "/clear":   "Clear chat context",
    "/compact": "Toggle compact output mode",
    "/exit":    "End session",
}


def render_help():
    """Render slash command help — clean table."""
    console.print()
    console.print(f"  [{Theme.TEXT}]Slash Commands[/{Theme.TEXT}]")
    console.print(f"  [{Theme.BORDER}]{'─' * 36}[/{Theme.BORDER}]")
    
    for cmd, desc in SLASH_COMMANDS.items():
        console.print(
            f"  [{Theme.TOOL_SAFE}]{cmd:<12}[/{Theme.TOOL_SAFE}] [{Theme.DIM}]{desc}[/{Theme.DIM}]"
        )
    
    console.print()
    console.print(f"  [{Theme.DIMMER}]Also: exit, quit, Ctrl+C[/{Theme.DIMMER}]")
    console.print()


def render_tools_list(tools_registry, safe_tools: set, dangerous_tools: set):
    """Render available tools list — compact."""
    console.print()
    console.print(f"  [{Theme.TEXT}]Available Tools[/{Theme.TEXT}]")
    console.print(f"  [{Theme.BORDER}]{'─' * 50}[/{Theme.BORDER}]")
    
    # Safe tools
    for tool in tools_registry:
        if tool.name in safe_tools:
            console.print(
                f"  [{Theme.TOOL_SAFE}]{ICON_TOOL} {tool.name:<24}[/{Theme.TOOL_SAFE}] "
                f"[{Theme.DIM}]{tool.description[:50]}[/{Theme.DIM}]"
            )
    
    console.print()
    
    # Dangerous tools
    for tool in tools_registry:
        if tool.name in dangerous_tools:
            console.print(
                f"  [{Theme.TOOL_DANGER}]{ICON_WRITE} {tool.name:<24}[/{Theme.TOOL_DANGER}] "
                f"[{Theme.DIM}]{tool.description[:50]}[/{Theme.DIM}]"
            )
    
    console.print()


def render_token_status_compact(
    history_tokens: int,
    context_limit: int,
    session_prompt: int,
    session_completion: int,
    cost: float,
    model: str
):
    """Compact inline token status."""
    usage_pct = (history_tokens / context_limit) * 100 if context_limit > 0 else 0
    total_session = session_prompt + session_completion
    
    # Color based on usage
    if usage_pct >= 80:
        color = Theme.DANGER
    elif usage_pct >= 60:
        color = Theme.WARNING
    else:
        color = Theme.SUCCESS
    
    short_model = model.split("/")[-1].split(":")[0]
    
    console.print()
    console.print(
        f"  [{Theme.TEXT}]Token Status[/{Theme.TEXT}]"
    )
    console.print(
        f"  [{color}]{history_tokens:,}[/{color}] [{Theme.DIM}]/ {context_limit:,} ({usage_pct:.1f}%)[/{Theme.DIM}]"
        f"  [{Theme.DIMMER}]·[/{Theme.DIMMER}]  "
        f"[{Theme.DIM}]session: {total_session:,}[/{Theme.DIM}]"
        f"  [{Theme.DIMMER}]·[/{Theme.DIMMER}]  "
        f"[{Theme.DIM}]${cost:.4f}[/{Theme.DIM}]"
        f"  [{Theme.DIMMER}]·[/{Theme.DIMMER}]  "
        f"[{Theme.DIMMER}]{short_model}[/{Theme.DIMMER}]"
    )
    console.print()


def render_token_warning_compact(
    token_count: int,
    context_limit: int,
    level: str
):
    """Compact token warning bar."""
    usage_pct = (token_count / context_limit) * 100 if context_limit > 0 else 0
    
    colors = {
        "WARNING": Theme.WARNING,
        "CRITICAL": Theme.TOOL_DANGER,
        "DANGER": Theme.DANGER,
    }
    color = colors.get(level, Theme.WARNING)
    
    console.print(
        f"\n  [{color}]{ICON_WARN} Context {level}: "
        f"{token_count:,} / {context_limit:,} ({usage_pct:.1f}%)[/{color}]"
        f"  [{Theme.DIM}]Type /clear to reset[/{Theme.DIM}]"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Status Messages
# ═══════════════════════════════════════════════════════════════════════════

def render_info(message: str):
    """Dimmed info message."""
    console.print(f"  [{Theme.DIM}]{message}[/{Theme.DIM}]")


def render_success(message: str):
    """Success message."""
    console.print(f"  [{Theme.SUCCESS}]{ICON_CHECK} {message}[/{Theme.SUCCESS}]")


def render_warning(message: str):
    """Warning message."""
    console.print(f"  [{Theme.WARNING}]{ICON_WARN} {message}[/{Theme.WARNING}]")


def render_error(message: str):
    """Error message."""
    console.print(f"  [{Theme.DANGER}]{ICON_CROSS} {message}[/{Theme.DANGER}]")


def render_context_loaded(has_changes: bool = False):
    """Compact context loading indicator."""
    console.print(f"  [{Theme.DIM}]{ICON_ARROW} Project context loaded[/{Theme.DIM}]", end="")
    if has_changes:
        console.print(f"  [{Theme.WARNING}]{ICON_DOT} uncommitted changes[/{Theme.WARNING}]")
    else:
        console.print()


def render_goodbye(total_tools: int):
    """Clean goodbye message."""
    console.print(
        f"\n  [{Theme.DIM}]Session ended[/{Theme.DIM}]"
        f"  [{Theme.DIMMER}]({total_tools} tools executed)[/{Theme.DIMMER}]"
    )
    console.print()


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _format_args_compact(tool_name: str, arguments: Dict) -> str:
    """Format tool arguments as a compact one-liner."""
    if not arguments:
        return ""
    
    # Special handling per tool
    if tool_name in ("read_file", "write_file"):
        path = arguments.get("path", "")
        return _shorten_path(path)
    
    elif tool_name == "replace_code_block":
        path = arguments.get("path", "")
        return _shorten_path(path)
    
    elif tool_name == "run_terminal_command":
        cmd = arguments.get("command", "")
        if len(cmd) > 60:
            return f'"{cmd[:57]}..."'
        return f'"{cmd}"'
    
    elif tool_name == "search_code":
        query = arguments.get("query", "")
        path = arguments.get("path", ".")
        return f'"{query}" in {path}'
    
    elif tool_name == "list_directory":
        return arguments.get("path", ".")
    
    elif tool_name == "git_diff":
        target = arguments.get("target", "")
        return target or "(all)"
    
    elif tool_name == "git_log":
        limit = arguments.get("limit", 10)
        return f"limit={limit}"
    
    else:
        # Generic: show first key-value
        items = list(arguments.items())
        if items:
            k, v = items[0]
            v_str = str(v)
            if len(v_str) > 40:
                v_str = v_str[:37] + "..."
            return f'{k}="{v_str}"'
        return ""


def _shorten_path(path: str) -> str:
    """Shorten file path for display."""
    if not path:
        return ""
    # Remove CWD prefix if present
    cwd = os.getcwd()
    if path.startswith(cwd):
        path = os.path.relpath(path, cwd)
    # Use forward slashes
    return path.replace("\\", "/")


def _summarize_result(tool_name: str, result: str) -> str:
    """Create a short summary of a tool result."""
    lines = result.strip().split("\n")
    line_count = len(lines)
    char_count = len(result)
    
    if tool_name == "read_file":
        return f"{line_count} lines read"
    elif tool_name == "list_directory":
        return f"{line_count} entries"
    elif tool_name == "search_code":
        # Count matches
        matches = sum(1 for l in lines if l.strip() and not l.startswith("---"))
        return f"{matches} matches"
    elif tool_name in ("write_file", "replace_code_block"):
        return result.split("\n")[0][:60] if result else "done"
    elif tool_name == "run_terminal_command":
        if line_count <= 2:
            return lines[0][:80]
        return f"{line_count} lines output"
    elif tool_name == "git_status":
        return f"{line_count} lines"
    elif tool_name == "git_diff":
        additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
        return f"+{additions} -{deletions}"
    elif tool_name == "git_log":
        commits = sum(1 for l in lines if l.startswith("commit"))
        return f"{commits} commits"
    else:
        return f"{line_count} lines"
