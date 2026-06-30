"""
Mythos Tools
=============
Model-agnostic tool registry for the agentic loop. The AI emits structured
`mythos-tool` blocks; this module executes them and returns observations.

File & Directory Tools:
  - read_file(path)            -> file contents (truncated at 60K chars)
  - write_file(path, content)  -> atomic write, creates parent dirs
  - list_dir(path)             -> directory listing (max 500 entries)
  - search(pattern, path, glob)-> search files for regex patterns

Shell & System:
  - run_shell(command, shell)  -> execute CMD/PowerShell commands

User Interaction:
  - ask_user(question)         -> free-text prompt via UI hook
  - ask_choice(question, options) -> multiple-choice selection (2-12 options)
  - ask_confirm(question)      -> yes/no confirmation

Web:
  - web_search(query)          -> search Wikipedia (no API key required)
  - web_fetch(url)             -> fetch + strip a web page's text

PDF:
  - generate_pdf(path, content, title, author) -> create PDF from markdown
  - read_pdf(path, pages)      -> extract text from PDF
  - merge_pdf(output, inputs)  -> merge multiple PDFs into one

Quantum Computing:
  - quantum_optimize(cost_function, initial_state) -> quantum annealing
  - quantum_search(data, target) -> Grover's search algorithm
  - quantum_sort(data)          -> quantum-inspired sorting
  - quantum_probability(outcomes, probabilities) -> probability distribution
  - quantum_correlate(state1, state2) -> entanglement score
  - quantum_neural(inputs, weights, architecture) -> quantum neural network
  - quantum_cluster(data, n_clusters) -> quantum clustering
  - quantum_pathfind(graph, start, end) -> quantum pathfinding
  - quantum_encrypt(data, key) -> quantum encryption
  - quantum_decrypt(data, key) -> quantum decryption
  - quantum_recommend(user_history, item_features) -> recommendations
  - quantum_anomaly(data, threshold) -> anomaly detection
  - quantum_forecast(data, periods) -> time series forecast
  - quantum_importance(features, target) -> feature importance

Design principles:
  - Path safety: all paths resolved against cwd; traversal blocked.
  - Deterministic: same args -> same result (no hidden state).
  - Verbose errors: AI must see WHY a tool failed so it can self-correct.
"""
from __future__ import annotations
import os
import re
import html
import fnmatch
import threading
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Tuple

from .executor import ShellExecutor


@dataclass
class ToolCall:
    """A single parsed tool invocation."""
    name: str
    args: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.args.items())
        return f"{self.name}({args_str})"


@dataclass
class ToolResult:
    """Outcome of a tool call."""
    ok: bool
    output: str
    error: str = ""

    def as_observation(self) -> str:
        """Format for feeding back into the AI context."""
        if self.ok:
            return f"[TOOL OK]\n{self.output}"
        return f"[TOOL ERROR] {self.error}\n{self.output}"


