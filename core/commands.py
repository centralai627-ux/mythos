"""
Mythos Command System
=====================
High-precision slash command handler with auto-complete, validation, and context-aware execution.
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
from typing import Optional, Dict, Any, Callable, List, Tuple
from dataclasses import dataclass, field


@dataclass
class Command:
    """A single slash command definition."""
    name: str
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    usage: str = ""
    handler: Optional[Callable] = None
    requires_args: bool = False
    hidden: bool = False
    category: str = "general"


class CommandRegistry:
    """Central command registry with validation and execution."""

    def __init__(self, agent: Any = None) -> None:
        self.agent = agent
        self.commands: Dict[str, Command] = {}
        self._register_all()

    def _register_all(self) -> None:
        """Register all built-in commands."""
        self._register(Command(
            name="/help", aliases=["/h", "/?"],
            description="Show available commands",
            usage="/help [command]",
            handler=self._cmd_help,
            category="system"
        ))
        self._register(Command(
            name="/exit", aliases=["/quit", "/q"],
            description="Exit Mythos",
            handler=self._cmd_exit,
            category="system"
        ))
        self._register(Command(
            name="/status", aliases=["/info"],
            description="Show system status and diagnostics",
            handler=self._cmd_status,
            category="system"
        ))
        self._register(Command(
            name="/model", aliases=["/m"],
            description="Switch or show current AI model",
            usage="/model [name]",
            handler=self._cmd_model,
            category="ai"
        ))
        self._register(Command(
            name="/models", aliases=["/ml"],
            description="List all available models",
            handler=self._cmd_models,
            category="ai"
        ))
        self._register(Command(
            name="/clear", aliases=["/cls"],
            description="Clear terminal screen",
            handler=self._cmd_clear,
            category="system"
        ))
        self._register(Command(
            name="/history",
            description="Show conversation history",
            usage="/history [lines]",
            handler=self._cmd_history,
            category="ai"
        ))
        self._register(Command(
            name="/reset",
            description="Reset conversation context",
            handler=self._cmd_reset,
            category="ai"
        ))
        self._register(Command(
            name="/cd",
            description="Change working directory",
            usage="/cd <path>",
            handler=self._cmd_cd,
            requires_args=True,
            category="file"
        ))
        self._register(Command(
            name="/pwd",
            description="Print working directory",
            handler=self._cmd_pwd,
            category="file"
        ))
        self._register(Command(
            name="/ls", aliases=["/dir"],
            description="List directory contents",
            usage="/ls [path]",
            handler=self._cmd_ls,
            category="file"
        ))
        self._register(Command(
            name="/file",
            description="Read file into context",
            usage="/file <path>",
            handler=self._cmd_file,
            requires_args=True,
            category="file"
        ))
        self._register(Command(
            name="/write",
            description="Write content to file",
            usage="/write <path> <content>",
            handler=self._cmd_write,
            requires_args=True,
            category="file"
        ))
        self._register(Command(
            name="/shell", aliases=["/sh"],
            description="Execute shell command (auto-detect)",
            usage="/shell <command>",
            handler=lambda arg: self._cmd_exec(arg, shell=None),
            requires_args=True,
            category="exec"
        ))
        self._register(Command(
            name="/ps",
            description="Execute PowerShell command",
            usage="/ps <command>",
            handler=lambda arg: self._cmd_exec(arg, shell="powershell"),
            requires_args=True,
            category="exec"
        ))
        self._register(Command(
            name="/cmd",
            description="Execute CMD command",
            usage="/cmd <command>",
            handler=lambda arg: self._cmd_exec(arg, shell="cmd"),
            requires_args=True,
            category="exec"
        ))
        self._register(Command(
            name="/bash",
            description="Execute Bash command",
            usage="/bash <command>",
            handler=lambda arg: self._cmd_exec(arg, shell="bash"),
            requires_args=True,
            category="exec"
        ))
        self._register(Command(
            name="/ishell", aliases=["/ish"],
            description="Drop into interactive shell",
            handler=self._cmd_ishell,
            category="exec"
        ))
        self._register(Command(
            name="/image", aliases=["/img"],
            description="Analyze image with vision",
            usage="/image <path> [question]",
            handler=self._cmd_image,
            requires_args=True,
            category="ai"
        ))
        self._register(Command(
            name="/pdf",
            description="Read PDF into context",
            usage="/pdf <path> [pages]",
            handler=self._cmd_pdf,
            requires_args=True,
            category="file"
        ))
        self._register(Command(
            name="/lock",
            description="Launch security lock screen",
            handler=self._cmd_lock,
            category="security"
        ))
        self._register(Command(
            name="/menu",
            description="Show quick-action menu",
            handler=self._cmd_menu,
            category="system"
        ))
        self._register(Command(
            name="/tools", aliases=["/t"],
            description="List available tools",
            handler=self._cmd_tools,
            category="system"
        ))
        self._register(Command(
            name="/keys",
            description="Show API key status",
            handler=self._cmd_keys,
            category="system"
        ))
        self._register(Command(
            name="/verbose", aliases=["/v"],
            description="Toggle verbose output",
            usage="/verbose [on|off]",
            handler=self._cmd_verbose,
            category="system"
        ))
        self._register(Command(
            name="/debug", aliases=["/d"],
            description="Toggle debug mode",
            usage="/debug [on|off]",
            handler=self._cmd_debug,
            category="system"
        ))
        self._register(Command(
            name="/version",
            description="Show Mythos version",
            handler=self._cmd_version,
            category="system"
        ))
        self._register(Command(
            name="/memory",
            description="Show memory usage",
            handler=self._cmd_memory,
            category="system"
        ))
        self._register(Command(
            name="/compact",
            description="Compact conversation history",
            handler=self._cmd_compact,
            category="ai"
        ))
        self._register(Command(
            name="/export",
            description="Export conversation to file",
            usage="/export [path]",
            handler=self._cmd_export,
            category="ai"
        ))
        self._register(Command(
            name="/theme",
            description="Change UI theme",
            usage="/theme [name]",
            handler=self._cmd_theme,
            category="system"
        ))

    def _register(self, cmd: Command) -> None:
        """Register a command."""
        self.commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self.commands[alias] = cmd

    def resolve(self, input_cmd: str) -> Optional[Command]:
        """Resolve a command input to its Command object."""
        cmd = input_cmd.lower().strip()
        return self.commands.get(cmd)

    def list_commands(self, show_hidden: bool = False) -> List[Command]:
        """Get unique commands (excluding aliases)."""
        seen = set()
        result = []
        for cmd in self.commands.values():
            if cmd.name not in seen and (show_hidden or not cmd.hidden):
                seen.add(cmd.name)
                result.append(cmd)
        return sorted(result, key=lambda c: (c.category, c.name))

    def get_categories(self) -> Dict[str, List[Command]]:
        """Group commands by category."""
        cats: Dict[str, List[Command]] = {}
        for cmd in self.list_commands():
            cats.setdefault(cmd.category, []).append(cmd)
        return cats

    def execute(self, line: str) -> bool:
        """Execute a slash command. Returns True if handled."""
        if not line.startswith("/"):
            return False

        parts = line.split(maxsplit=1)
        cmd_input = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        cmd = self.resolve(cmd_input)
        if cmd is None:
            if self.agent and self.agent.ui:
                self.agent.ui.error(f"Unknown command: {cmd_input}. Type /help for commands.")
            return True

        if cmd.requires_args and not arg.strip():
            if self.agent and self.agent.ui:
                self.agent.ui.error(f"Missing arguments. Usage: {cmd.usage}")
            return True

        try:
            if cmd.handler:
                cmd.handler(arg)
            return True
        except Exception as e:
            if self.agent and self.agent.ui:
                self.agent.ui.error(f"Command error: {e}")
            return True

    # ----------------------- Command Handlers ----------------------- #

    def _cmd_help(self, arg: str) -> None:
        """Show help for a specific command or all commands."""
        ui = self.agent.ui if self.agent else None
        if not ui:
            return

        if arg.strip():
            cmd = self.resolve(arg.strip())
            if cmd:
                ui.info(f"Command: {cmd.name}")
                ui.info(f"  {cmd.description}")
                if cmd.usage:
                    ui.info(f"  Usage: {cmd.usage}")
                if cmd.aliases:
                    ui.info(f"  Aliases: {', '.join(cmd.aliases)}")
            else:
                ui.error(f"Unknown command: {arg}")
            return

        cats = self.get_categories()
        ui.help_header()
        for cat, cmds in cats.items():
            ui.help_category(cat)
            for cmd in cmds:
                ui.help_item(cmd.name, cmd.description)
        ui.help_footer()

    def _cmd_exit(self, arg: str) -> None:
        if self.agent:
            self.agent.ui.info("Shutting down Mythos. Goodbye.")
            self.agent.running = False

    def _cmd_status(self, arg: str) -> None:
        if self.agent:
            self.agent.ui.status_table(
                self.agent.keys.status(),
                self.agent.brain.current_model,
                self.agent.executor.detect_shells(),
                tools=self.agent.tools.names,
            )

    def _cmd_model(self, arg: str) -> None:
        if not self.agent:
            return
        if not arg.strip():
            self.agent.ui.info(f"Current model: {self.agent.brain.current_model}")
            return
        self.agent._switch_model(arg)

    def _cmd_models(self, arg: str) -> None:
        if not self.agent:
            return
        models = {
            "code": "Mythos Code (fast)",
            "code-alt": "Mythos Code Alt",
            "code-super": "Mythos Code Super (120B)",
            "ultra": "Mythos Ultra (powerful)",
            "vision": "Mythos Vision (multimodal)",
            "5": "Mythos-5 (Shannon)",
            "5-pro": "Mythos-5 Pro",
        }
        self.agent.ui.model_list(models, self.agent.brain.current_model)

    def _cmd_clear(self, arg: str) -> None:
        if self.agent:
            self.agent.ui.console.clear()

    def _cmd_history(self, arg: str) -> None:
        if not self.agent:
            return
        n = 12
        if arg.strip():
            try:
                n = int(arg.strip())
            except ValueError:
                pass
        self.agent._show_history()

    def _cmd_reset(self, arg: str) -> None:
        if not self.agent:
            return
        self.agent.brain.history.clear()
        self.agent.ui.success("Conversation context cleared.")

    def _cmd_cd(self, arg: str) -> None:
        if not self.agent:
            return
        target = arg.strip() or os.path.expanduser("~")
        full = target if os.path.isabs(target) else os.path.join(self.agent.cwd, target)
        full = os.path.abspath(full)
        if os.path.isdir(full):
            self.agent.cwd = full
            os.chdir(full)
            self.agent.ui.success(f"cwd -> {full}")
        else:
            self.agent.ui.error(f"Not a directory: {full}")

    def _cmd_pwd(self, arg: str) -> None:
        if self.agent:
            self.agent.ui.info(f"cwd: {self.agent.cwd}")

    def _cmd_ls(self, arg: str) -> None:
        if not self.agent:
            return
        target = arg.strip() or "."
        full = target if os.path.isabs(target) else os.path.join(self.agent.cwd, target)
        self.agent._exec_and_show(
            f'Get-ChildItem "{full}" | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize',
            shell="powershell"
        )

    def _cmd_file(self, arg: str) -> None:
        if not self.agent:
            return
        self.agent._read_file(arg)

    def _cmd_write(self, arg: str) -> None:
        if not self.agent:
            return
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self.agent.ui.error("Usage: /write <path> <content>")
            return
        path, content = parts
        self.agent._write_file(path, content)

    def _cmd_exec(self, arg: str, shell: Optional[str] = None) -> None:
        if not self.agent:
            return
        self.agent._exec_and_show(arg, shell=shell)

    def _cmd_ishell(self, arg: str) -> None:
        if self.agent:
            self.agent._interactive_shell()

    def _cmd_image(self, arg: str) -> None:
        if not self.agent:
            return
        self.agent._analyze_image(arg)

    def _cmd_pdf(self, arg: str) -> None:
        if not self.agent:
            return
        self.agent._read_pdf_context(arg)

    def _cmd_lock(self, arg: str) -> None:
        if self.agent:
            self.agent._launch_lock_screen()

    def _cmd_menu(self, arg: str) -> None:
        if self.agent:
            self.agent._quick_menu()

    def _cmd_tools(self, arg: str) -> None:
        if self.agent:
            self.agent.ui.tools_table(self.agent.tools.names, self.agent.tools.schema_for_prompt())

    def _cmd_keys(self, arg: str) -> None:
        if not self.agent:
            return
        status = self.agent.keys.status()
        self.agent.ui.key_status(status)

    def _cmd_verbose(self, arg: str) -> None:
        if not self.agent:
            return
        state = arg.strip().lower()
        if state == "on":
            self.agent.verbose = True
            self.agent.ui.success("Verbose mode ON")
        elif state == "off":
            self.agent.verbose = False
            self.agent.ui.success("Verbose mode OFF")
        else:
            self.agent.verbose = not getattr(self.agent, "verbose", False)
            self.agent.ui.info(f"Verbose mode: {'ON' if self.agent.verbose else 'OFF'}")

    def _cmd_debug(self, arg: str) -> None:
        if not self.agent:
            return
        state = arg.strip().lower()
        if state == "on":
            self.agent.debug = True
            self.agent.ui.success("Debug mode ON")
        elif state == "off":
            self.agent.debug = False
            self.agent.ui.success("Debug mode OFF")
        else:
            self.agent.debug = not getattr(self.agent, "debug", False)
            self.agent.ui.info(f"Debug mode: {'ON' if self.agent.debug else 'OFF'}")

    def _cmd_version(self, arg: str) -> None:
        if self.agent:
            self.agent.ui.info("Mythos v1.0.0 Glasswing")

    def _cmd_memory(self, arg: str) -> None:
        if not self.agent:
            return
        history_size = len(self.agent.brain.history)
        self.agent.ui.info(f"Conversation messages: {history_size}")
        self.agent.ui.info(f"Current model: {self.agent.brain.current_model}")
        self.agent.ui.info(f"Working directory: {self.agent.cwd}")

    def _cmd_compact(self, arg: str) -> None:
        if not self.agent:
            return
        if not self.agent.brain.history:
            self.agent.ui.info("Nothing to compact.")
            return
        before = len(self.agent.brain.history)
        self.agent.brain.history = self.agent.brain.history[-20:]
        after = len(self.agent.brain.history)
        self.agent.ui.success(f"Compacted: {before} -> {after} messages")

    def _cmd_export(self, arg: str) -> None:
        if not self.agent:
            return
        path = arg.strip() or f"mythos_export_{int(time.time())}.json"
        data = {
            "model": self.agent.brain.current_model,
            "cwd": self.agent.cwd,
            "history": self.agent.brain.history,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.agent.ui.success(f"Exported to {path}")
        except Exception as e:
            self.agent.ui.error(f"Export failed: {e}")

    def _cmd_theme(self, arg: str) -> None:
        if not self.agent:
            return
        themes = ["glass", "frost", "neon", "minimal"]
        current = getattr(self.agent.ui, "theme", "glass")
        if arg.strip().lower() in themes:
            self.agent.ui.set_theme(arg.strip().lower())
            self.agent.ui.success(f"Theme: {arg.strip().lower()}")
        else:
            self.agent.ui.info(f"Current: {current}. Options: {', '.join(themes)}")
