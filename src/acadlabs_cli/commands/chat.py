"""
Chat Commands

Command untuk sesi chat interaktif dengan AI + Agentic Loop.
Redesigned with Claude Code-style interface.
"""
import uuid
from datetime import datetime, timezone

import typer
from rich.console import Console

from acadlabs_cli.client.supabase import save_chat_to_db, save_message_to_db, supabase
from acadlabs_cli.client.openrouter import ask_ai_with_tools, openrouter_client
from acadlabs_cli.tools import get_tools_schema, SAFE_TOOLS, DANGEROUS_TOOLS, get_project_context, git_status
from acadlabs_cli.core.agent import AgenticLoop, AgenticConfig, create_agentic_loop
from acadlabs_cli.core.token import (
    TokenManager,
    create_token_manager,
    estimate_history_tokens,
    check_and_prompt_clear
)
from acadlabs_cli import __version__
from acadlabs_cli import ui

console = Console()
app = typer.Typer(
    name="chat",
    help="Interactive AI chat session dengan Agentic Loop.",
    invoke_without_command=True,
)


@app.callback()
def chat_callback(ctx: typer.Context):
    """
    Interactive AI chat session.

    Ketik 'acadlabs chat' untuk langsung memulai sesi chat,
    atau 'acadlabs chat start' untuk hasil yang sama.
    """
    # If no subcommand was given, run 'start' automatically
    if ctx.invoked_subcommand is None:
        start()

# Agentic Loop dengan konfigurasi
agentic_config = AgenticConfig(
    max_iterations=15,
    max_tools_per_iteration=5,
    auto_approve_safe=True,
    auto_approve_dangerous=False,  # Dangerous tools WAJIB konfirmasi
    show_thinking=True,
    verbose=True
)
agentic_loop = create_agentic_loop(
    max_iterations=15,
    auto_approve_safe=True,
    auto_approve_dangerous=False,
    verbose=True
)
tools_schema = get_tools_schema()

# Token manager untuk tracking dan warning
token_manager = create_token_manager()