class ToolRegistry:
    """Holds tool definitions and their executors."""

    def __init__(self, executor: ShellExecutor, ui_hook: Optional[Callable] = None,
                 choice_hook: Optional[Callable] = None,
                 confirm_hook: Optional[Callable] = None,
                 cwd: str = ".") -> None:
        self.executor = executor
        self.ui_hook = ui_hook          # (question) -> str
        self.choice_hook = choice_hook  # (question, options) -> int|None
        self.confirm_hook = confirm_hook  # (question) -> bool
        self.cwd = os.path.abspath(cwd)
        self._lock = threading.Lock()
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_all()

    # ----------------------- Registration ----------------------- #
    def _register_all(self) -> None:
        self._tools = {
            "read_file": {
                "desc": "Read a file's contents.",
                "params": {"path": "string (relative or absolute file path)"},
                "run": self._read_file,
            },
            "write_file": {
                "desc": "Write content to a file (atomic). Creates parent dirs.",
                "params": {"path": "string", "content": "string"},
                "run": self._write_file,
            },
            "list_dir": {
                "desc": "List directory entries.",
                "params": {"path": "string (default: cwd)"},
                "run": self._list_dir,
            },
            "search": {
                "desc": "Search for a regex/pattern in files (recursively).",
                "params": {
                    "pattern": "string (regex)",
                    "path": "string (default: cwd)",
                    "glob": "string (e.g. *.py; default *)",
                },
                "run": self._search,
            },
            "run_shell": {
                "desc": "Execute a CMD/PowerShell/bash command.",
                "params": {
                    "command": "string",
                    "shell": "cmd | powershell | pwsh | bash (default: auto)",
                },
                "run": self._run_shell,
            },
            "ask_user": {
                "desc": "Ask the human a free-text clarifying question.",
                "params": {"question": "string"},
                "run": self._ask_user,
            },
            "ask_choice": {
                "desc": "Ask the human to pick ONE option from a list. Use when choices are constrained.",
                "params": {
                    "question": "string",
                    "options": "array of strings (the choices)",
                },
                "run": self._ask_choice,
            },
            "ask_confirm": {
                "desc": "Ask the human a yes/no confirmation before a risky action.",
                "params": {"question": "string"},
                "run": self._ask_confirm,
            },
            "web_search": {
                "desc": "Search the web for current information. Returns titles + snippets + URLs.",
                "params": {
                    "query": "string (search terms)",
                    "max_results": "int (default 5, max 10)",
                },
                "run": self._web_search,
            },
            "web_fetch": {
                "desc": "Fetch the text content of a web page URL (strips HTML).",
                "params": {"url": "string (http/https URL)"},
                "run": self._web_fetch,
            },
            "generate_pdf": {
                "desc": "Generate a professional PDF document from markdown-like content. "
                        "Supports headings (#, ##, ###), paragraphs, bullet lists (- or *), "
                        "numbered lists (1. 2.), code blocks (```), blockquotes (>), "
                        "tables (| col | col |), page breaks (---), bold (**text**), "
                        "and italic (*text*). "
                        "EXAMPLE: {\"name\": \"generate_pdf\", \"args\": {\"path\": \"report.pdf\", "
                        "\"content\": \"# Title\\n\\nContent here\", \"title\": \"My Report\"}}",
                "params": {
                    "path": "string (output .pdf file path, must end with .pdf)",
                    "content": "string (markdown-like document content with headings, code, etc)",
                    "title": "string (optional, document title for cover page)",
                    "author": "string (optional, document author name)",
                },
                "run": self._generate_pdf,
            },
            "read_pdf": {
                "desc": "Extract and return text content from a PDF file.",
                "params": {
                    "path": "string (path to .pdf file)",
                    "pages": "string (optional, page range e.g. '1-3' or '1,3,5')",
                },
                "run": self._read_pdf,
            },
            "merge_pdf": {
                "desc": "Merge multiple PDF files into a single output PDF.",
                "params": {
                    "output": "string (output .pdf file path)",
                    "inputs": "string (comma-separated list of input .pdf paths)",
                },
                "run": self._merge_pdf,
            },
            # Quantum-inspired tools
            "quantum_optimize": {
                "desc": "Quantum-inspired optimization for scheduling, routing, resource allocation.",
                "params": {"cost_function": "string", "initial_state": "string (JSON)"},
                "run": self._quantum_optimize,
            },
            "quantum_search": {
                "desc": "Quantum-inspired search in list (Grover-inspired).",
                "params": {"data": "string (JSON array)", "target": "string"},
                "run": self._quantum_search,
            },
            "quantum_sort": {
                "desc": "Quantum-inspired parallel sort.",
                "params": {"data": "string (JSON array)"},
                "run": self._quantum_sort,
            },
            "quantum_probability": {
                "desc": "Calculate quantum probability distribution.",
                "params": {"outcomes": "string (JSON array)", "weights": "string (JSON array)"},
                "run": self._quantum_probability,
            },
            "quantum_correlate": {
                "desc": "Quantum correlation score between feature sets.",
                "params": {"features_a": "string (JSON array)", "features_b": "string (JSON array)"},
                "run": self._quantum_correlate,
            },
            # NEW Quantum Tools
            "quantum_neural": {
                "desc": "Quantum Neural Network for pattern recognition/classification.",
                "params": {"inputs": "string (JSON array)", "weights": "string (JSON 2D array)", "activation": "string (sigmoid/relu/tanh)"},
                "run": self._quantum_neural,
            },
            "quantum_cluster": {
                "desc": "Quantum-inspired K-means clustering.",
                "params": {"data": "string (JSON 2D array)", "n_clusters": "int", "iterations": "int"},
                "run": self._quantum_cluster,
            },
            "quantum_pathfind": {
                "desc": "Quantum-inspired Dijkstra pathfinding.",
                "params": {"graph": "string (JSON adjacency dict)", "start": "string", "end": "string"},
                "run": self._quantum_pathfind,
            },
            "quantum_encrypt": {
                "desc": "Quantum-inspired encryption.",
                "params": {"data": "string", "key": "string"},
                "run": self._quantum_encrypt,
            },
            "quantum_decrypt": {
                "desc": "Quantum-inspired decryption.",
                "params": {"encrypted": "string (hex)", "key": "string"},
                "run": self._quantum_decrypt,
            },
            "quantum_recommend": {
                "desc": "Quantum-inspired recommendation system.",
                "params": {"preferences": "string (JSON)", "items": "string (JSON array)", "top_n": "int"},
                "run": self._quantum_recommend,
            },
            "quantum_anomaly": {
                "desc": "Quantum-inspired anomaly detection.",
                "params": {"data": "string (JSON array)", "threshold": "float"},
                "run": self._quantum_anomaly,
            },
            "quantum_forecast": {
                "desc": "Quantum-inspired time series forecasting.",
                "params": {"data": "string (JSON array)", "steps": "int"},
                "run": self._quantum_forecast,
            },
            "quantum_importance": {
                "desc": "Quantum-inspired feature importance analysis.",
                "params": {"features": "string (JSON array)", "data": "string (JSON array)", "target": "string"},
                "run": self._quantum_importance,
            },
            # Obsidian Integration
            "obsidian_set_vault": {
                "desc": "Set Obsidian vault path. Call this first before other Obsidian tools.",
                "params": {"path": "string (path to Obsidian vault folder)"},
                "run": self._obsidian_set_vault,
            },
            "obsidian_list_notes": {
                "desc": "List all notes in Obsidian vault.",
                "params": {"folder": "string (optional, subfolder to list)", "recursive": "bool (default true)"},
                "run": self._obsidian_list_notes,
            },
            "obsidian_read_note": {
                "desc": "Read a note from Obsidian vault.",
                "params": {"note_path": "string (path relative to vault, e.g. 'notes/my-note.md')"},
                "run": self._obsidian_read_note,
            },
            "obsidian_write_note": {
                "desc": "Write/create a note in Obsidian vault.",
                "params": {"note_path": "string (path relative to vault)", "content": "string (markdown content)", "tags": "string (optional, comma-separated tags)"},
                "run": self._obsidian_write_note,
            },
            "obsidian_search": {
                "desc": "Search notes in Obsidian vault by content or title.",
                "params": {"query": "string (search term)", "folder": "string (optional, limit to subfolder)"},
                "run": self._obsidian_search,
            },
            "obsidian_daily_note": {
                "desc": "Create or read today's daily note in Obsidian.",
                "params": {"content": "string (optional, content for the note)"},
                "run": self._obsidian_daily_note,
            },
            "obsidian_link_notes": {
                "desc": "Add a link from one note to another in Obsidian.",
                "params": {"source": "string (source note path)", "target": "string (target note name)"},
                "run": self._obsidian_link_notes,
            },
            # Feed & Timeline
            "feed_add": {
                "desc": "Add an activity to Mythos feed (like a social media post).",
                "params": {"type": "string (note/task/achievement/idea)", "title": "string", "content": "string", "tags": "string (comma-separated)"},
                "run": self._feed_add,
            },
            "feed_view": {
                "desc": "View recent activities in Mythos feed.",
                "params": {"limit": "int (default 10)", "type": "string (optional filter)"},
                "run": self._feed_view,
            },
            "feed_search": {
                "desc": "Search activities in Mythos feed.",
                "params": {"query": "string"},
                "run": self._feed_search,
            },
            "feed_stats": {
                "desc": "Get feed statistics (total activities, today, this week).",
                "params": {},
                "run": self._feed_stats,
            },
            # Obsidian Sync
            "obsidian_sync": {
                "desc": "Sync all Mythos data (feed, notes, projects) to Obsidian vault.",
                "params": {"vault_path": "string (optional, Obsidian vault path)"},
                "run": self._obsidian_sync,
            },
            "obsidian_sync_feed": {
                "desc": "Sync Mythos feed activities to Obsidian vault.",
                "params": {"vault_path": "string (optional)"},
                "run": self._obsidian_sync_feed,
            },
            "obsidian_sync_memory": {
                "desc": "Sync Mythos memory (conversations, facts, preferences) to Obsidian vault automatically.",
                "params": {"vault_path": "string (optional)"},
                "run": self._obsidian_sync_memory,
            },
            # Smart AI
            "smart_reflect": {
                "desc": "AI self-reflection - critique own response and suggest improvements.",
                "params": {"question": "string", "response": "string"},
                "run": self._smart_reflect,
            },
            "smart_confidence": {
                "desc": "Calculate confidence score for a response.",
                "params": {"question": "string", "response": "string"},
                "run": self._smart_confidence,
            },
            "smart_validate": {
                "desc": "Validate AI output before showing to user.",
                "params": {"output": "string", "type": "string (text/code/json)"},
                "run": self._smart_validate,
            },
            "smart_stats": {
                "desc": "Get Smart AI statistics (mistakes, knowledge, confidence).",
                "params": {},
                "run": self._smart_stats,
            },
        }

    @property
    def names(self) -> List[str]:
        return list(self._tools.keys())

    def schema_for_prompt(self) -> str:
        """Render a compact schema string for the AI system prompt."""
        lines = []
        for name, spec in self._tools.items():
            params = ", ".join(spec["params"].keys())
            lines.append(f"- {name}({params}): {spec['desc']}")
        return "\n".join(lines)

    # ----------------------- Path safety ----------------------- #
    def _resolve(self, path: str) -> str:
        """Resolve a path against cwd; return absolute normalized path.
        Blocks path traversal outside of cwd for security."""
        if os.path.isabs(path):
            p = os.path.normpath(path)
        else:
            p = os.path.normpath(os.path.join(self.cwd, path))
        # Security: ensure resolved path stays under cwd
        if not p.startswith(self.cwd):
            p = os.path.join(self.cwd, os.path.basename(p))
        return p

    # ----------------------- Tool implementations ----------------------- #
    def _read_file(self, path: str, **_) -> ToolResult:
        full = self._resolve(path)
        if not os.path.isfile(full):
            return ToolResult(False, "", f"Not a file: {full}")
        content = self.executor.safe_read(full, max_bytes=1_000_000)
        if content is None:
            return ToolResult(False, "", f"Cannot read (too large or unreadable): {full}")
        # Truncate for AI context.
        if len(content) > 60_000:
            content = content[:60_000] + f"\n... [truncated, {len(content)} chars total]"
        return ToolResult(True, content)

    def _write_file(self, path: str, content: str = "", **_) -> ToolResult:
        full = self._resolve(path)
        ok = self.executor.atomic_write(full, content)
        if not ok:
            return ToolResult(False, "", f"Failed to write: {full}")
        n = len(content.encode("utf-8"))
        return ToolResult(True, f"Wrote {n:,} bytes -> {full}")

    def _list_dir(self, path: str = ".", **_) -> ToolResult:
        full = self._resolve(path)
        if not os.path.isdir(full):
            return ToolResult(False, "", f"Not a directory: {full}")
        try:
            entries = sorted(os.listdir(full))
        except OSError as e:
            return ToolResult(False, "", str(e))
        if not entries:
            return ToolResult(True, "(empty directory)")
        lines = []
        for e in entries[:500]:
            ep = os.path.join(full, e)
            tag = "DIR " if os.path.isdir(ep) else "FILE"
            size = ""
            try:
                if os.path.isfile(ep):
                    size = f" ({os.path.getsize(ep):,}b)"
            except OSError:
                pass
            lines.append(f"{tag:4} {e}{size}")
        out = "\n".join(lines)
        if len(entries) > 500:
            out += f"\n... [{len(entries) - 500} more entries]"
        return ToolResult(True, out)

    def _search(self, pattern: str, path: str = ".", glob: str = "*",
                **_) -> ToolResult:
        full = self._resolve(path)
        if not os.path.isdir(full):
            return ToolResult(False, "", f"Not a directory: {full}")
        try:
            rx = re.compile(pattern)
        except re.error as e:
            return ToolResult(False, "", f"Invalid regex '{pattern}': {e}")
        matches: List[str] = []
        count = 0
        max_results = 200
        for root, dirs, files in os.walk(full):
            # Skip hidden / heavy dirs.
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                       {"node_modules", "__pycache__", ".git", "venv", "env"}]
            for fn in files:
                if not fnmatch.fnmatch(fn, glob):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        for lineno, line in enumerate(f, 1):
                            if rx.search(line):
                                rel = os.path.relpath(fp, full)
                                matches.append(f"{rel}:{lineno}: {line.rstrip()[:200]}")
                                count += 1
                                if count >= max_results:
                                    matches.append(
                                        f"... [truncated at {max_results} matches]"
                                    )
                                    return ToolResult(True, "\n".join(matches))
                except OSError:
                    continue
        if not matches:
            return ToolResult(True, f"No matches for /{pattern}/ in {full}")
        return ToolResult(True, "\n".join(matches))

    def _run_shell(self, command: str, shell: Optional[str] = None, **_) -> ToolResult:
        if not command or not command.strip():
            return ToolResult(False, "", "Empty command.")
        result = self.executor.run(command, shell=shell, cwd=self.cwd)
        parts = []
        if result.stdout.strip():
            parts.append(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr.strip():
            parts.append(f"STDERR:\n{result.stderr.strip()}")
        if not parts:
            parts.append("(no output)")
        out = "\n".join(parts) + f"\n[exit {result.exit_code}, {result.shell}, {result.duration:.2f}s]"
        return ToolResult(result.success, out, "" if result.success else f"exit {result.exit_code}")

    def _ask_user(self, question: str, **_) -> ToolResult:
        if self.ui_hook:
            try:
                answer = self.ui_hook(question)
                return ToolResult(True, f"User answered: {answer}")
            except Exception as e:
                return ToolResult(False, "", f"ask_user failed: {e}")
        return ToolResult(False, "", "ask_user not available (no UI hook).")

    def _ask_choice(self, question: str, options: Any = None, **_) -> ToolResult:
        """Ask the user to pick one option from a list."""
        if self.choice_hook is None:
            return ToolResult(False, "", "ask_choice not available (no choice hook).")
        # Normalize options to a list of strings.
        if isinstance(options, str):
            opts = [o.strip() for o in options.split("|") if o.strip()]
        elif isinstance(options, (list, tuple)):
            opts = [str(o) for o in options]
        else:
            return ToolResult(False, "",
                              "ask_choice requires 'options' as a list/array.")
        # Remove duplicates but keep order.
        seen = set()
        opts = [o for o in opts if not (o in seen or seen.add(o))]
        if len(opts) < 2:
            return ToolResult(False, "",
                              "ask_choice needs at least 2 distinct options.")
        if len(opts) > 12:
            return ToolResult(False, "",
                              f"Too many options ({len(opts)}). Maximum 12.")
        try:
            idx = self.choice_hook(question, opts)
        except Exception as e:
            return ToolResult(False, "", f"ask_choice failed: {e}")
        if idx is None:
            return ToolResult(True, "User cancelled the choice.")
        # Bounds check to prevent IndexError
        if not isinstance(idx, int) or idx < 0 or idx >= len(opts):
            return ToolResult(False, "", f"Invalid selection index: {idx}")
        chosen = opts[idx]
        # Return both the chosen option AND its index so the AI has full info.
        return ToolResult(True,
                          f"User chose option {idx + 1}: {chosen}\n"
                          f"(index {idx} of {opts})")

    def _ask_confirm(self, question: str, **_) -> ToolResult:
        """Ask the user a yes/no confirmation."""
        if self.confirm_hook is None:
            return ToolResult(False, "", "ask_confirm not available (no confirm hook).")
        try:
            ok = self.confirm_hook(question)
        except Exception as e:
            return ToolResult(False, "", f"ask_confirm failed: {e}")
        return ToolResult(True, "User confirmed: YES" if ok else "User declined: NO")

    # ----------------------- Web tools ----------------------- #
    _WEB_HEADERS = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def _web_search(self, query: str, max_results: int = 5, **_) -> ToolResult:
        """Search the web via Wikipedia OpenSearch API (no key, JSON, fast)."""
        if not query or not query.strip():
            return ToolResult(False, "", "Empty query.")
        try:
            max_results = max(1, min(int(max_results), 10))
        except (TypeError, ValueError):
            max_results = 5
        try:
            import requests
        except ImportError:
            return ToolResult(False, "", "requests not installed.")

        # OpenSearch returns: [query, [titles], [descriptions], [urls]]
        params = {
            "action": "opensearch",
            "search": query,
            "limit": max_results,
            "namespace": 0,
            "format": "json",
            "origin": "*",
        }
        try:
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params=params, headers=self._WEB_HEADERS, timeout=15,
            )
        except requests.RequestException as e:
            return ToolResult(False, "", f"Search request failed: {e}")

        if resp.status_code != 200:
            return ToolResult(False, "",
                              f"Search HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError:
            return ToolResult(False, "", "Search returned non-JSON response.")

        if not isinstance(data, list) or len(data) < 4:
            return ToolResult(True, f"No results found for: {query}")
        titles = data[1] or []
        descriptions = data[2] or []
        urls = data[3] or []
        if not titles:
            return ToolResult(True, f"No results found for: {query}")

        lines = [f"Web search: {query}", f"({len(titles)} results)", ""]
        for i in range(len(titles)):
            title = html.unescape(titles[i]).strip()
            snippet = (html.unescape(descriptions[i]).strip()
                       if i < len(descriptions) else "")
            url = urls[i] if i < len(urls) else ""
            lines.append(f"{i+1}. {title}")
            if snippet:
                lines.append(f"   {snippet}")
            if url:
                lines.append(f"   URL: {url}")
            lines.append("")
        return ToolResult(True, "\n".join(lines))

    def _web_fetch(self, url: str, **_) -> ToolResult:
        """Fetch a web page and return its text content (HTML stripped)."""
        if not url or not url.strip():
            return ToolResult(False, "", "Empty URL.")
        url = url.strip()
        if not re.match(r"^https?://", url, re.IGNORECASE):
            return ToolResult(False, "", f"Invalid URL (must start with http/https): {url}")
        try:
            import requests
        except ImportError:
            return ToolResult(False, "", "requests not installed.")
        try:
            resp = requests.get(url, headers=self._WEB_HEADERS, timeout=20)
        except requests.RequestException as e:
            return ToolResult(False, "", f"Fetch failed: {e}")
        if resp.status_code != 200:
            return ToolResult(False, "",
                              f"HTTP {resp.status_code} for {url}")
        text = self._html_to_text(resp.text)
        # Truncate for AI context.
        max_chars = 16_000
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... [truncated, {len(text)} chars total]"
        header = f"Fetched {url} ({len(text)} chars):\n\n"
        return ToolResult(True, header + text.strip() or "(empty page)")

    def _html_to_text(self, raw_html: str) -> str:
        """Strip HTML tags + scripts, return readable text."""
        # Remove script/style blocks entirely.
        text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>",
                      "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        # Block tags -> newline.
        text = re.sub(r"<(p|div|br|h[1-6]|li|tr|hr)[^>]*>",
                      "\n", text, flags=re.IGNORECASE)
        # Strip all remaining tags.
        text = re.sub(r"<[^>]+>", "", text)
        # Decode HTML entities.
        text = html.unescape(text)
        # Collapse whitespace.
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    # ----------------------- PDF tools ----------------------- #
    def _generate_pdf(self, path: str, content: str = "", title: str = "",
                      author: str = "", **_) -> ToolResult:
        """Generate a professional PDF from markdown-like content."""
        if not path or not path.strip():
            return ToolResult(False, "", "Empty output path.")
        if not content or not content.strip():
            return ToolResult(False, "", "Empty content — nothing to render.")
        full = self._resolve(path)
        if not full.lower().endswith(".pdf"):
            full += ".pdf"
        try:
            from fpdf import FPDF  # noqa: F401
        except ImportError:
            return ToolResult(False, "", "fpdf2 not installed. Run: pip install fpdf2")
        try:
            pdf = _create_mythos_pdf(orientation="P", unit="mm", format="A4")
            pdf.set_auto_page_break(auto=True, margin=25)
            pdf.set_author(author or "Mythos AI")
            pdf.set_title(title or os.path.basename(full))
            # Determine which font family to use.
            uni = getattr(pdf, "_mythos_uni_font", None)
            pdf._body_font = uni or "Helvetica"
            pdf._mono_font = "Courier"
            pdf._doc_title = title or ""
            pdf._doc_author = author or "Mythos AI"
            # --- Cover page ---
            _render_cover_page(pdf, title, author)
            # --- Content pages ---
            pdf.add_page()
            pdf.set_margins(20, 25, 20)
            pdf.set_y(25)
            pdf.set_x(20)
            self._render_pdf_content(pdf, content, "")
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            pdf.output(full)
            size_kb = os.path.getsize(full) / 1024
            return ToolResult(
                True,
                f"PDF generated: {full} ({size_kb:.1f} KB, "
                f"{pdf.page_no()} pages)"
            )
        except Exception as e:
            return ToolResult(False, "", f"PDF generation failed: {e}")

    def _render_pdf_content(self, pdf, content: str, doc_title: str) -> None:
        """Parse markdown-like content and render with Mythos Glasswing styling."""
        import re as _re
        F = getattr(pdf, "_body_font", "Helvetica")
        LM = 20   # left margin
        RM = pdf.w - 20  # right edge

        lines = content.split("\n")
        i = 0
        in_code_block = False
        code_lines: list = []
        in_table = False
        table_rows: list = []

        def _flush_table():
            nonlocal table_rows, in_table
            if not table_rows:
                return
            _render_table(pdf, table_rows)
            table_rows = []
            in_table = False

        def _flush_code():
            nonlocal code_lines, in_code_block
            if not code_lines:
                return
            _render_code_block(pdf, "\n".join(code_lines))
            code_lines = []
            in_code_block = False

        while i < len(lines):
            line = lines[i]

            # --- Code fence toggle ---
            if line.strip().startswith("```"):
                if in_code_block:
                    _flush_code()
                else:
                    _flush_table()
                    in_code_block = True
                i += 1
                continue
            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # --- Table detection (| col | col |) ---
            if _re.match(r"^\s*\|.*\|\s*$", line):
                if _re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
                    i += 1
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not in_table:
                    in_table = True
                table_rows.append(cells)
                i += 1
                continue
            else:
                if in_table:
                    _flush_table()

            stripped = line.strip()

            # --- Page break ---
            if stripped in ("---", "***", "___"):
                pdf.add_page()
                pdf.set_y(25)
                pdf.set_x(LM)
                i += 1
                continue

            # --- Headings ---
            h3 = _re.match(r"^###\s+(.+)", stripped)
            h2 = _re.match(r"^##\s+(.+)", stripped)
            h1 = _re.match(r"^#\s+(.+)", stripped)
            if h1:
                pdf.ln(8)
                y = pdf.get_y()
                # Cyan accent bar on left.
                pdf.set_fill_color(*_C_CYAN)
                pdf.rect(LM, y, 2.5, 9, "F")
                pdf.set_x(LM + 6)
                pdf.set_font(F, "B", 19)
                pdf.set_text_color(*_C_DARK)
                pdf.multi_cell(RM - LM - 6, 9, h1.group(1))
                pdf.ln(1)
                # Subtle underline.
                ux = pdf.get_y()
                pdf.set_draw_color(*_C_CYAN_LIGHT)
                pdf.set_line_width(0.3)
                pdf.line(LM, ux, RM, ux)
                pdf.ln(4)
                pdf.set_x(LM)
            elif h2:
                pdf.ln(6)
                y = pdf.get_y()
                # Shorter accent bar.
                pdf.set_fill_color(*_C_CYAN)
                pdf.rect(LM, y, 2, 7.5, "F")
                pdf.set_x(LM + 5)
                pdf.set_font(F, "B", 15)
                pdf.set_text_color(*_C_NAVY)
                pdf.multi_cell(RM - LM - 5, 7.5, h2.group(1))
                pdf.ln(3)
                pdf.set_x(LM)
            elif h3:
                pdf.ln(4)
                y = pdf.get_y()
                pdf.set_fill_color(*_C_CYAN_LIGHT)
                pdf.rect(LM, y, 1.5, 6, "F")
                pdf.set_x(LM + 4)
                pdf.set_font(F, "B", 12)
                pdf.set_text_color(*_C_NAVY)
                pdf.multi_cell(RM - LM - 4, 6, h3.group(1))
                pdf.ln(2)
                pdf.set_x(LM)
            # --- Blockquote ---
            elif stripped.startswith(">"):
                quote_text = stripped.lstrip(">").strip()
                y = pdf.get_y()
                # Background panel.
                qh = 7 + len(quote_text) // 60 * 6
                pdf.set_fill_color(*_C_FROST_BG)
                pdf.rect(LM, y, RM - LM, min(qh, 50), "F")
                # Left accent bar.
                pdf.set_fill_color(*_C_CYAN)
                pdf.rect(LM, y, 2, min(qh, 50), "F")
                pdf.set_x(LM + 6)
                pdf.set_font(F, "I", 10)
                pdf.set_text_color(*_C_FROST_TEXT)
                pdf.multi_cell(RM - LM - 10, 5.5, quote_text)
                pdf.ln(3)
                pdf.set_x(LM)
                pdf.set_text_color(*_C_BODY)
            # --- Bullet list ---
            elif _re.match(r"^[\-\*]\s+", stripped):
                item = _re.sub(r"^[\-\*]\s+", "", stripped)
                pdf.set_font(F, "", 10)
                pdf.set_text_color(*_C_BODY)
                pdf.set_x(LM + 6)
                # Crystal diamond bullet.
                pdf.set_fill_color(*_C_CYAN)
                bx = pdf.get_x()
                by = pdf.get_y() + 2.2
                pdf.rect(bx - 1, by, 2, 2, "F")
                pdf.set_x(LM + 11)
                self._write_rich_text(pdf, item, RM - LM - 11)
                pdf.ln(1.5)
                pdf.set_x(LM)
            # --- Numbered list ---
            elif _re.match(r"^\d+[.)\)]\s+", stripped):
                m_num = _re.match(r"^(\d+)([.)\)])\s+(.*)", stripped)
                num = m_num.group(1) if m_num else ""
                item = m_num.group(3) if m_num else stripped
                pdf.set_x(LM + 6)
                # Styled number badge.
                pdf.set_fill_color(*_C_NAVY)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font(F, "B", 8)
                nw = pdf.get_string_width(num) + 4
                pdf.cell(nw, 5, f" {num} ", fill=True, align="C")
                pdf.set_text_color(*_C_BODY)
                pdf.set_font(F, "", 10)
                pdf.set_x(LM + 6 + nw + 3)
                self._write_rich_text(pdf, item, RM - LM - nw - 9)
                pdf.ln(2)
                pdf.set_x(LM)
            # --- Empty line ---
            elif not stripped:
                pdf.ln(3)
            # --- Normal paragraph ---
            else:
                pdf.set_font(F, "", 10)
                pdf.set_text_color(*_C_BODY)
                self._write_rich_text(pdf, stripped, RM - LM)
                pdf.ln(2.5)
                pdf.set_x(LM)
            i += 1

        # Flush remaining blocks.
        if in_code_block:
            _flush_code()
        if in_table:
            _flush_table()

    def _write_rich_text(self, pdf, text: str, width: float) -> None:
        """Write text with inline **bold** and *italic* support."""
        import re as _re
        F = getattr(pdf, "_body_font", "Helvetica")
        parts = _re.split(r"(\*\*.*?\*\*|\*.*?\*)", text)
        line_h = 5.5
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                pdf.set_font(F, "B", 10)
                pdf.set_text_color(*_C_DARK)
                pdf.write(line_h, part[2:-2])
            elif part.startswith("*") and part.endswith("*") and len(part) > 2:
                pdf.set_font(F, "I", 10)
                pdf.set_text_color(*_C_NAVY_MID)
                pdf.write(line_h, part[1:-1])
            else:
                pdf.set_font(F, "", 10)
                pdf.set_text_color(*_C_BODY)
                pdf.write(line_h, part)
        pdf.ln(line_h)

    def _read_pdf(self, path: str, pages: str = "", **_) -> ToolResult:
        """Extract text from a PDF file."""
        if not path or not path.strip():
            return ToolResult(False, "", "Empty path.")
        full = self._resolve(path)
        if not os.path.isfile(full):
            return ToolResult(False, "", f"File not found: {full}")
        try:
            from pypdf import PdfReader
        except ImportError:
            return ToolResult(False, "", "pypdf not installed. Run: pip install pypdf")
        try:
            reader = PdfReader(full)
            total = len(reader.pages)
            if total == 0:
                return ToolResult(True, "PDF has no pages.")
            # Parse page range.
            page_indices = self._parse_page_range(pages, total) if pages else list(range(total))
            texts = []
            for idx in page_indices:
                if 0 <= idx < total:
                    page_text = reader.pages[idx].extract_text() or ""
                    texts.append(f"--- Page {idx + 1} ---\n{page_text.strip()}")
            result = "\n\n".join(texts)
            if not result.strip():
                result = "(no extractable text — PDF may contain only images)"
            # Truncate for AI context.
            if len(result) > 40_000:
                result = result[:40_000] + f"\n... [truncated, {len(result)} chars total]"
            header = f"PDF: {full} ({total} pages, extracted {len(page_indices)} pages):\n\n"
            return ToolResult(True, header + result)
        except Exception as e:
            return ToolResult(False, "", f"PDF read failed: {e}")

    def _merge_pdf(self, output: str, inputs: str = "", **_) -> ToolResult:
        """Merge multiple PDF files into one."""
        if not output or not output.strip():
            return ToolResult(False, "", "Empty output path.")
        if not inputs or not inputs.strip():
            return ToolResult(False, "", "No input PDFs specified.")
        out_full = self._resolve(output)
        if not out_full.lower().endswith(".pdf"):
            out_full += ".pdf"
        input_paths = [p.strip() for p in inputs.split(",") if p.strip()]
        if len(input_paths) < 2:
            return ToolResult(False, "", "Need at least 2 PDFs to merge.")
        try:
            from pypdf import PdfWriter
        except ImportError:
            return ToolResult(False, "", "pypdf not installed. Run: pip install pypdf")
        try:
            writer = PdfWriter()
            merged = []
            for inp in input_paths:
                inp_full = self._resolve(inp)
                if not os.path.isfile(inp_full):
                    return ToolResult(False, "", f"Input PDF not found: {inp_full}")
                reader_obj = __import__("pypdf", fromlist=["PdfReader"]).PdfReader(inp_full)
                for page in reader_obj.pages:
                    writer.add_page(page)
                merged.append(os.path.basename(inp_full))
            os.makedirs(os.path.dirname(out_full) or ".", exist_ok=True)
            with open(out_full, "wb") as f:
                writer.write(f)
            size_kb = os.path.getsize(out_full) / 1024
            return ToolResult(
                True,
                f"Merged {len(merged)} PDFs -> {out_full} ({size_kb:.1f} KB)\n"
                f"Sources: {', '.join(merged)}"
            )
        except Exception as e:
            return ToolResult(False, "", f"PDF merge failed: {e}")

    def _parse_page_range(self, spec: str, total: int) -> list:
        """Parse a page spec like '1-3' or '1,3,5' into 0-based indices."""
        indices = set()
        for part in spec.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                try:
                    start = max(1, int(a.strip()))
                    end = min(total, int(b.strip()))
                    indices.update(range(start - 1, end))
                except ValueError:
                    continue
            else:
                try:
                    idx = int(part) - 1
                    if 0 <= idx < total:
                        indices.add(idx)
                except ValueError:
                    continue
        return sorted(indices)

    # ----------------------- Quantum Tools ----------------------- #
    def _quantum_optimize(self, cost_function: str = "", initial_state: str = "[]", **_) -> ToolResult:
        """Quantum-inspired optimization."""
        try:
            import json
            from .quantum import quantum_annealing_optimize

            initial = json.loads(initial_state) if initial_state else []

            # Use provided cost_function or fallback to default
            if cost_function and cost_function.strip():
                # Try to parse as JSON array of costs, else use as expression
                try:
                    costs = json.loads(cost_function)
                    def custom_cost(state):
                        if isinstance(state, list) and len(state) <= len(costs):
                            return sum(costs[i] for i in state if i < len(costs))
                        return len(state)
                    cost_fn = custom_cost
                except json.JSONDecodeError:
                    cost_fn = lambda state: len(state) if isinstance(state, list) else 0
            else:
                cost_fn = lambda state: len(state) if isinstance(state, list) else 0

            result = quantum_annealing_optimize(cost_fn, initial)
            return ToolResult(True, f"Optimized result: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Optimization error: {e}")

    def _quantum_search(self, data: str = "[]", target: str = "", **_) -> ToolResult:
        """Quantum-inspired search in list."""
        try:
            import json
            from .quantum import grover_search

            data_list = json.loads(data) if data else []
            idx = grover_search(data_list, target)

            if idx >= 0:
                return ToolResult(True, f"Found '{target}' at index {idx}")
            return ToolResult(True, f"'{target}' not found in list")
        except Exception as e:
            return ToolResult(False, "", f"Search error: {e}")

    def _quantum_sort(self, data: str = "[]", **_) -> ToolResult:
        """Quantum-inspired sort."""
        try:
            import json
            from .quantum import quantum_sort

            data_list = json.loads(data) if data else []
            sorted_data = quantum_sort(data_list)
            return ToolResult(True, f"Sorted: {sorted_data}")
        except Exception as e:
            return ToolResult(False, "", f"Sort error: {e}")

    def _quantum_probability(self, outcomes: str = "[]", weights: str = "[]", **_) -> ToolResult:
        """Quantum probability distribution."""
        try:
            import json
            from .quantum import quantum_probability_distribution

            outcomes_list = json.loads(outcomes) if outcomes else []
            weights_list = json.loads(weights) if weights else []
            dist = quantum_probability_distribution(outcomes_list, weights_list)
            return ToolResult(True, f"Distribution: {dist}")
        except Exception as e:
            return ToolResult(False, "", f"Probability error: {e}")

    def _quantum_correlate(self, features_a: str = "[]", features_b: str = "[]", **_) -> ToolResult:
        """Quantum correlation score."""
        try:
            import json
            from .quantum import quantum_entanglement_score

            a = json.loads(features_a) if features_a else []
            b = json.loads(features_b) if features_b else []
            score = quantum_entanglement_score(a, b)
            return ToolResult(True, f"Correlation score: {score:.4f}")
        except Exception as e:
            return ToolResult(False, "", f"Correlation error: {e}")

    # ----------------------- NEW Quantum Tools ----------------------- #
    def _quantum_neural(self, inputs: str = "[]", weights: str = "[[]]", activation: str = "sigmoid", **_) -> ToolResult:
        """Quantum Neural Network."""
        try:
            import json
            from .quantum import quantum_neural_network

            inp = json.loads(inputs) if inputs else []
            w = json.loads(weights) if weights else [[]]
            
            # Validate dimensions
            if not inp:
                return ToolResult(False, "", "Inputs cannot be empty")
            if not w or not w[0]:
                return ToolResult(False, "", "Weights cannot be empty")
            for i, neuron_w in enumerate(w):
                if len(neuron_w) != len(inp):
                    return ToolResult(False, "", 
                        f"Dimension mismatch: neuron {i} has {len(neuron_w)} weights but input has {len(inp)} values")
            
            result = quantum_neural_network(inp, w, activation)
            return ToolResult(True, f"Neural output: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Neural error: {e}")

    def _quantum_cluster(self, data: str = "[[]]", n_clusters: int = 3, iterations: int = 100, **_) -> ToolResult:
        """Quantum clustering."""
        try:
            import json
            from .quantum import quantum_cluster

            d = json.loads(data) if data else []
            nc = int(n_clusters) if n_clusters else 3
            iters = int(iterations) if iterations else 100
            
            # Validate inputs
            if not d:
                return ToolResult(False, "", "Data cannot be empty")
            if nc <= 0:
                return ToolResult(False, "", "Number of clusters must be positive")
            
            # Warning if n_clusters > data points
            warning = ""
            if nc > len(d):
                warning = f" Warning: n_clusters ({nc}) > data points ({len(d)}), results may be suboptimal."
            
            result = quantum_cluster(d, nc, iters)
            return ToolResult(True, f"Cluster assignments: {result}{warning}")
        except Exception as e:
            return ToolResult(False, "", f"Cluster error: {e}")

    def _quantum_pathfind(self, graph: str = "{}", start: str = "", end: str = "", **_) -> ToolResult:
        """Quantum pathfinding."""
        try:
            import json
            from .quantum import quantum_pathfind

            g = json.loads(graph) if graph else {}
            
            # Validate inputs
            if not g:
                return ToolResult(False, "", "Graph cannot be empty")
            if not start:
                return ToolResult(False, "", "Start node is required")
            if not end:
                return ToolResult(False, "", "End node is required")
            
            # Validate nodes exist in graph
            if start not in g:
                return ToolResult(False, "", f"Start node '{start}' not found in graph. Available nodes: {list(g.keys())}")
            if end not in g:
                return ToolResult(False, "", f"End node '{end}' not found in graph. Available nodes: {list(g.keys())}")
            
            path, weight = quantum_pathfind(g, start, end)
            
            # Check if path was found
            if not path:
                return ToolResult(True, f"No path found from '{start}' to '{end}'")
            
            return ToolResult(True, f"Path: {path}, Total weight: {weight}")
        except Exception as e:
            return ToolResult(False, "", f"Pathfind error: {e}")

    def _quantum_encrypt(self, data: str = "", key: str = "", **_) -> ToolResult:
        """Quantum encryption."""
        try:
            from .quantum import quantum_encrypt
            
            # Validate inputs
            if not data:
                return ToolResult(False, "", "Data to encrypt cannot be empty")
            if not key or not key.strip():
                return ToolResult(False, "", "Encryption key cannot be empty")
            
            result = quantum_encrypt(data, key)
            return ToolResult(True, f"Encrypted: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Encrypt error: {e}")

    def _quantum_decrypt(self, encrypted: str = "", key: str = "", **_) -> ToolResult:
        """Quantum decryption."""
        try:
            from .quantum import quantum_decrypt
            
            # Validate inputs
            if not encrypted:
                return ToolResult(False, "", "Encrypted data cannot be empty")
            if not key or not key.strip():
                return ToolResult(False, "", "Decryption key cannot be empty")
            
            # Validate hex format
            if len(encrypted) % 2 != 0:
                return ToolResult(False, "", "Invalid encrypted data: must be even-length hex string")
            try:
                int(encrypted, 16)
            except ValueError:
                return ToolResult(False, "", "Invalid encrypted data: contains non-hex characters")
            
            result = quantum_decrypt(encrypted, key)
            return ToolResult(True, f"Decrypted: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Decrypt error: {e}")

    def _quantum_recommend(self, preferences: str = "{}", items: str = "[]", top_n: int = 5, **_) -> ToolResult:
        """Quantum recommendation."""
        try:
            import json
            from .quantum import quantum_recommend

            prefs = json.loads(preferences) if preferences else {}
            item_list = json.loads(items) if items else []
            result = quantum_recommend(prefs, item_list, top_n)
            return ToolResult(True, f"Recommendations: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Recommend error: {e}")

    def _quantum_anomaly(self, data: str = "[]", threshold: float = 2.0, **_) -> ToolResult:
        """Quantum anomaly detection."""
        try:
            import json
            from .quantum import quantum_anomaly_detection

            d = json.loads(data) if data else []
            t = float(threshold) if threshold else 2.0
            result = quantum_anomaly_detection(d, t)
            return ToolResult(True, f"Anomalies at indices: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Anomaly error: {e}")

    def _quantum_forecast(self, data: str = "[]", steps: int = 5, **_) -> ToolResult:
        """Quantum time series forecast."""
        try:
            import json
            from .quantum import quantum_time_series_forecast

            d = json.loads(data) if data else []
            s = int(steps) if steps else 5
            
            # Validate inputs
            if not d:
                return ToolResult(False, "", "Data cannot be empty")
            if len(d) < 2:
                return ToolResult(False, "", f"Need at least 2 data points for forecasting, got {len(d)}")
            if s <= 0:
                return ToolResult(False, "", "Forecast steps must be positive")
            
            result = quantum_time_series_forecast(d, s)
            return ToolResult(True, f"Forecast ({s} steps): {result}")
        except Exception as e:
            return ToolResult(False, "", f"Forecast error: {e}")

    def _quantum_importance(self, features: str = "[]", data: str = "[{}]", target: str = "", **_) -> ToolResult:
        """Quantum feature importance."""
        try:
            import json
            from .quantum import quantum_feature_importance

            f = json.loads(features) if features else []
            d = json.loads(data) if data else [{}]
            result = quantum_feature_importance(f, d, target)
            return ToolResult(True, f"Feature importance: {result}")
        except Exception as e:
            return ToolResult(False, "", f"Importance error: {e}")

    # ----------------------- Obsidian Tools ----------------------- #
    def _obsidian_set_vault(self, path: str = "", **_) -> ToolResult:
        """Set Obsidian vault path."""
        try:
            from .obsidian import obsidian
            if not path:
                return ToolResult(True, f"Current vault: {obsidian.vault_path}")
            if obsidian.set_vault(path):
                return ToolResult(True, f"Vault set to: {path}")
            return ToolResult(False, "", f"Invalid vault path: {path}")
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    def _obsidian_list_notes(self, folder: str = "", recursive: bool = True, **_) -> ToolResult:
        """List notes in Obsidian vault."""
        try:
            from .obsidian import obsidian
            notes = obsidian.list_notes(folder, recursive)
            if not notes:
                return ToolResult(True, "No notes found in vault.")
            
            result = f"Found {len(notes)} notes:\n"
            for note in notes[:20]:
                result += f"- {note['path']} ({note['size']} bytes)\n"
            if len(notes) > 20:
                result += f"... and {len(notes) - 20} more"
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    def _obsidian_read_note(self, note_path: str = "", **_) -> ToolResult:
        """Read a note from Obsidian vault."""
        try:
            from .obsidian import obsidian
            if not note_path:
                return ToolResult(False, "", "Note path is required")
            
            result = obsidian.read_note(note_path)
            if "error" in result:
                return ToolResult(False, "", result["error"])
            
            content = result["content"]
            if len(content) > 10000:
                content = content[:10000] + "\n... [truncated]"
            
            return ToolResult(True, f"Note: {note_path}\n\n{content}")
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    def _obsidian_write_note(self, note_path: str = "", content: str = "", tags: str = "", **_) -> ToolResult:
        """Write/create a note in Obsidian vault."""
        try:
            from .obsidian import obsidian
            if not note_path:
                return ToolResult(False, "", "Note path is required")
            
            frontmatter = {}
            if tags:
                frontmatter["tags"] = tags
            
            result = obsidian.write_note(note_path, content, frontmatter)
            if "error" in result:
                return ToolResult(False, "", result["error"])
            
            return ToolResult(True, f"Note created: {note_path} ({result['size']} bytes)")
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    def _obsidian_search(self, query: str = "", folder: str = "", **_) -> ToolResult:
        """Search notes in Obsidian vault."""
        try:
            from .obsidian import obsidian
            if not query:
                return ToolResult(False, "", "Search query is required")
            
            results = obsidian.search_notes(query, folder)
            if not results:
                return ToolResult(True, f"No results found for: {query}")
            
            output = f"Found {len(results)} results for '{query}':\n"
            for r in results[:10]:
                output += f"- {r['path']} ({r['matches']} matches): {r['preview']}\n"
            return ToolResult(True, output)
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    def _obsidian_daily_note(self, content: str = "", **_) -> ToolResult:
        """Create or read today's daily note."""
        try:
            from .obsidian import obsidian
            result = obsidian.create_daily_note(content)
            if "error" in result:
                return ToolResult(False, "", result["error"])
            return ToolResult(True, f"Daily note created: {result['path']}")
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    def _obsidian_link_notes(self, source: str = "", target: str = "", **_) -> ToolResult:
        """Add a link from source note to target note."""
        try:
            from .obsidian import obsidian
            if not source or not target:
                return ToolResult(False, "", "Both source and target are required")
            
            result = obsidian.link_notes(source, target)
            if "error" in result:
                return ToolResult(False, "", result["error"])
            return ToolResult(True, f"Link added: {source} -> [[{target}]]")
        except Exception as e:
            return ToolResult(False, "", f"Obsidian error: {e}")

    # ----------------------- Feed Tools ----------------------- #
    def _feed_add(self, type: str = "note", title: str = "", content: str = "", tags: str = "", **_) -> ToolResult:
        """Add an activity to Mythos feed."""
        try:
            from .feed import feed
            if not title:
                return ToolResult(False, "", "Title is required")
            
            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
            activity = feed.add_activity(type, title, content, tag_list)
            return ToolResult(True, f"Activity added: {title} (#{activity['id']})")
        except Exception as e:
            return ToolResult(False, "", f"Feed error: {e}")

    def _feed_view(self, limit: int = 10, type: str = "", **_) -> ToolResult:
        """View recent activities in feed."""
        try:
            from .feed import feed
            activities = feed.get_feed(limit, type if type else None)
            
            if not activities:
                return ToolResult(True, "No activities yet. Add one with feed_add!")
            
            result = f"Recent activities ({len(activities)}):\n\n"
            for a in activities:
                emoji = {"note": "📝", "task": "✅", "achievement": "🏆", "idea": "💡"}.get(a["type"], "📌")
                result += f"{emoji} [{a['type']}] {a['title']}\n"
                if a["content"]:
                    result += f"   {a['content'][:100]}...\n"
                result += f"   {a['timestamp'][:16]} | {a['likes']} likes | {len(a['comments'])} comments\n\n"
            
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Feed error: {e}")

    def _feed_search(self, query: str = "", **_) -> ToolResult:
        """Search activities in feed."""
        try:
            from .feed import feed
            if not query:
                return ToolResult(False, "", "Search query is required")
            
            results = feed.search_activities(query)
            if not results:
                return ToolResult(True, f"No results for: {query}")
            
            output = f"Found {len(results)} results:\n"
            for a in results[:10]:
                output += f"- {a['title']} ({a['type']})\n"
            return ToolResult(True, output)
        except Exception as e:
            return ToolResult(False, "", f"Feed error: {e}")

    def _feed_stats(self, **_) -> ToolResult:
        """Get feed statistics."""
        try:
            from .feed import feed
            stats = feed.get_stats()
            
            result = f"Mythos Feed Stats:\n"
            result += f"Total: {stats['total']} activities\n"
            result += f"Today: {stats['today']}\n"
            result += f"This week: {stats['this_week']}\n"
            
            if stats.get('by_type'):
                result += "\nBy type:\n"
                for t, count in stats['by_type'].items():
                    result += f"  {t}: {count}\n"
            
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Feed error: {e}")

    # ----------------------- Obsidian Sync Tools ----------------------- #
    def _obsidian_sync(self, vault_path: str = "", **_) -> ToolResult:
        """Sync all Mythos data to Obsidian."""
        try:
            from .obsidian_sync import obsidian_sync
            from .feed import feed
            
            if vault_path:
                obsidian_sync.set_vault(vault_path)
            
            # Get feed data
            feed_data = feed.get_feed(limit=100)
            
            # Perform full sync
            results = obsidian_sync.full_sync(feed_data=feed_data)
            
            output = "Mythos → Obsidian Sync Complete!\n\n"
            for key, result in results.items():
                if result.get("success"):
                    output += f"✓ {key}: synced\n"
                else:
                    output += f"✗ {key}: failed\n"
            
            output += f"\nVault: {obsidian_sync.vault_path}"
            output += f"\nOpen Obsidian to view your data!"
            
            return ToolResult(True, output)
        except Exception as e:
            return ToolResult(False, "", f"Sync error: {e}")

    def _obsidian_sync_feed(self, vault_path: str = "", **_) -> ToolResult:
        """Sync Mythos feed to Obsidian."""
        try:
            from .obsidian_sync import obsidian_sync
            from .feed import feed
            
            if vault_path:
                obsidian_sync.set_vault(vault_path)
            
            feed_data = feed.get_feed(limit=100)
            result = obsidian_sync.sync_feed(feed_data)
            
            if result.get("success"):
                return ToolResult(True, f"Feed synced! {result['synced']} activities → {result['folder']}")
            return ToolResult(False, "", "Sync failed")
        except Exception as e:
            return ToolResult(False, "", f"Sync error: {e}")

    def _obsidian_sync_memory(self, vault_path: str = "", **_) -> ToolResult:
        """Sync Mythos memory to Obsidian."""
        try:
            from .memory import sync_memory_to_obsidian
            
            result = sync_memory_to_obsidian(vault_path if vault_path else None)
            
            if result.get("success"):
                synced = result["synced"]
                output = f"Memory synced to Obsidian!\n\n"
                output += f"Vault: {result['vault']}\n\n"
                output += f"Synced:\n"
                output += f"  - Conversations: {synced['conversations']}\n"
                output += f"  - Facts: {synced['facts']}\n"
                output += f"  - Preferences: {synced['preferences']}\n"
                return ToolResult(True, output)
            return ToolResult(False, "", "Memory sync failed")
        except Exception as e:
            return ToolResult(False, "", f"Memory sync error: {e}")

    # ----------------------- Smart AI Tools ----------------------- #
    def _smart_reflect(self, question: str = "", response: str = "", **_) -> ToolResult:
        """AI self-reflection."""
        try:
            from .smart_ai import smart_ai
            if not question or not response:
                return ToolResult(False, "", "Both question and response are required")
            
            reflection = smart_ai.reflect_on_response(question, response)
            
            result = f"Self-Reflection:\n"
            result += f"Confidence: {reflection['confidence']:.0%}\n"
            
            if reflection["issues"]:
                result += f"\nIssues found:\n"
                for issue in reflection["issues"]:
                    result += f"  ⚠ {issue}\n"
            
            if reflection["suggestions"]:
                result += f"\nSuggestions:\n"
                for suggestion in reflection["suggestions"]:
                    result += f"  💡 {suggestion}\n"
            
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Smart AI error: {e}")

    def _smart_confidence(self, question: str = "", response: str = "", **_) -> ToolResult:
        """Calculate confidence score."""
        try:
            from .smart_ai import smart_ai
            if not question or not response:
                return ToolResult(False, "", "Both question and response are required")
            
            confidence = smart_ai.calculate_confidence(question, response)
            
            emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
            result = f"{emoji} Confidence: {confidence:.0%}\n"
            
            if confidence < 0.7:
                result += "\nLow confidence - consider:\n"
                result += "  - Providing more details\n"
                result += "  - Using tools for verification\n"
                result += "  - Asking for clarification\n"
            
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Smart AI error: {e}")

    def _smart_validate(self, output: str = "", type: str = "text", **_) -> ToolResult:
        """Validate AI output."""
        try:
            from .smart_ai import smart_ai
            if not output:
                return ToolResult(False, "", "Output is required")
            
            validation = smart_ai.validate_output(output, type)
            
            if validation["is_valid"]:
                result = f"✅ Output valid ({type})"
            else:
                result = f"❌ Output invalid ({type})\n"
                for issue in validation["issues"]:
                    result += f"  - {issue}\n"
            
            if validation.get("suggestions"):
                result += "\nSuggestions:\n"
                for suggestion in validation["suggestions"]:
                    result += f"  💡 {suggestion}\n"
            
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Smart AI error: {e}")

    def _smart_stats(self, **_) -> ToolResult:
        """Get Smart AI statistics."""
        try:
            from .smart_ai import smart_ai
            stats = smart_ai.get_stats()
            
            result = f"Smart AI Stats:\n"
            result += f"Total mistakes recorded: {stats['total_mistakes']}\n"
            result += f"Knowledge entries: {stats['knowledge_entries']}\n"
            result += f"Average confidence: {stats['avg_confidence']:.0%}\n"
            
            if stats.get('most_common_errors'):
                result += f"\nMost common errors:\n"
                for error in stats['most_common_errors']:
                    result += f"  - {error}\n"
            
            return ToolResult(True, result)
        except Exception as e:
            return ToolResult(False, "", f"Smart AI error: {e}")

    # ----------------------- Execution ----------------------- #
    def execute(self, call: ToolCall) -> ToolResult:
        """Execute a parsed tool call."""
        with self._lock:
            spec = self._tools.get(call.name)
            if not spec:
                return ToolResult(False, "", f"Unknown tool: {call.name}")
            try:
                return spec["run"](**call.args)
            except TypeError as e:
                return ToolResult(False, "", f"Bad args for {call.name}: {e}")
            except Exception as e:
                return ToolResult(False, "", f"{call.name} crashed: {e}")


# ----------------------- PDF rendering helpers ----------------------- #
# Mythos Glasswing color palette (R, G, B tuples).
_C_NAVY       = (22, 33, 62)     # Deep navy (primary dark)
_C_NAVY_MID   = (35, 50, 85)     # Mid navy
_C_CYAN       = (100, 220, 255)  # Bright ice cyan accent
_C_CYAN_LIGHT = (170, 230, 248)  # Soft cyan
_C_DARK       = (18, 18, 28)     # Near-black for headings
_C_BODY       = (42, 42, 52)     # Dark charcoal for body text
_C_FROST_TEXT = (80, 95, 115)    # Muted blue-gray
_C_FROST_BG   = (235, 242, 250)  # Frosted glass background
_C_WHITE      = (255, 255, 255)
_C_TABLE_HEAD = (22, 33, 62)     # Navy header
_C_TABLE_ALT  = (240, 245, 252)  # Alternating row
_C_CODE_BG    = (28, 32, 44)     # Dark terminal bg
_C_CODE_TEXT  = (210, 225, 240)  # Light terminal text
_C_CODE_EDGE  = (100, 220, 255)  # Cyan border for code


def _render_cover_page(pdf, title: str, author: str) -> None:
    """Render a premium Mythos Glasswing cover page."""
    F = getattr(pdf, "_body_font", "Helvetica")
    W = pdf.w
    H = pdf.h
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # Full dark navy background.
    pdf.set_fill_color(*_C_NAVY)
    pdf.rect(0, 0, W, H, "F")

    # Top decorative gradient-like band (cyan -> navy fade simulation).
    for s in range(12):
        alpha = 1.0 - (s / 12.0)
        r = int(_C_CYAN[0] * alpha + _C_NAVY[0] * (1 - alpha))
        g = int(_C_CYAN[1] * alpha + _C_NAVY[1] * (1 - alpha))
        b = int(_C_CYAN[2] * alpha + _C_NAVY[2] * (1 - alpha))
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, s * 3, W, 3, "F")

    # Decorative wing-like geometric motif.
    pdf.set_draw_color(*_C_CYAN)
    pdf.set_line_width(0.4)
    cx = W / 2
    cy = H * 0.28
    # Diamond shape.
    d = 18
    pdf.line(cx, cy - d, cx + d, cy)
    pdf.line(cx + d, cy, cx, cy + d)
    pdf.line(cx, cy + d, cx - d, cy)
    pdf.line(cx - d, cy, cx, cy - d)
    # Inner diamond.
    d2 = 10
    pdf.set_line_width(0.25)
    pdf.line(cx, cy - d2, cx + d2, cy)
    pdf.line(cx + d2, cy, cx, cy + d2)
    pdf.line(cx, cy + d2, cx - d2, cy)
    pdf.line(cx - d2, cy, cx, cy - d2)
    # Horizontal wing lines.
    pdf.set_line_width(0.3)
    pdf.line(cx - d - 20, cy, cx - d, cy)
    pdf.line(cx + d, cy, cx + d + 20, cy)
    pdf.line(cx - d - 14, cy - 4, cx - d - 3, cy - 4)
    pdf.line(cx + d + 3, cy - 4, cx + d + 14, cy - 4)
    pdf.line(cx - d - 14, cy + 4, cx - d - 3, cy + 4)
    pdf.line(cx + d + 3, cy + 4, cx + d + 14, cy + 4)

    # "MYTHOS" title.
    pdf.set_font(F, "B", 38)
    pdf.set_text_color(*_C_CYAN)
    pdf.set_xy(0, H * 0.40)
    pdf.cell(W, 16, "MYTHOS", align="C")

    # Subtitle line.
    pdf.set_font(F, "", 11)
    pdf.set_text_color(*_C_CYAN_LIGHT)
    pdf.set_xy(0, H * 0.40 + 18)
    pdf.cell(W, 6, "crystalline intelligence", align="C")

    # Decorative separator.
    sep_y = H * 0.52
    pdf.set_draw_color(*_C_CYAN)
    pdf.set_line_width(0.5)
    pdf.line(W * 0.25, sep_y, W * 0.75, sep_y)
    pdf.set_fill_color(*_C_CYAN)
    pdf.rect(W * 0.49, sep_y - 1.5, W * 0.02, 3, "F")

    # Document title (if provided).
    if title:
        pdf.set_font(F, "B", 22)
        pdf.set_text_color(*_C_WHITE)
        pdf.set_xy(25, H * 0.57)
        pdf.multi_cell(W - 50, 10, title, align="C")

    # Author.
    pdf.set_font(F, "", 12)
    pdf.set_text_color(*_C_CYAN_LIGHT)
    author_line = author or "Mythos AI"
    pdf.set_xy(0, H * 0.72)
    pdf.cell(W, 8, author_line, align="C")

    # Date.
    import datetime
    pdf.set_font(F, "", 10)
    pdf.set_text_color(140, 160, 180)
    pdf.set_xy(0, H * 0.72 + 12)
    pdf.cell(W, 6, datetime.date.today().strftime("%B %d, %Y"), align="C")

    # Bottom decorative band.
    for s in range(8):
        alpha = s / 8.0
        r = int(_C_CYAN[0] * alpha + _C_NAVY[0] * (1 - alpha))
        g = int(_C_CYAN[1] * alpha + _C_NAVY[1] * (1 - alpha))
        b = int(_C_CYAN[2] * alpha + _C_NAVY[2] * (1 - alpha))
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, H - 24 + s * 3, W, 3, "F")

    # Footer text.
    pdf.set_font(F, "I", 8)
    pdf.set_text_color(120, 140, 160)
    pdf.set_xy(0, H - 14)
    pdf.cell(W, 6, "Generated by Mythos Glasswing", align="C")

    # Restore auto page break for content pages.
    pdf.set_auto_page_break(auto=True, margin=25)


