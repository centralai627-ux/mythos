"""
Mythos Agent
============
The orchestrator. Wires UI + Brain + Executor + Vision + KeyManager.
Runs the REPL loop, handles slash commands, executes AI-emitted actions.
"""
from __future__ import annotations
import os
import sys
import re
import time
from typing import Optional, Dict, Any, List

from rich.text import Text

from .config import config
from .key_manager import KeyManager
from .api_client import MythosAPI
from .executor import ShellExecutor, ExecResult
from .ai_brain import MythosBrain
from .vision import MythosVision, IMAGE_EXTS
from .tools import ToolRegistry
from .ui import MythosUI
from .commands import CommandRegistry
from . import memory


class MythosAgent:
    """Top-level Mythos orchestrator."""

    def __init__(self) -> None:
        self.cfg = config
        # Build subsystems.
        self.keys = KeyManager(
            self.cfg.openrouter_keys, self.cfg.zai_keys, self.cfg.notify_rolling
        )
        self.api = MythosAPI(self.keys)
        self.executor = ShellExecutor(cwd=os.getcwd())
        # Tool registry — wires executor + interactive UI hooks.
        self.tools = ToolRegistry(
            self.executor,
            ui_hook=self._ask_user_prompt,
            choice_hook=self._ask_choice_prompt,
            confirm_hook=self._ask_confirm_prompt,
            cwd=os.getcwd(),
        )
        self.brain = MythosBrain(
            self.api, tools=self.tools,
            on_tool=self._on_tool_call, on_observation=self._on_observation,
        )
        self.vision = MythosVision(self.api)
        self.ui = MythosUI()
        self.commands = CommandRegistry(self)
        self.running = True
        self.verbose = False
        self.debug = False
        self.cwd = os.getcwd()

        # Initialize memory system - try to continue last conversation
        self.conversation_id = self._load_or_create_conversation()
        self.brain.set_conversation(self.conversation_id)
        
        # Load relevant facts from past conversations
        self._load_relevant_context()

    def _load_or_create_conversation(self) -> str:
        """Load last conversation or create new one."""
        try:
            # Try to get recent conversations
            conversations = memory.get_conversations(limit=5)
            
            if conversations:
                # Load the most recent conversation
                last_conv = conversations[0]
                conv_id = last_conv["id"]
                
                # Check if it's recent (within last 24 hours)
                from datetime import datetime, timedelta
                updated = datetime.fromisoformat(last_conv["updated_at"])
                if datetime.now() - updated < timedelta(hours=24):
                    self.ui.info(f"Continuing conversation: {last_conv['title']}")
                    return conv_id
            
            # Create new conversation if no recent one
            return memory.create_conversation(
                title=f"Session {time.strftime('%Y-%m-%d %H:%M')}",
                model=self.brain.current_model
            )
        except Exception:
            # Fallback to new conversation
            return memory.create_conversation(
                title=f"Session {time.strftime('%Y-%m-%d %H:%M')}",
                model=self.brain.current_model
            )

    def _load_relevant_context(self):
        """Load relevant facts from past conversations."""
        try:
            # Get recent facts
            facts = memory.search_facts("", limit=10)
            if facts:
                # Add facts to brain context
                context = "Relevant information from past conversations:\n"
                for fact in facts:
                    context += f"- {fact['content']}\n"
                
                self.brain.history.append({
                    "role": "system",
                    "content": context
                })
        except Exception:
            pass  # Silently fail if memory not available

    # ----------------------- Tool-loop UI callbacks ----------------------- #
    def _on_tool_call(self, name: str, args: Dict[str, Any], step: int) -> None:
        """Show tool execution indicator."""
        self.ui.tool_executing(name, step, args)

    def _on_observation(self, output: str, ok: bool, step: int) -> None:
        """Show tool result indicator."""
        icon = "\u2713" if ok else "\u2717"
        style = "ok" if ok else "err"
        preview = output[:100].replace("\n", " ") + ("..." if len(output) > 100 else "")
        self.console.print(Text.assemble(
            (f"    {icon} ", style),
            (f"#{step} ", style),
            (preview, "glass.dim"),
        ))

    @property
    def console(self):
        return self.ui.console

    # ----------------------- Interactive UI hooks ----------------------- #
    def _ask_user_prompt(self, question: str) -> str:
        """UI hook for the ask_user tool (free-text)."""
        return self.ui.ask_question(question)

    def _ask_choice_prompt(self, question: str, options: List[str]) -> Optional[int]:
        """UI hook for the ask_choice tool (multiple-choice)."""
        return self.ui.ask_choice(question, options)

    def _ask_confirm_prompt(self, question: str) -> bool:
        """UI hook for the ask_confirm tool (yes/no)."""
        return self.ui.ask_confirm(question)

    # ----------------------- Lifecycle ----------------------- #
    def start(self) -> None:
        """Boot screen then REPL loop."""
        self.ui.boot_screen(
            version="1.0.0",
            keys_alive=self.keys.openrouter.alive_count(),
            model=self.brain.current_model,
        )
        self.ui.success("Mythos Glasswing online. Tools armed. Type /help for commands.")
        self.ui.info("Tip: ask anything — Mythos will verify with tools before answering.")
        self._loop()

    def stop(self) -> None:
        self.running = False

    # ----------------------- REPL ----------------------- #
    def _loop(self) -> None:
        while self.running:
            try:
                line = self.ui.prompt(self.cwd)
            except KeyboardInterrupt:
                self.ui.warn("Interrupted. Type /exit to quit.")
                continue

            if not line:
                continue

            if line.startswith("/"):
                self._handle_slash(line)
                continue

            # Natural-language request -> AI.
            self._process_request(line)

    # ----------------------- Slash commands ----------------------- #
    def _handle_slash(self, line: str) -> None:
        """Delegate to the command registry for high-precision execution."""
        self.commands.execute(line)

    # ----------------------- AI request flow ----------------------- #
    def _process_request(self, user_text: str) -> None:
        # Sync cwd into executor + tools (in case /cd changed it).
        self.executor.cwd = self.cwd
        self.tools.cwd = self.cwd

        # Auto-detect image attachments and route to vision model.
        image_path, question = self._detect_image_attachment(user_text)
        if image_path:
            self._analyze_image_with_context(image_path, question)
            return

        # Show thinking indicator with model info.
        self.ui.ai_thinking("Processing", self.brain.current_model)

        # Run the agentic loop with visible tool execution.
        intent, steps = self.brain.run_with_tools(user_text)

        # Save important facts to memory for future reference
        self._extract_and_save_facts(user_text, intent.text)

        # Show completion indicator.
        self.ui.response_complete(
            model=self.brain.current_model,
            tools_used=steps,
        )

        # Show the final answer.
        self.ui.assistant(intent.text, model=self.brain.current_model,
                          tools_used=steps)

        # Execute any remaining direct shell/file actions emitted by the AI.
        if intent.has_actions:
            self.ui.divider("EXECUTING ACTIONS")
            for path, content in intent.file_blocks:
                self._write_file(path, content)
            for shell, command in intent.shell_blocks:
                self._exec_and_show(command, shell=shell)
            self.ui.divider()

    def _extract_and_save_facts(self, user_text: str, response: str):
        """Extract and save important facts from conversation."""
        try:
            # Save user preferences
            preference_keywords = ["prefer", "like", "want", "need", "always", "never"]
            for keyword in preference_keywords:
                if keyword in user_text.lower():
                    # Extract the preference
                    memory.add_fact(f"User preference: {user_text[:200]}", "conversation")
                    break
            
            # Save important information
            important_keywords = ["project", "name", "email", "path", "directory", "password"]
            for keyword in important_keywords:
                if keyword in user_text.lower():
                    memory.add_fact(f"User info: {user_text[:200]}", "conversation")
                    break
        except Exception:
            pass  # Silently fail

    # ----------------------- Action execution ----------------------- #
    def _write_file(self, path: str, content: str) -> None:
        full = path if os.path.isabs(path) else os.path.join(self.cwd, path)
        ok = self.executor.atomic_write(full, content)
        if ok:
            n_lines = content.count("\n") + (1 if content else 0)
            n_bytes = len(content.encode("utf-8"))
            self.ui.file_written(full, n_lines, n_bytes)
        else:
            self.ui.error(f"Failed to write: {full}")

    def _exec_and_show(self, command: str, shell: Optional[str]) -> None:
        if not command.strip():
            self.ui.warn("Empty command.")
            return
        result = self.executor.run(command, shell=shell, cwd=self.cwd)
        self.ui.shell_output(result)

    def _read_file(self, path: str) -> None:
        full = path if os.path.isabs(path) else os.path.join(self.cwd, path)
        content = self.executor.safe_read(full)
        if content is None:
            self.ui.error(f"Cannot read: {full}")
            return
        # Feed into brain context as a system note.
        self.brain.history.append({
            "role": "system",
            "content": f"File contents of {path}:\n```\n{content}\n```",
        })
        self.ui.success(f"Loaded {len(content):,} chars from {full} into context.")

    def _analyze_image(self, path: str) -> None:
        if not path:
            self.ui.error("Usage: /image <path> [question]")
            return
        # Allow "path question..." form.
        bits = path.split(maxsplit=1)
        img_path = bits[0]
        question = bits[1] if len(bits) > 1 else "Describe this in detail."
        full = img_path if os.path.isabs(img_path) else os.path.join(self.cwd, img_path)
        self.ui.spinner("analyzing via Mythos-Vision...", duration=0.1)
        result = self.vision.analyze_file(full, question)
        self.ui.assistant(result, model="mythos-vision")

    def _detect_image_attachment(self, text: str) -> tuple:
        """
        Detect image/file paths in user input.
        Returns (file_path, question) or (None, None) if no file found.
        
        Supported patterns:
        - Direct path: "analyze this image.png"
        - Quoted path: "look at 'my screenshot.jpg'"
        - Path with question: "what is in photo.png?"
        - PDF/DOCX files: "read this document.pdf"
        """
        # All supported extensions
        all_exts = r"(?:png|jpg|jpeg|gif|webp|bmp|pdf|docx|doc|xlsx|xls|pptx|ppt|txt|md|csv|json|html|htm)"
        
        # Pattern 1: Quoted path
        quoted = re.search(rf"['\"]([^'\"]+\.{all_exts})['\"]", text, re.IGNORECASE)
        if quoted:
            file_path = quoted.group(1)
            question = text[:quoted.start()].strip() + " " + text[quoted.end():].strip()
            return (file_path, question.strip() or "Describe this in detail.")
        
        # Pattern 2: Unquoted path (word ending with supported extension)
        unquoted = re.search(rf'(?:^|\s)(\S+\.{all_exts})(?:\s|$|\.|\?)', text, re.IGNORECASE)
        if unquoted:
            file_path = unquoted.group(1)
            # Check if file exists
            full_path = file_path if os.path.isabs(file_path) else os.path.join(self.cwd, file_path)
            if os.path.isfile(full_path):
                question = text[:unquoted.start()].strip() + " " + text[unquoted.end():].strip()
                return (file_path, question.strip() or "Describe this in detail.")
        
        return (None, None)

    def _analyze_image_with_context(self, image_path: str, question: str) -> None:
        """Analyze image/file with vision model and show result with context."""
        full = image_path if os.path.isabs(image_path) else os.path.join(self.cwd, image_path)
        
        # Verify file exists
        if not os.path.isfile(full):
            self.ui.error(f"File not found: {full}")
            return
        
        # Check file extension
        ext = os.path.splitext(full)[1].lower()
        all_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", 
                    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
                    ".txt", ".md", ".csv", ".json", ".html", ".htm"}
        if ext not in all_exts:
            self.ui.error(f"Unsupported file type: {ext}")
            return
        
        self.ui.spinner("analyzing file via Mythos-Vision...", duration=0.1)
        
        try:
            result = self.vision.analyze_file(full, question)
            self.ui.assistant(result, model="mythos-vision")
        except Exception as e:
            self.ui.error(f"Vision analysis failed: {e}")

    def _read_pdf_context(self, path: str) -> None:
        """Read a PDF file and load its text into conversation context."""
        if not path:
            self.ui.error("Usage: /pdf <path> [pages]")
            return
        bits = path.split(maxsplit=1)
        pdf_path = bits[0]
        pages = bits[1].strip() if len(bits) > 1 else ""
        full = pdf_path if os.path.isabs(pdf_path) else os.path.join(self.cwd, pdf_path)
        if not os.path.isfile(full):
            self.ui.error(f"File not found: {full}")
            return
        self.ui.spinner("extracting PDF content...", duration=0.1)
        # Use the read_pdf tool directly.
        from .tools import ToolCall
        result = self.tools.execute(ToolCall(name="read_pdf", args={"path": full, "pages": pages}))
        if result.ok:
            # Feed into brain context.
            self.brain.history.append({
                "role": "system",
                "content": f"PDF contents of {path}:\n{result.output}",
            })
            self.ui.success(f"PDF loaded ({len(result.output):,} chars) into context.")
            self.ui.info(result.output[:600] + ("..." if len(result.output) > 600 else ""))
        else:
            self.ui.error(f"Failed to read PDF: {result.error}")

    def _switch_model(self, alias: str) -> None:
        alias = alias.strip().lower()
        # Accept friendly names including alternate + Shannon (Mythos-5) models.
        mapping = {
            "code": "mythos-code",
            "code-alt": "mythos-code-alt",
            "code-super": "mythos-code-super",
            "super": "mythos-code-super",
            "ultra": "mythos-ultra",
            "vision": "mythos-vision",
            "5": "mythos-5",
            "shannon": "mythos-5",
            "mythos-5": "mythos-5",
            "5-pro": "mythos-5-pro",
            "pro": "mythos-5-pro",
            "mythos-5-pro": "mythos-5-pro",
        }
        target = mapping.get(alias, alias)
        if self.brain.set_model(target):
            self.ui.success(f"Active model: {target}")
        else:
            self.ui.error(
                "Unknown model. Options: code, code-alt, code-super, ultra, vision, 5 (Mythos-5), 5-pro"
            )

    def _show_history(self) -> None:
        if not self.brain.history:
            self.ui.info("No conversation yet.")
            return
        for i, m in enumerate(self.brain.history[-12:]):
            role = m["role"]
            style = {"user": "crystal", "assistant": "crystal.hot",
                     "system": "glass.dim"}.get(role, "glass.dim")
            preview = m["content"][:100].replace("\n", " ")
            self.ui.console.print(f"  [{style}]{role}[/{style}]: {preview}...")

    def _change_dir(self, path: str) -> None:
        full = path if os.path.isabs(path) else os.path.join(self.cwd, path)
        if os.path.isdir(full):
            self.cwd = os.path.abspath(full)
            os.chdir(self.cwd)
            self.ui.success(f"cwd -> {self.cwd}")
        else:
            self.ui.error(f"Not a directory: {full}")

    # ----------------------- Lock screen ----------------------- #
    def _short_cwd(self, maxlen: int = 50) -> str:
        """Shorten the CWD for display."""
        p = self.cwd
        if len(p) <= maxlen:
            return p
        parts = p.split(os.sep)
        if len(parts) > 3:
            return parts[0] + os.sep + "\u2026" + os.sep + os.sep.join(parts[-2:])
        return "\u2026" + p[-(maxlen - 3):]

    def _launch_lock_screen(self) -> None:
        """Launch the Mythos lock screen security challenge."""
        from .lock_screen import LockScreen
        self.ui.info("Launching Mythos Security Gateway...")
        ls = LockScreen()
        result = ls.run()
        if result == "unlock":
            self.ui.success("Identity verified. Welcome back.")
        else:
            self.ui.info("Terminal closed by user.")
            self.running = False

    # ----------------------- Interactive Shell ----------------------- #
    def _interactive_shell(self) -> None:
        """Drop into an interactive shell session within Mythos."""
        shell = self.executor.best_shell()
        self.ui.divider(f"INTERACTIVE SHELL \u00b7 {shell.upper()}")
        self.ui.info('Type commands directly. Type "exit" or Ctrl+C to return to Mythos.')
        self.ui.info(f"Working directory: {self.cwd}")
        self.ui.console_obj.print()

        while self.running:
            try:
                # Show shell prompt.
                short_cwd = self._short_cwd()
                self.ui.console_obj.print(
                    Text(f"  {short_cwd}", style="glass.dim"),
                    Text(" $ ", style="crystal"),
                    sep="", end="",
                )
                cmd = input()
            except (EOFError, KeyboardInterrupt):
                self.ui.console_obj.print()
                self.ui.info("Exiting interactive shell.")
                break

            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit"):
                self.ui.info("Exiting interactive shell.")
                break

            # Handle cd specially.
            if cmd.startswith("cd ") or cmd == "cd":
                target = cmd[3:].strip() if len(cmd) > 2 else os.path.expanduser("~")
                if not os.path.isabs(target):
                    target = os.path.join(self.cwd, target)
                target = os.path.abspath(target)
                if os.path.isdir(target):
                    self.cwd = target
                    os.chdir(self.cwd)
                    self.ui.success(f"cwd -> {self.cwd}")
                else:
                    self.ui.error(f"Not a directory: {target}")
                continue

            # Execute command.
            result = self.executor.run(cmd, shell=shell, cwd=self.cwd)
            self.ui.shell_output(result)

        self.ui.divider()

    # ----------------------- Quick menu ----------------------- #
    def _quick_menu(self) -> None:
        """Interactive quick-action menu for common tasks."""
        options = [
            ("Ask Mythos to write code", "ask"),
            ("Open interactive shell", "ishell"),
            ("List files in current directory", "list"),
            ("Show system status", "status"),
            ("Search the web", "search"),
            ("Analyze an image", "image"),
            ("Clear screen", "clear"),
        ]
        labels = [o[0] for o in options]
        idx = self.ui.ask_choice("What would you like to do?", labels)
        if idx is None:
            self.ui.info("Menu cancelled.")
            return
        action = options[idx][1]

        if action == "ask":
            self.ui.info("Type your coding request below:")
        elif action == "ishell":
            self._interactive_shell()
        elif action == "list":
            self._exec_and_show("Get-ChildItem | Select-Object Name,Length,LastWriteTime", shell="powershell")
        elif action == "status":
            self._handle_slash("/status")
        elif action == "search":
            q = self.ui.ask_question("What do you want to search the web for?")
            if q:
                self._process_request(f"Use web_search to find: {q}")
        elif action == "image":
            p = self.ui.ask_question("Path to image:")
            if p:
                self._analyze_image(p)
        elif action == "clear":
            self.ui.console_obj.clear()
