"""
Mythos UI - Glasswing Edition
=============================
Premium terminal UI with frosted glass aesthetic, Unicode wing banner,
animated boot sequence, and rich-styled panels throughout.
"""
from __future__ import annotations
import os
import re
import time
import threading
from typing import Optional, List, Dict, Any

from rich.align import Align
from rich.box import ROUNDED, SIMPLE, MINIMAL
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.markdown import Markdown
from rich.padding import Padding

try:
    from colorama import init as _colorama_init
    _colorama_init()
except Exception:
    pass


# ============== Glasswing Theme ==============
GLASS_THEME = Theme({
    "glass.face":      "#d7e6f2",
    "glass.dim":       "#8fa8bf",
    "glass.edge":      "#5b7a96",
    "glass.edge.soft": "#324a63",
    "crystal":         "bold #7ff0ff",
    "crystal.hot":     "bold #b9f2ff",
    "crystal.deep":    "#4fc3e8",
    "crystal.dim":     "#4a90a8",
    "ok":     "bold #8effc8",
    "warn":   "bold #ffe08a",
    "err":    "bold #ff9aa8",
    "info":   "#9fd8ff",
    "tool.t":    "bold #c8a8ff",
    "obs.t":     "#a8c8e8",
    "shell.cmd": "bold #7ff0ff",
})

# ASCII wing motif for Windows compatibility.
_WING = (
    "---/\\  "
    "*-----"
    "-----*"
    "  /\\---"
)