@app.command()
def start():
    """Mulai sesi chat interaktif dengan AI + Agentic Loop (ReAct Pattern).

    AI akan melakukan reasoning mandiri, memanggil tools, dan mengobservasi
    hasil secara otomatis sampai task selesai.
    """
    # Cek session login
    try:
        user = supabase.auth.get_user()
        if not user:
            ui.render_warning("Kamu belum login. Jalankan 'acadlabs login' dulu.")
            return
        user_id = user.user.id
    except Exception:
        ui.render_error("Session expired. Jalankan 'acadlabs login' lagi.")
        return

    # Generate ID chat session
    chat_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # ── Compact Banner ──
    model_name = openrouter_client.default_model
    ui.render_banner(
        version=__version__,
        model=model_name,
    )
    
    # ── Auto Context Injection ──
    project_context = get_project_context(max_depth=2)
    git_changes = git_status()
    
    system_context = f"""[SYSTEM CONTEXT - Otomatis dimuat]
Kamu sedang bekerja di project berikut:

{project_context}

Perubahan terakhir (git status):
{git_changes}

[END SYSTEM CONTEXT]

PENTING: Kamu sudah tahu konteks project ini. Jangan tanya user tentang struktur project kecuali perlu detail lebih lanjut. User mungkin baru saja memodifikasi file yang ditampilkan di git status di atas.

FORMAT RESPONSE: Gunakan Markdown formatting (bold, code blocks, lists, headers) untuk membuat response lebih readable.
"""
    
    chat_history = [{"role": "system", "content": system_context}]
    
    # Compact context loaded message
    has_changes = "Modified files" in git_changes or "Working tree clean" not in git_changes
    ui.render_context_loaded(has_changes=has_changes)
    
    chat_title = None
    chat_saved = False
    total_tools_executed = 0
    session_prompt_tokens = 0
    session_completion_tokens = 0
    compact_mode = False  # Toggle with /compact

    while True:
        try:
            # ── Clean Prompt ──
            prompt = ui.read_user_input()
            
            if not prompt:
                continue
            
            # ── Slash Commands ──
            if prompt.startswith("/") or prompt.lower() in ("exit", "quit", "keluar"):
                handled = _handle_slash_command(
                    prompt,
                    token_manager,
                    chat_history,
                    system_context,
                    session_prompt_tokens,
                    session_completion_tokens,
                    total_tools_executed,
                    compact_mode,
                )
                
                if handled == "exit":
                    ui.render_goodbye(total_tools_executed)
                    break
                elif handled == "clear":
                    chat_history = [{"role": "system", "content": system_context}]
                    token_manager.reset()
                    session_prompt_tokens = 0
                    session_completion_tokens = 0
                    ui.render_success("Context cleared. Fresh start.")
                    continue
                elif handled == "compact_toggle":
                    compact_mode = not compact_mode
                    state = "on" if compact_mode else "off"
                    ui.render_info(f"Compact mode: {state}")
                    continue
                elif handled == "handled":
                    continue
                # If handled is None, treat as normal message (not a command)

            # Set judul chat dari pesan pertama
            if chat_title is None:
                chat_title = prompt[:50] + ("..." if len(prompt) > 50 else "")
                chat_saved = save_chat_to_db(chat_id, user_id, chat_title, now, message=prompt)
                if not chat_saved:
                    ui.render_warning("Gagal menyimpan chat ke database")

            # ── Token Check ──
            current_tokens = estimate_history_tokens(chat_history)
            if current_tokens >= token_manager.warning_threshold:
                should_clear, new_history = check_and_prompt_clear(chat_history, token_manager)
                if should_clear:
                    chat_history = new_history
                    if not chat_history:
                        chat_history = [{"role": "system", "content": system_context}]
                    ui.render_success("Context cleared. Melanjutkan dengan fresh context.")
            
            # ── Agentic Loop ──
            final_response, loop_state, execution_log = agentic_loop.run(
                user_message=prompt,
                ask_ai_func=ask_ai_with_tools,
                history=chat_history,
                tools_schema=tools_schema
            )
            
            # Update totals
            total_tools_executed += loop_state.total_tools_called
            session_prompt_tokens += loop_state.prompt_tokens
            session_completion_tokens += loop_state.completion_tokens
            
            # ── Render AI Response with Markdown ──
            if final_response:
                ui.render_ai_response(final_response)
            
            # Update history
            chat_history.append({"role": "user", "content": prompt})
            chat_history.append({"role": "assistant", "content": final_response or "(task completed)"})
            
            # Simpan ke database
            if chat_saved:
                save_message_to_db(str(uuid.uuid4()), "user", prompt, chat_id, user_id, now)
                save_message_to_db(str(uuid.uuid4()), "assistant", final_response or "(completed)", chat_id, user_id, now)

        except KeyboardInterrupt:
            console.print(f"\n  [{ui.Theme.DIM}]Interrupted. Type /exit to end session.[/{ui.Theme.DIM}]")
            continue


def _handle_slash_command(
    prompt: str,
    token_manager: TokenManager,
    chat_history: list,
    system_context: str,
    session_prompt: int,
    session_completion: int,
    total_tools: int,
    compact_mode: bool,
) -> str:
    """Handle slash commands. Returns action string or None if not a command."""
    
    cmd = prompt.strip().lower()
    
    # Exit commands
    if cmd in ("/exit", "/quit", "exit", "quit", "keluar"):
        return "exit"
    
    # Help
    if cmd == "/help":
        ui.render_help()
        return "handled"
    
    # Tools list
    if cmd in ("/tools", "tools"):
        _show_available_tools()
        return "handled"
    
    # Token status
    if cmd in ("/status", "/tokens", "tokens"):
        _show_token_status_compact(
            token_manager, chat_history, session_prompt, session_completion
        )
        return "handled"
    
    # Clear
    if cmd in ("/clear", "clear"):
        return "clear"
    
    # Compact toggle
    if cmd == "/compact":
        return "compact_toggle"
    
    # Unknown slash command
    if cmd.startswith("/"):
        ui.render_warning(f"Unknown command: {cmd}. Type /help for commands.")
        return "handled"
    
    return None  # Not a command, treat as normal message


def _show_token_status_compact(
    token_manager: TokenManager,
    chat_history: list,
    session_prompt: int,
    session_completion: int
):
    """Show compact token status."""
    history_tokens = estimate_history_tokens(chat_history)
    cost = token_manager.estimate_cost()
    
    ui.render_token_status_compact(
        history_tokens=history_tokens,
        context_limit=token_manager.context_limit,
        session_prompt=session_prompt,
        session_completion=session_completion,
        cost=cost,
        model=token_manager.model,
    )


def _show_available_tools():
    """Show available tools list — compact."""
    from acadlabs_cli.tools import TOOLS_REGISTRY
    
    ui.render_tools_list(TOOLS_REGISTRY, SAFE_TOOLS, DANGEROUS_TOOLS)