def _render_table(pdf, rows: list) -> None:
    """Render a styled Mythos-themed table into the PDF."""
    if not rows:
        return
    F = getattr(pdf, "_body_font", "Helvetica")
    n_cols = max(len(r) for r in rows)
    rows = [r + [""] * (n_cols - len(r)) for r in rows]
    LM = 20
    avail = pdf.w - 40
    col_w = avail / n_cols

    # Header row with navy background + white/cyan text.
    pdf.set_font(F, "B", 9)
    pdf.set_fill_color(*_C_TABLE_HEAD)
    pdf.set_text_color(*_C_WHITE)
    pdf.set_draw_color(*_C_NAVY_MID)
    pdf.set_line_width(0.15)
    for cell in rows[0]:
        pdf.cell(col_w, 8, f"  {cell}", border=0, fill=True)
    pdf.ln()
    # Cyan accent line under header.
    pdf.set_fill_color(*_C_CYAN)
    pdf.rect(LM, pdf.get_y(), avail, 0.6, "F")
    pdf.ln(0.6)

    # Data rows.
    pdf.set_font(F, "", 9)
    fill = False
    for row in rows[1:]:
        if fill:
            pdf.set_fill_color(*_C_TABLE_ALT)
        else:
            pdf.set_fill_color(*_C_WHITE)
        pdf.set_text_color(*_C_BODY)
        pdf.set_draw_color(220, 225, 235)
        for cell in row:
            pdf.cell(col_w, 7, f"  {cell}", border=0, fill=True)
        pdf.ln()
        fill = not fill
    # Bottom accent line.
    pdf.set_fill_color(*_C_CYAN_LIGHT)
    pdf.rect(LM, pdf.get_y(), avail, 0.4, "F")
    pdf.ln(4)
    pdf.set_x(LM)