class MythosUI:
    """Glasswing TUI renderer."""

    def __init__(self) -> None:
        self.console = Console(theme=GLASS_THEME, highlight=False)
        self._stop = threading.Event()

    # ======================= Boot ======================= #
    def boot_screen(self, version: str = "1.0.0", keys_alive: int = 0,
                    model: str = "mythos-code") -> None:
        self.console.clear()

        # --- Animated boot sequence with ASCII-compatible characters ---
        steps = [
            ("[*] Condensing glass surface",     "crystal"),
            ("[*] Folding crystalline wings",     "crystal.hot"),
            ("[*] Aligning neural lattice",       "crystal.deep"),
            ("[*] Polishing frosted panels",      "info"),
            ("[*] Ready for flight",              "ok"),
        ]
        for i, (txt, style) in enumerate(steps):
            self.console.print(f"  [{style}]{txt}[/{style}]")
            time.sleep(0.05)
            pct = int((i + 1) / len(steps) * 100)
            self.console.print(self._progress_bar(pct, width=24))
            time.sleep(0.04)
        self.console.print()

        # --- Wing banner inside styled panel ---
        rule_top = Rule(style="crystal.dim", characters="-")
        rule_bot = Rule(style="crystal.dim", characters="-")

        brand = Text.assemble(
            ("M", "crystal.hot"),
            ("Y", "crystal"), ("T", "crystal"),
            ("H", "crystal"), ("O", "crystal"),
            ("S", "crystal.hot"),
        )
        tagline = Text("crystalline intelligence", style="glass.dim")
        edition = Text("GLASSWING EDITION", style="crystal.deep")

        banner_body = Group(
            rule_top, Text(""),
            Align.center(Text(_WING, style="crystal.deep")),
            Text(""),
            Align.center(brand),
            Text(""),
            Align.center(edition),
            Text(""),
            Align.center(tagline),
            Text(""),
            rule_bot,
        )

        meta = Text.assemble(
            ("v", "glass.dim"), (version, "crystal"),
            ("  \u00b7  ", "glass.edge.soft"),
            (str(keys_alive), "crystal"),
            (" keys online", "glass.dim"),
            ("  \u00b7  ", "glass.edge.soft"),
            (model, "glass.face"),
        )

        self.console.print(Panel(
            banner_body, border_style="crystal.dim",
            box=ROUNDED, padding=(1, 4),
        ))
        self.console.print(Align.center(meta))
        self.console.print()

    def _progress_bar(self, pct: int, width: int = 24) -> Text:
        """Inline progress bar:  ▓▓▓▓▓▓▓▓░░░░░░░░  60%"""
        filled = max(0, int(width * pct / 100))
        empty = width - filled
        return Text.assemble(
            "    ",
            ("#" * filled, "crystal"),
            ("-" * empty, "glass.edge.soft"),
            (f"  {pct:3d}%", "glass.dim"),
        )

    def header_bar(self, model: str, keys_alive: int, cwd: str) -> None:
        short = self._short_path(cwd)
        bar = Table.grid(expand=True)
        bar.add_column(justify="left", style="glass.dim", ratio=1)
        bar.add_column(justify="center", style="crystal", ratio=1)
        bar.add_column(justify="right", style="glass.dim", ratio=1)
        bar.add_row(
            f"\u25c8 {model}",
            f"* {keys_alive} keys",
            f"- {short}",
        )
        self.console.print(Panel(
            bar, border_style="glass.edge.soft", box=MINIMAL, padding=(0, 1),
        ))

    # ======================= Prompt ======================= #
    def prompt(self, cwd: str) -> str:
        self.console.print()
        self.console.print(
            Text(">", style="crystal.hot"),
            Text(" mythos ", style="crystal"),
            Text("\u276f", style="crystal.deep"),
            sep="", end="",
        )
        try:
            line = input(" ")
        except (EOFError, KeyboardInterrupt):
            return "/exit"
        return line.strip()

    def _short_path(self, path: str, maxlen: int = 42) -> str:
        if len(path) <= maxlen:
            return path
        parts = path.split(os.sep)
        if len(parts) > 3:
            return parts[0] + os.sep + "\u2026" + os.sep + os.sep.join(parts[-2:])
        return "\u2026" + path[-(maxlen - 3):]

    # ======================= Renderers ======================= #
    def assistant(self, text: str, model: str = "mythos-code",
                  tools_used: int = 0) -> None:
        header = Text.assemble(
            ("* ", "crystal"),
            ("MYTHOS", "crystal.hot"),
            (f" \u00b7 {model}", "crystal"),
        )
        if tools_used:
            header.append(f"  \u00b7  {tools_used} tool{'s' if tools_used > 1 else ''}",
                          "glass.dim")
        body = self._render_mixed(text)
        self.console.print(Panel(
            body, border_style="glass.edge", box=ROUNDED,
            title=header, title_align="left", padding=(1, 2),
        ))

    def _render_mixed(self, text: str) -> Group:
        parts: List[Any] = []
        pattern = re.compile(r"```(\w+[-\w]*)?\n(.*?)```", re.DOTALL)
        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                parts.append(Markdown(text[last:m.start()]))
            lang = m.group(1) or "text"
            code = m.group(2).rstrip("\n")
            if lang in ("mythos-shell", "mythos-file"):
                code = re.sub(r"^# (shell|path):.*\n", "", code, flags=re.MULTILINE)
                if lang == "mythos-shell":
                    lang = "powershell"
            display_lang = "json" if lang == "mythos-tool" else lang
            syntax = Syntax(code, display_lang, theme="monokai",
                            word_wrap=True, background_color="default",
                            padding=(1, 2))
            parts.append(syntax)
            last = m.end()
        if last < len(text):
            parts.append(Markdown(text[last:]))
        if not parts:
            parts.append(Text(text))
        return Group(*parts)

    def tool_call(self, name: str, args: Dict[str, Any], step: int) -> None:
        args_str = ", ".join(f"{k}={self._fmt(v)}" for k, v in args.items())
        chip = Text.assemble(
            ("* ", "tool.t"),
            (f"#{step}  ", "tool.t"),
            (f"{name}(", "glass.face"),
            (args_str, "crystal.deep"),
            (")", "glass.face"),
        )
        self.console.print(Padding.indent(chip, 2))

    def observation(self, output: str, ok: bool, step: int) -> None:
        icon = "\u2713" if ok else "\u2717"
        style = "obs.t" if ok else "err"
        head = Text.assemble(
            (f"{icon} ", style), (f"#{step}  ", style),
            ("result", "glass.dim"),
        )
        body = Text(output[:2000] + ("\n...[truncated]" if len(output) > 2000 else ""),
                    style="glass.face")
        self.console.print(Padding.indent(
            Panel(body, border_style="glass.edge.soft", box=ROUNDED,
                  title=head, title_align="left", padding=(0, 1)), 4))

    def shell_output(self, result: Any) -> None:
        icon = "\u2713" if result.success else "\u2717"
        st = "ok" if result.success else "err"
        head = Text.assemble(
            (f"{icon} ", st), ("SHELL ", "shell.cmd"),
            (f"{result.shell.upper()} ", "crystal"),
            (f"\u00b7 {result.duration:.2f}s \u00b7 exit {result.exit_code}",
             "glass.dim"),
        )
        lines = [Text(f"$ {result.command}", style="shell.cmd"), Text("")]
        if result.stdout.strip():
            lines.append(Text(result.stdout.rstrip(), style="glass.face"))
        if result.stderr.strip():
            lines.append(Text(result.stderr.rstrip(), style="err"))
        if not result.stdout.strip() and not result.stderr.strip():
            lines.append(Text("(no output)", style="glass.dim"))
        self.console.print(Panel(
            Group(*lines), border_style="glass.edge", box=ROUNDED,
            title=head, title_align="left", padding=(1, 2)))

    def file_written(self, path: str, lines: int, bytes_size: int) -> None:
        self.console.print(Text.assemble(
            ("\u2713 ", "ok"), ("WROTE ", "crystal"), (path, "crystal.hot"),
            (f"  \u00b7  {lines} lines \u00b7 {bytes_size:,} bytes", "glass.dim"),
        ))

    # ======================= Interactive prompts ======================= #
    def ask_question(self, question: str) -> str:
        """Free-text question from AI. Returns the user's typed answer."""
        self.console.print()
        q = Panel(
            Text(question, style="glass.face"),
            border_style="crystal.deep", box=ROUNDED,
            title=Text.assemble(("\u275d ", "crystal.hot"),
                                ("MYTHOS ASKS", "crystal")),
            title_align="left", padding=(1, 2),
        )
        self.console.print(q)
        self.console.print(Text("  \u276f ", style="crystal.hot"), end="")
        try:
            return input().strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def ask_choice(self, question: str, options: List[str]) -> Optional[int]:
        """
        Multiple-choice question from AI. Renders numbered options.
        Returns the chosen index (0-based), or None on cancel.
        """
        self.console.print()
        q = Panel(
            Text(question, style="glass.face"),
            border_style="crystal.deep", box=ROUNDED,
            title=Text.assemble(("\u275d ", "crystal.hot"),
                                ("MYTHOS ASKS", "crystal")),
            title_align="left", padding=(1, 2),
        )
        self.console.print(q)
        self.console.print()
        for i, opt in enumerate(options, 1):
            self.console.print(Text.assemble(
                ("   ", ""),
                (f"[{i}]", "crystal.hot"),
                (f"  {opt}", "glass.face"),
            ))
        self.console.print(Text.assemble(
            ("   ", ""),
            ("[0]", "glass.dim"),
            ("  cancel", "glass.dim"),
        ))
        self.console.print()
        n = len(options)
        while True:
            self.console.print(
                Text(f"  \u276f choose 1-{n} (0=cancel) ", style="crystal"),
                end="")
            try:
                raw = input().strip()
            except (EOFError, KeyboardInterrupt):
                return None
            if not raw:
                continue
            try:
                idx = int(raw)
            except ValueError:
                self.warn("Enter a number.")
                continue
            if 0 <= idx <= n:
                return idx - 1 if idx > 0 else None
            self.warn(f"Out of range. Pick 0-{n}.")

    def ask_confirm(self, question: str) -> bool:
        """Yes/no confirmation from AI. Returns True for yes."""
        self.console.print()
        q = Panel(
            Text(question, style="glass.face"),
            border_style="warn", box=ROUNDED,
            title=Text.assemble(("\u26a0 ", "warn"),
                                ("CONFIRM", "warn")),
            title_align="left", padding=(1, 2),
        )
        self.console.print(q)
        while True:
            self.console.print(Text("  \u276f y/n ", style="warn"), end="")
            try:
                raw = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                return False
            if raw in ("y", "yes"):
                return True
            if raw in ("n", "no"):
                return False
            self.warn("Type y or n.")

    def ai_thinking(self, message: str = "thinking", model: str = "") -> None:
        """Enhanced thinking indicator with model info."""
        self.console.print()
        model_info = f" | {model}" if model else ""
        self.console.print(Text.assemble(
            ("  [*] ", "crystal"),
            ("MYTHOS", "crystal.hot"),
            (model_info, "crystal"),
            (" ... ", "glass.dim"),
            (message, "glass.dim"),
        ))

    def tool_executing(self, tool_name: str, step: int, args: Dict[str, Any] = None) -> None:
        """Show tool execution in progress."""
        args_preview = ""
        if args:
            key_args = []
            for k, v in list(args.items())[:2]:
                val = str(v)[:30]
                key_args.append(f"{k}={val}")
            args_preview = f" | {', '.join(key_args)}"

        self.console.print(Text.assemble(
            ("  > ", "tool.t"),
            (f"STEP #{step}", "tool.t"),
            (" | ", "glass.edge.soft"),
            (tool_name, "crystal"),
            (args_preview, "glass.dim"),
        ))

    def streaming_start(self, model: str = "") -> None:
        """Show streaming response started."""
        self.console.print(Text.assemble(
            ("  >> ", "crystal"),
            ("RECEIVING", "crystal"),
            (f" | {model}" if model else "", "crystal.dim"),
            (" ...", "glass.dim"),
        ), end="")

    def processing_tools(self, count: int) -> None:
        """Show multiple tools being processed."""
        self.console.print(Text.assemble(
            ("  [*] ", "tool.t"),
            ("PROCESSING", "tool.t"),
            (f" {count} tool{'s' if count > 1 else ''}", "glass.face"),
            (" ...", "glass.dim"),
        ))

    def response_complete(self, model: str = "", tools_used: int = 0, duration: float = 0) -> None:
        """Show response completed with stats."""
        parts = [
            ("  [OK] ", "ok"),
            ("COMPLETE", "ok"),
        ]
        if model:
            parts.append((" | ", "glass.edge.soft"))
            parts.append((model, "crystal"))
        if tools_used:
            parts.append((" | ", "glass.edge.soft"))
            parts.append((f"{tools_used} tool{'s' if tools_used > 1 else ''}", "tool.t"))
        if duration > 0:
            parts.append((" | ", "glass.edge.soft"))
            parts.append((f"{duration:.1f}s", "glass.dim"))
        self.console.print(Text.assemble(*parts))

    def phase_indicator(self, phase: str, detail: str = "") -> None:
        """Show current processing phase."""
        icons = {
            "thinking": "[*]",
            "routing": "[>]",
            "executing": "[>]",
            "verifying": "[OK]",
            "streaming": "[>>]",
            "complete": "[OK]",
            "error": "[!]",
        }
        icon = icons.get(phase, "[*]")
        style = "err" if phase == "error" else "crystal"
        self.console.print(Text.assemble(
            (f"  {icon} ", style),
            (phase.upper(), style),
            (f" | {detail}" if detail else "", "glass.dim"),
        ))

    # ======================= Status ======================= #
    def info(self, m: str) -> None:
        self.console.print(Text.assemble(
            ("  > ", "info"), (m, "info")))

    def success(self, m: str) -> None:
        self.console.print(Text.assemble(
            ("  \u2713 ", "ok"), (m, "ok")))

    def warn(self, m: str) -> None:
        self.console.print(Text.assemble(
            ("  \u26a0 ", "warn"), (m, "warn")))

    def error(self, m: str) -> None:
        self.console.print(Text.assemble(
            ("  \u2717 ", "err"), (m, "err")))

    def divider(self, label: str = "") -> None:
        if label:
            self.console.print(Rule(
                title=Text(f" {label} ", style="crystal"),
                style="glass.edge.soft", characters="-"))
        else:
            self.console.print(Rule(style="glass.edge.soft", characters="-"))

    def spinner(self, msg: str, duration: Optional[float] = None) -> None:
        sp = Spinner("dots12", text=Text(f"  {msg}", style="crystal"))
        with Live(sp, console=self.console, refresh_per_second=15,
                  transient=True) as live:
            if duration is not None:
                end = time.time() + duration
                while time.time() < end:
                    live.update(sp); time.sleep(0.05)
            else:
                time.sleep(0.4)

    @property
    def console_obj(self) -> Console:
        return self.console

    def _fmt(self, v: Any) -> str:
        if isinstance(v, str) and len(v) > 60:
            return repr(v[:60] + "...")
        return repr(v)

    # ======================= Help / status ======================= #
    def help_table(self) -> None:
        t = Table(box=SIMPLE, padding=(0, 2), show_header=False,
                  border_style="glass.edge.soft")
        t.add_column("Cmd", style="crystal", no_wrap=True)
        t.add_column("Description", style="glass.face")
        for c, d in [
            ("/help", "Show this help"),
            ("/status", "Show key & model status"),
            ("/clear", "Clear screen"),
            ("/ishell", "Interactive shell session"),
            ("/menu", "Quick-action menu"),
            ("/shell <cmd>", "Force shell execution"),
            ("/ps <cmd>", "Force PowerShell"),
            ("/cmd <cmd>", "Force CMD"),
            ("/file <path>", "Read a file into context"),
            ("/image <path>", "Analyze an image with Mythos-Vision"),
            ("/pdf <path>", "Read a PDF file into context"),
            ("/lock", "Launch security lock screen"),
            ("/model <name>", "Switch model (code/ultra/vision)"),
            ("/tools", "List available AI tools"),
            ("/history", "Show conversation history"),
            ("/exit", "Exit Mythos"),
        ]:
            t.add_row(c, d)
        self.console.print(Panel(
            t, box=ROUNDED, border_style="glass.edge", padding=(1, 2),
            title=Text.assemble(
                ("* ", "crystal"), ("COMMANDS", "crystal.hot")),
            title_align="left",
        ))

    def status_table(self, key_stats: Dict[str, int], current_model: str,
                     shells: Dict[str, Any], tools: Optional[List[str]] = None) -> None:
        t = Table(box=SIMPLE, padding=(0, 2),
                  border_style="glass.edge.soft")
        t.add_column("Subsystem", style="crystal.hot", no_wrap=True)
        t.add_column("State", style="glass.face")
        t.add_row("Active Model", f"[crystal]{current_model}[/crystal]")
        t.add_row("OpenRouter Keys",
                  f"{key_stats.get('openrouter_available',0)}"
                  f"/{key_stats.get('openrouter_alive',0)} available")
        t.add_row("Z.AI Keys",
                  f"{key_stats.get('zai_available',0)}"
                  f"/{key_stats.get('zai_alive',0)} available")
        if tools:
            t.add_row("AI Tools", ", ".join(tools))
        for name, path in shells.items():
            if path:
                t.add_row(f"Shell: {name}", "[ok]available[/ok]")
        self.console.print(Panel(
            t, box=ROUNDED, border_style="glass.edge", padding=(1, 2),
            title=Text.assemble(
                ("* ", "crystal"), ("STATUS", "crystal.hot")),
            title_align="left",
        ))

    def tools_table(self, tools: List[str], schema: str) -> None:
        t = Table(box=SIMPLE, padding=(0, 2),
                  border_style="glass.edge.soft")
        t.add_column("Tool", style="crystal.hot")
        t.add_column("Signature", style="glass.face")
        for line in schema.splitlines():
            m = re.match(r"-\s+(\w+)\((.*?)\):\s*(.*)", line)
            if m:
                t.add_row(m.group(1), f"{m.group(2)} \u00b7 {m.group(3)}")
        self.console.print(Panel(
            t, box=ROUNDED, border_style="glass.edge", padding=(1, 2),
            title=Text.assemble(
                ("* ", "crystal"), ("AI TOOL REGISTRY", "crystal.hot")),
            title_align="left",
        ))

    # ======================= Command System UI ======================= #
    def help_header(self) -> None:
        self.console.print(Panel(
            Text("Mythos Command Reference", style="crystal.hot"),
            box=ROUNDED, border_style="crystal.dim", padding=(0, 2),
        ))

    def help_category(self, category: str) -> None:
        icons = {
            "system": "\u2699",
            "ai": "\u2661",
            "file": "\u2630",
            "exec": ">",
            "security": "\u26a1",
        }
        icon = icons.get(category, "*")
        self.console.print(Text.assemble(
            ("\n  ", ""),
            (f"{icon} ", "crystal"),
            (category.upper(), "crystal.hot"),
        ), end="")

    def help_item(self, cmd: str, desc: str) -> None:
        self.console.print(Text.assemble(
            ("    ", ""),
            (f"{cmd:<20}", "crystal"),
            (desc, "glass.dim"),
        ))

    def help_footer(self) -> None:
        self.console.print(Text.assemble(
            ("\n  ", ""),
            ("Tip: ", "glass.dim"),
            ("Use /model <name> to switch models", "info"),
        ))

    def model_list(self, models: Dict[str, str], current: str) -> None:
        t = Table(box=SIMPLE, padding=(0, 2),
                  border_style="glass.edge.soft")
        t.add_column("Alias", style="crystal.hot", no_wrap=True)
        t.add_column("Model", style="glass.face")
        t.add_column("Status", style="glass.dim")
        for alias, name in models.items():
            status = "[ok]ACTIVE[/ok]" if alias == current else ""
            t.add_row(alias, name, status)
        self.console.print(Panel(
            t, box=ROUNDED, border_style="glass.edge", padding=(1, 2),
            title=Text.assemble(
                ("* ", "crystal"), ("AVAILABLE MODELS", "crystal.hot")),
            title_align="left",
        ))

    def key_status(self, status: Dict[str, Any]) -> None:
        t = Table(box=SIMPLE, padding=(0, 2),
                  border_style="glass.edge.soft")
        t.add_column("Provider", style="crystal.hot", no_wrap=True)
        t.add_column("Alive", style="ok")
        t.add_column("Available", style="glass.face")
        t.add_row("OpenRouter",
                  str(status.get("openrouter_alive", 0)),
                  str(status.get("openrouter_available", 0)))
        t.add_row("Z.AI",
                  str(status.get("zai_alive", 0)),
                  str(status.get("zai_available", 0)))
        self.console.print(Panel(
            t, box=ROUNDED, border_style="glass.edge", padding=(1, 2),
            title=Text.assemble(
                ("* ", "crystal"), ("API KEY STATUS", "crystal.hot")),
            title_align="left",
        ))

    def set_theme(self, theme: str) -> None:
        """Set UI theme (placeholder for future implementation)."""
        self.theme = theme
