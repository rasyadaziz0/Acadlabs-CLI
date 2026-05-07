"""
Agentic Loop - ReAct Pattern (Reason, Act, Observe)

Implementasi perulangan mandiri AI yang memungkinkan AI untuk:
1. REASON: Menganalisis situasi dan memutuskan aksi
2. ACT: Memanggil tools untuk melakukan aksi
3. OBSERVE: Mengamati hasil dan memutuskan langkah selanjutnya

Loop berlanjut sampai AI menyatakan tugas selesai atau mencapai batas iterasi.

Display: Claude Code-style compact output via ui module.
"""
import json
from typing import List, Dict, Any, Optional, Tuple, Callable

from rich.console import Console

# Import config
from acadlabs_cli.core.agent.config import LoopStatus, LoopState, AgenticConfig

# Import token manager
from acadlabs_cli.core.token import (
    TokenManager,
    estimate_tokens,
    estimate_history_tokens,
    create_token_manager
)

# Import UI renderer
from acadlabs_cli import ui

console = Console()


class AgenticLoop:
    """
    Agentic Loop dengan pola ReAct.
    
    Flow:
    1. User memberikan task
    2. AI REASON: Menganalisis dan memutuskan aksi
    3. AI ACT: Memanggil tools (melewati security layers)
    4. AI OBSERVE: Melihat hasil dan memutuskan lanjut atau selesai
    5. Jika belum selesai, kembali ke step 2
    6. Jika selesai, return hasil ke user
    """
    
    def __init__(
        self,
        config: AgenticConfig = None,
        secure_executor=None,
        tool_registry=None,
        token_manager: TokenManager = None
    ):
        self.config = config or AgenticConfig()
        self.state = LoopState()
        
        # Import secure executor for dangerous operations
        if secure_executor is None:
            from acadlabs_cli.utils.security import secure_executor as se
            secure_executor = se
        self.secure_executor = secure_executor
        
        # Import tool registry
        if tool_registry is None:
            from acadlabs_cli.tools import (
                TOOLS_REGISTRY,
                execute_tool,
                is_dangerous_tool,
                get_tool_by_name
            )
            self.tool_registry = TOOLS_REGISTRY
            self.execute_tool_fn = execute_tool
            self.is_dangerous_tool_fn = is_dangerous_tool
            self.get_tool_by_name_fn = get_tool_by_name
        else:
            self.tool_registry = tool_registry
        
        # Token manager for tracking and warnings
        if token_manager is None:
            self.token_manager = create_token_manager()
        else:
            self.token_manager = token_manager
        
        # Callbacks
        self.on_iteration_start: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_result: Optional[Callable] = None
        self.on_iteration_end: Optional[Callable] = None
        self.on_token_warning: Optional[Callable] = None
    
    def run(
        self,
        user_message: str,
        ask_ai_func: Callable,
        history: List[Dict] = None,
        tools_schema: List[Dict] = None
    ) -> Tuple[str, LoopState, List[Dict]]:
        """
        Menjalankan agentic loop.
        
        Args:
            user_message: Pesan dari user
            ask_ai_func: Fungsi untuk memanggil AI (ask_ai_with_tools)
            history: Chat history
            tools_schema: Schema tools untuk AI
        
        Returns:
            (final_response, final_state, execution_log)
        """
        self.state = LoopState()  # Reset state
        execution_log = []
        
        if history is None:
            history = []
        
        current_message = user_message
        current_tool_calls = None
        
        while not self.state.is_complete:
            self.state.iteration += 1
            
            # Check max iterations
            if self.state.iteration > self.config.max_iterations:
                ui.render_warning(f"Max iterations reached ({self.config.max_iterations})")
                self.state.is_complete = True
                break
            
            # ── Token Check ──
            if self.config.enable_token_warnings:
                current_tokens = estimate_history_tokens(history) if history else 0
                self.state.total_tokens = current_tokens
                
                if current_tokens >= self.config.token_warning_threshold:
                    self._handle_token_warning(current_tokens)
                    
                    if self.on_token_warning:
                        should_continue = self.on_token_warning(current_tokens, self.token_manager)
                        if not should_continue:
                            ui.render_info("Session stopped by user.")
                            self.state.is_complete = True
                            break
            
            # Callback: iteration start
            if self.on_iteration_start:
                self.on_iteration_start(self.state)
            
            # ── Thinking indicator ──
            ui.render_ai_thinking(self.state.iteration if self.state.iteration > 1 else None)
            
            # ── STEP 1: REASON ──
            ai_response, tool_calls = ask_ai_func(
                current_message,
                history,
                tools_schema
            )
            
            # Track tokens for this iteration
            prompt_tokens = estimate_tokens(current_message) + estimate_history_tokens(history[-3:] if history else [])
            completion_tokens = estimate_tokens(ai_response or "")
            self.state.prompt_tokens += prompt_tokens
            self.state.completion_tokens += completion_tokens
            self.state.total_tokens = self.state.prompt_tokens + self.state.completion_tokens
            
            # Update token manager
            self.token_manager.add_usage(prompt_tokens, completion_tokens, len(tool_calls) if tool_calls else 0)
            
            self.state.last_response = ai_response or ""
            
            # ── STEP 2: ACT ──
            if tool_calls:
                self.state.tools_this_iteration = len(tool_calls)
                
                # Check max tools per iteration
                if self.state.tools_this_iteration > self.config.max_tools_per_iteration:
                    ui.render_info(f"Limiting to {self.config.max_tools_per_iteration} tools per iteration")
                    tool_calls = tool_calls[:self.config.max_tools_per_iteration]
                
                # Execute tools
                tool_results, tool_log = self._execute_tools_with_security(tool_calls)
                execution_log.extend(tool_log)
                self.state.total_tools_called += len(tool_log)
                
                # Check blocked
                blocked_count = sum(1 for t in tool_log if not t.get("approved", True))
                if blocked_count > 0:
                    self.state.blocked_actions.extend([
                        t["name"] for t in tool_log if not t.get("approved", True)
                    ])
                
                # ── STEP 3: OBSERVE ──
                current_message = self._build_observation_message(tool_calls, tool_results)
                
                # Callback: iteration end
                if self.on_iteration_end:
                    self.on_iteration_end(self.state, tool_log)
            
            else:
                # No tool calls — AI gave final answer
                self.state.is_complete = True
        
        # ── Compact Summary ──
        cost = self.token_manager.estimate_cost()
        ui.render_loop_summary(
            iterations=self.state.iteration,
            tools_called=self.state.total_tools_called,
            blocked=len(self.state.blocked_actions),
            errors=len(self.state.errors),
            total_tokens=self.state.total_tokens,
            cost=cost,
        )
        
        final_response = self.state.last_response
        return final_response, self.state, execution_log
    
    def _execute_tools_with_security(self, tool_calls: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Eksekusi tools dengan integrasi security layers.
        
        Safe tools: Langsung dieksekusi
        Dangerous tools: Melewati 5-layer security system
        """
        results = []
        execution_log = []
        
        for tc in tool_calls:
            tool_id = tc["id"]
            tool_name = tc["name"]
            arguments = tc["arguments"]
            
            # Check if dangerous
            is_dangerous = self.is_dangerous_tool_fn(tool_name)
            
            # ── Compact Tool Call Display ──
            ui.render_tool_call(tool_name, arguments, is_dangerous)
            
            if is_dangerous:
                # ── Dangerous Tool — Security Layers ──
                result, approved = self._execute_dangerous_tool(tool_name, arguments)
            else:
                # ── Safe Tool ──
                if self.config.auto_approve_safe:
                    result = self.execute_tool_fn(tool_name, arguments)
                    approved = True
                else:
                    approved = ui.render_tool_confirmation(tool_name, arguments)
                    if approved:
                        result = self.execute_tool_fn(tool_name, arguments)
                    else:
                        result = f"Tool '{tool_name}' blocked by user."
            
            results.append(result)
            
            # Log
            execution_log.append({
                "id": tool_id,
                "name": tool_name,
                "arguments": arguments,
                "result": result[:500] if len(result) > 500 else result,
                "approved": approved,
                "dangerous": is_dangerous,
                "iteration": self.state.iteration
            })
            
            # ── Compact Result Display ──
            ui.render_tool_result(tool_name, result, approved)
        
        return results, execution_log
    
    def _execute_dangerous_tool(self, tool_name: str, arguments: Dict) -> Tuple[str, bool]:
        """
        Eksekusi dangerous tool melalui security layers.
        
        Integrasi dengan Layer 1-5:
        - Layer 1: Human confirmation (via SecureExecutor)
        - Layer 2: Whitelist validation
        - Layer 3: Anti-injection
        - Layer 4: Path locking
        - Layer 5: Containerization (opsional)
        """
        try:
            # Special handling untuk write_file
            if tool_name == "write_file":
                path = arguments.get("path", "")
                content = arguments.get("content", "")
                mode = arguments.get("mode", "w")
                
                # Gunakan secure_executor yang sudah terintegrasi dengan Layer 1-4
                self.secure_executor.write_file(path, content, mode)
                return f"Success: File written to '{path}'", True
            
            # Special handling untuk replace_code_block
            elif tool_name == "replace_code_block":
                path = arguments.get("path", "")
                old_code = arguments.get("old_code", "")
                new_code = arguments.get("new_code", "")
                replace_all = arguments.get("replace_all", False)
                
                # Baca file dulu
                import os
                if not os.path.exists(path):
                    return f"Error: File not found: '{path}'", True
                
                with open(path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                if old_code not in file_content:
                    return f"Error: old_code tidak ditemukan di file '{path}'", True
                
                # Compact confirmation
                approved = ui.render_tool_confirmation(tool_name, {
                    "path": path,
                    "old_code": old_code[:80] + "..." if len(old_code) > 80 else old_code,
                    "new_code": new_code[:80] + "..." if len(new_code) > 80 else new_code,
                })
                
                if approved:
                    if replace_all:
                        new_content = file_content.replace(old_code, new_code)
                    else:
                        new_content = file_content.replace(old_code, new_code, 1)
                    
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    return f"Success: Code replaced in '{path}'", True
                else:
                    return f"Tool '{tool_name}' blocked by user.", False
            
            # Special handling untuk run_terminal_command
            elif tool_name == "run_terminal_command":
                command = arguments.get("command", "")
                timeout = arguments.get("timeout", 30)
                
                try:
                    result = self.secure_executor.run_command(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                    output = result.stdout or result.stderr or "(no output)"
                    return output, True
                except Exception as e:
                    if "ditolak" in str(e) or "SecurityViolation" in str(e):
                        return f"Command blocked: {command}", False
                    return f"Error: {e}", True
            
            # Default: confirm + execute
            else:
                approved = ui.render_tool_confirmation(tool_name, arguments)
                if approved:
                    result = self.execute_tool_fn(tool_name, arguments)
                    return result, True
                else:
                    return f"Tool '{tool_name}' blocked by user.", False
        
        except Exception as e:
            error_msg = str(e)
            self.state.errors.append(error_msg)
            
            if "SecurityViolation" in error_msg or "ditolak" in error_msg:
                return f"Blocked by security: {error_msg}", False
            
            return f"Error: {error_msg}", True
    
    def _build_observation_message(self, tool_calls: List[Dict], tool_results: List[str]) -> str:
        """Build pesan observasi untuk dikirim ke AI"""
        observations = []
        
        for tc, result in zip(tool_calls, tool_results):
            tool_name = tc["name"]
            observations.append(f"[Tool: {tool_name}]\nResult: {result}")
        
        return "Berikut hasil eksekusi tools:\n\n" + "\n\n".join(observations)
    
    def _handle_token_warning(self, current_tokens: int):
        """Handle token warning with compact display."""
        # Determine level
        if current_tokens >= self.token_manager.danger_threshold:
            level = "DANGER"
        elif current_tokens >= self.token_manager.critical_threshold:
            level = "CRITICAL"
        else:
            level = "WARNING"
        
        ui.render_token_warning_compact(
            current_tokens,
            self.token_manager.context_limit,
            level
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_agentic_loop(
    max_iterations: int = 15,
    auto_approve_safe: bool = True,
    auto_approve_dangerous: bool = False,
    verbose: bool = True
) -> AgenticLoop:
    """Factory function untuk membuat AgenticLoop dengan konfigurasi custom"""
    config = AgenticConfig(
        max_iterations=max_iterations,
        auto_approve_safe=auto_approve_safe,
        auto_approve_dangerous=auto_approve_dangerous,
        verbose=verbose
    )
    return AgenticLoop(config=config)


# Default instance
agentic_loop = AgenticLoop()