def _render_code_block(pdf, code: str) -> None:
    """Render a code block with dark terminal-like background and cyan border."""
    M = getattr(pdf, "_mono_font", "Courier")
    F = getattr(pdf, "_body_font", "Helvetica")
    LM = 20
    pdf.ln(3)
    code_lines = code.split("\n")
    line_h = 4.5
    block_h = len(code_lines) * line_h + 8
    w = pdf.w - 40
    y_start = pdf.get_y()
    # Check if block fits on page; if not, add page.
    if y_start + block_h > pdf.h - 25:
        pdf.add_page()
        y_start = pdf.get_y()
    actual_h = min(block_h, pdf.h - 50)
    # Dark background panel.
    pdf.set_fill_color(*_C_CODE_BG)
    pdf.rect(LM, y_start, w, actual_h, "F")
    # Cyan left accent border.
    pdf.set_fill_color(*_C_CODE_EDGE)
    pdf.rect(LM, y_start, 1.5, actual_h, "F")
    # Top bar (terminal-like).
    pdf.set_fill_color(*_C_NAVY_MID)
    pdf.rect(LM, y_start, w, 5, "F")
    # Terminal dots.
    pdf.set_fill_color(255, 95, 95)
    pdf.rect(LM + 3, y_start + 1.5, 2, 2, "F")
    pdf.set_fill_color(255, 200, 80)
    pdf.rect(LM + 7, y_start + 1.5, 2, 2, "F")
    pdf.set_fill_color(80, 220, 120)
    pdf.rect(LM + 11, y_start + 1.5, 2, 2, "F")
    # Code text.
    pdf.set_font(M, "", 8)
    pdf.set_text_color(*_C_CODE_TEXT)
    pdf.set_y(y_start + 7)
    for cl in code_lines:
        pdf.set_x(LM + 5)
        pdf.cell(0, line_h, cl[:130])
        pdf.ln(line_h)
    pdf.set_y(y_start + actual_h)
    pdf.ln(4)
    pdf.set_x(LM)
    # Reset.
    pdf.set_font(F, "", 10)
    pdf.set_text_color(*_C_BODY)
    pdf.set_fill_color(*_C_WHITE)


# Lazy-init the actual FPDF subclass so import only happens when needed.
def _init_pdf_class():
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    class MythosPDFDoc(FPDF):
        def header(self):
            if self.page_no() <= 1:
                return  # No header on cover page.
            F = getattr(self, "_body_font", "Helvetica")
            # Thin top accent bar.
            self.set_fill_color(*_C_NAVY)
            self.rect(0, 0, self.w, 3, "F")
            self.set_fill_color(*_C_CYAN)
            self.rect(0, 3, self.w, 0.8, "F")
            # Header text.
            self.set_font(F, "", 7)
            self.set_text_color(140, 155, 175)
            self.set_y(5)
            title = getattr(self, "_doc_title", "") or "Mythos Document"
            self.cell(self.w - 20, 4, f"  {title}", align="L")
            self.ln(6)

        def footer(self):
            if self.page_no() <= 1:
                return  # No footer on cover page.
            F = getattr(self, "_body_font", "Helvetica")
            # Bottom accent bar.
            self.set_fill_color(*_C_CYAN)
            self.rect(0, self.h - 10, self.w, 0.5, "F")
            self.set_fill_color(*_C_NAVY)
            self.rect(0, self.h - 9.5, self.w, 9.5, "F")
            # Page number + branding.
            self.set_font(F, "", 7)
            self.set_text_color(*_C_CYAN_LIGHT)
            self.set_y(self.h - 8)
            self.cell(25, 5, "  MYTHOS", align="L")
            self.set_text_color(160, 175, 195)
            self.cell(self.w - 50, 5,
                      f"Page {self.page_no() - 1}/{{nb}}", align="C")
            self.cell(25, 5, "Glasswing  ", align="R")

    return MythosPDFDoc


def _create_mythos_pdf(orientation="P", unit="mm", format="A4"):
    """Create an FPDF instance with Mythos branding (page numbers in footer)."""
    cls = _init_pdf_class()
    if cls is None:
        raise ImportError("fpdf2 not installed")
    doc = cls(orientation=orientation, unit=unit, format=format)
    doc.alias_nb_pages()
    # Register a Unicode-capable font if available on Windows.
    _register_unicode_font(doc)
    return doc


def _register_unicode_font(doc) -> None:
    """Try to register DejaVu Sans (or a Windows system font) for Unicode support."""
    import os as _os
    # Candidate font paths (Windows common locations).
    candidates = [
        _os.path.join(_os.environ.get("WINDIR", "C:\\Windows"),
                      "Fonts", "arial.ttf"),
        _os.path.join(_os.environ.get("WINDIR", "C:\\Windows"),
                      "Fonts", "segoeui.ttf"),
        _os.path.join(_os.environ.get("WINDIR", "C:\\Windows"),
                      "Fonts", "calibri.ttf"),
    ]
    for path in candidates:
        if _os.path.isfile(path):
            try:
                doc.add_font("UniFont", "", path, uni=True)
                doc.add_font("UniFont", "B", path, uni=True)
                doc.add_font("UniFont", "I", path, uni=True)
                doc._mythos_uni_font = "UniFont"
                return
            except Exception:
                continue
    # No Unicode font found — fall back to built-in (Latin-1 only).
    doc._mythos_uni_font = None


def _safe_text(text: str) -> str:
    """Strip characters that built-in fonts can't render (safety net)."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ----------------------- Parser (model-agnostic) ----------------------- #
# Tool calls are emitted by the AI as fenced `mythos-tool` JSON blocks.
# Example:
#   ```mythos-tool
#   {"name": "run_shell", "args": {"command": "echo hi", "shell": "cmd"}}
#   ```
_TOOL_RE = re.compile(r"```mythos-tool\s*\n(.*?)```", re.DOTALL)


def parse_tool_calls(text: str) -> Tuple[List[ToolCall], str]:
    """
    Extract mythos-tool blocks from AI text.
    Returns (list_of_calls, cleaned_text_without_blocks).
    """
    calls: List[ToolCall] = []
    import json

    def _extract(m: re.Match) -> str:
        block = m.group(1).strip()
        # A block may contain one or many JSON objects (one per line or array).
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            # Try line-by-line for multiple calls.
            for line in block.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    obj = json.loads(line)
                    _append(obj, calls)
                except json.JSONDecodeError:
                    continue
            return "[tool calls parsed]"
        if isinstance(data, list):
            for obj in data:
                _append(obj, calls)
        else:
            _append(data, calls)
        return "[tool call parsed]"

    cleaned = _TOOL_RE.sub(_extract, text)

    # Second pass: inline JSON tool-calls (models that emit native tool-call
    # JSON without our fence, e.g. Cohere-style {"tool_name","parameters"}).
    # Scan all balanced {...} objects, parse, and keep tool-call-shaped ones.
    inline_spans = []
    for s, e, obj in _extract_balanced_json_objects(cleaned):
        if _looks_like_tool_call(obj):
            before = len(calls)
            _append(obj, calls)
            if len(calls) > before:
                inline_spans.append((s, e))
    if inline_spans:
        for s, e in sorted(inline_spans, reverse=True):
            cleaned = cleaned[:s] + "[tool call parsed]" + cleaned[e:]

    # Strip trailing model control tokens (<EOS_TOKEN> etc.).
    cleaned = re.sub(r"<[A-Z_]+_TOKEN>?:?", "", cleaned).strip()
    return calls, cleaned


def _append(obj: Dict[str, Any], calls: List[ToolCall]) -> None:
    """Normalize a JSON object into a ToolCall, accepting common field names."""
    if not isinstance(obj, dict):
        return
    # Name: "name" | "tool_name" | "tool" | "function"
    name = (obj.get("name") or obj.get("tool_name")
            or obj.get("tool") or obj.get("function"))
    # Cohere-style: nested {"function": {"name": ...}}.
    if isinstance(name, dict):
        name = name.get("name")
    if not name or not isinstance(name, str):
        return
    # Args: "args" | "arguments" | "parameters" | "input"
    args = (obj.get("args") or obj.get("arguments")
            or obj.get("parameters") or obj.get("input") or {})
    # Cohere-style: nested under "parameters" could be there already.
    if not isinstance(args, dict):
        args = {"value": args}
    calls.append(ToolCall(name=name, args=args))


def _extract_balanced_json_objects(text: str) -> List[Tuple[int, int, dict]]:
    """
    Find all top-level balanced {...} spans in text and parse each to a dict.
    Returns list of (start, end, parsed_obj). Robust against nested braces
    and string contents (ignores braces inside quoted strings).
    """
    import json as _json
    results = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        # Attempt to scan a balanced object starting here.
        depth = 0
        in_str = False
        esc = False
        j = i
        candidate = None
        while j < n:
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = (i, j + 1)
                        break
            j += 1
        if candidate is None:
            i += 1
            continue
        s, e = candidate
        try:
            obj = _json.loads(text[s:e])
            if isinstance(obj, dict):
                results.append((s, e, obj))
            # Advance past this object.
            i = e
        except _json.JSONDecodeError:
            # Not valid JSON; advance one char to keep searching.
            i += 1
    return results


def _looks_like_tool_call(obj: Dict[str, Any]) -> bool:
    """Heuristic: does this dict look like a tool-call payload?"""
    name_keys = {"name", "tool_name", "tool", "function"}
    arg_keys = {"args", "arguments", "parameters", "input"}
    has_name = any(k in obj for k in name_keys)
    has_args = any(k in obj for k in arg_keys)
    has_id = "tool_call_id" in obj or "id" in obj
    # tool_name + parameters (Cohere) or name + args, or any name with an id.
    return (has_name and has_args) or (has_name and has_id)
