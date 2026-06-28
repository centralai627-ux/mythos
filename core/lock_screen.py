"""
Mythos Lock Screen
==================
Fullscreen security challenge displayed on boot.
Second layer of protection after Windows login.

Questions are complex IT/AI/CS topics.
The answer is ALWAYS one of two keywords:
  - Cetharis  → unlock and proceed to Mythos
  - Dissa     → close the terminal
"""
from __future__ import annotations
import os
import sys
import time
import random
import getpass
from typing import List, Tuple, Optional

from rich.align import Align
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

try:
    from colorama import init as _colorama_init
    _colorama_init()
except Exception:
    pass


# ============== Question Bank ==============
# 40 complex IT/AI/CS questions — answer is always Cetharis or Dissa.
QUESTIONS: List[Tuple[str, str]] = [
    # --- Networking ---
    ("In the TCP/IP model, which layer is responsible for end-to-end "
     "delivery, segmentation, and flow control — and what is its number?",
     "Transport Layer, Layer 4"),

    ("Explain the complete DNS resolution chain from a recursive resolver "
     "to the authoritative nameserver, including DNSSEC validation.",
     "Root → TLD → Authoritative NS; DNSSEC validates via RRSIG/DNSKEY chain"),

    ("What is the fundamental difference between BGP and OSPF in terms of "
     "routing algorithm class and their convergence behavior?",
     "BGP is path-vector (policy-based, slow convergence); "
     "OSPF is link-state (Dijkstra, fast convergence)"),

    ("Describe the TCP three-way handshake sequence and explain why a "
     "four-way handshake is NOT used for connection establishment.",
     "SYN → SYN-ACK → ACK. Three messages suffice because SYN+ACK "
     "piggybacks the server's sequence number on the acknowledgment."),

    ("What is the difference between QUIC and TCP+TLS in terms of "
     "connection establishment latency and head-of-line blocking?",
     "QUIC uses 0-RTT/1-RTT handshake over UDP, eliminates HoL blocking "
     "via independent streams, while TCP+TLS requires 2-3 RTT and "
     "suffers from transport-level HoL blocking."),

    ("Explain how ARP poisoning works on a local network segment and "
     "what defense mechanism can mitigate it at the switch level.",
     "Attacker sends forged ARP replies mapping their MAC to the "
     "gateway IP. Mitigated by Dynamic ARP Inspection (DAI) on switches."),

    # --- Operating Systems ---
    ("Describe the difference between a process and a thread in terms of "
     "memory space, context-switch cost, and inter-entity communication.",
     "Processes have isolated memory (expensive context switch, IPC needed); "
     "threads share memory (cheap switch, direct shared-memory communication)"),

    ("What is the difference between preemptive and cooperative multitasking "
     "and why did modern operating systems move to preemptive scheduling?",
     "Preemptive: OS can interrupt tasks (fairness, responsiveness). "
     "Cooperative: tasks yield voluntarily (risk of starvation/blocking)."),

    ("Explain the concept of virtual memory, page tables, and how a TLB "
     "(Translation Lookaside Buffer) accelerates address translation.",
     "Virtual memory maps virtual→physical via page tables. TLB caches "
     "recent translations to avoid multi-level table walks on every access."),

    ("In Linux, explain the fork() system call and how copy-on-write "
     "(COW) optimization makes it efficient for process creation.",
     "fork() duplicates the process. COW delays physical page copying "
     "until a write occurs — both parent and child share read-only pages."),

    ("Describe the difference between a mutex, a semaphore, and a "
     "condition variable in concurrent programming.",
     "Mutex: mutual exclusion (1 owner). Semaphore: counting lock (N "
     "permits). Condition variable: wait/signal mechanism for thread "
     "coordination on a predicate."),

    ("Explain how the Linux Completely Fair Scheduler (CFS) works and "
     "what data structure it uses to track process fairness.",
     "CFS uses a red-black tree sorted by virtual runtime (vruntime). "
     "The leftmost node (lowest vruntime) is scheduled next, ensuring "
     "proportional fair share of CPU time."),

    # --- Databases ---
    ("Explain the ACID properties and describe how a database achieves "
     "isolation using MVCC (Multi-Version Concurrency Control).",
     "Atomicity, Consistency, Isolation, Durability. MVCC keeps multiple "
     "row versions; readers see a snapshot without blocking writers."),

    ("What is the difference between a B-tree index and a hash index in "
     "terms of supported query patterns and performance characteristics?",
     "B-tree: supports range/order queries, O(log n). Hash: equality-only, "
     "O(1) average. B-tree is the default for most RDBMS."),

    ("Explain the CAP theorem and provide a concrete example of how a "
     "distributed database must choose between C and A during a partition.",
     "During a network partition: choose Consistency (reject writes, e.g. "
     "HBase) or Availability (serve stale data, e.g. Cassandra)."),

    ("Describe Write-Ahead Logging (WAL) and how it enables crash recovery "
     "in relational database systems.",
     "WAL writes changes to a sequential log before modifying data pages. "
     "On crash: redo committed transactions from log, undo uncommitted."),

    # --- Cryptography & Security ---
    ("Explain the difference between symmetric and asymmetric encryption "
     "and why TLS uses a hybrid approach during the handshake.",
     "Symmetric: same key (fast, key distribution problem). Asymmetric: "
     "key pair (slow, solves distribution). TLS uses asymmetric for key "
     "exchange, then symmetric for bulk data encryption."),

    ("What is a zero-knowledge proof and how does the Fiat-Shamir heuristic "
     "transform an interactive ZKP into a non-interactive one?",
     "ZKP proves knowledge without revealing the secret. Fiat-Shamir "
     "replaces the verifier's random challenge with a hash of the "
     "transcript, making it non-interactive."),

    ("Describe how Kerberos authentication works, including the roles of "
     "the AS, TGS, and service ticket in the protocol flow.",
     "Client → AS (gets TGT) → TGS (gets service ticket) → Service. "
     "All tickets encrypted with shared keys; no passwords over the wire."),

    ("What is the difference between HMAC and a digital signature in terms "
     "of key management and non-repudiation?",
     "HMAC uses a shared secret (symmetric, no non-repudiation). "
     "Digital signature uses a key pair (asymmetric, provides "
     "non-repudiation since only the signer has the private key)."),

    # --- AI / Machine Learning ---
    ("Explain the vanishing gradient problem in deep neural networks and "
     "how residual connections (ResNet) solve it mathematically.",
     "Gradients shrink exponentially through layers. ResNet adds skip "
     "connections: F(x)+x ensures gradient ∂L/∂x = ∂L/∂F·∂F/∂x + ∂L/∂x, "
     "preserving gradient flow."),

    ("What is the difference between bagging and boosting in ensemble "
     "learning, and why does boosting typically achieve lower bias?",
     "Bagging: parallel models on bootstrap samples (reduces variance). "
     "Boosting: sequential models on residuals (reduces bias). Boosting "
     "focuses on hard examples iteratively."),

    ("Explain the attention mechanism in Transformer architecture and how "
     "multi-head attention improves upon single-head attention.",
     "Attention: Q·K^T/√d → softmax → ·V. Multi-head projects Q,K,V "
     "into multiple subspaces, capturing different relationship patterns "
     "in parallel instead of one averaged attention."),

    ("What is the difference between L1 and L2 regularization in terms of "
     "their effect on model weights and feature selection?",
     "L1 (Lasso): promotes sparsity, drives weights to exactly zero "
     "(feature selection). L2 (Ridge): shrinks weights toward zero but "
     "rarely exactly zero (weight decay, no feature selection)."),

    ("Explain the bias-variance tradeoff and how model complexity affects "
     "the expected generalization error.",
     "High bias (underfitting): model too simple. High variance "
     "(overfitting): model too complex. Optimal complexity minimizes "
     "the sum of bias², variance, and irreducible noise."),

    ("Describe the difference between supervised, unsupervised, and "
     "reinforcement learning with one concrete algorithm example each.",
     "Supervised: labeled data (e.g. Random Forest). Unsupervised: "
     "unlabeled patterns (e.g. K-Means clustering). RL: agent learns "
     "via reward signals (e.g. PPO / Q-Learning)."),

    ("What is transfer learning and why does fine-tuning a pre-trained "
     "language model (e.g. BERT) on a downstream task require far fewer "
     "examples than training from scratch?",
     "Pre-trained models learn general language representations from "
     "massive corpora. Fine-tuning adapts these representations to a "
     "specific task, requiring only task-specific examples to adjust "
     "the final layers."),

    # --- Programming Languages ---
    ("Explain the difference between garbage collection (mark-and-sweep) "
     "and reference counting, including their respective weaknesses.",
     "GC: periodic tracing (handles cycles, pause times). Ref counting: "
     "immediate deallocation (deterministic, fails on cycles). Python "
     "uses both: ref counting + cyclic GC for cycle collection."),

    ("What is the difference between pass-by-value, pass-by-reference, and "
     "pass-by-sharing (as used in Java/Python)?",
     "Pass-by-value: copy of value. Pass-by-reference: alias to original "
     "variable. Pass-by-sharing: copy of reference (object is shared, "
     "but reassignment doesn't affect caller's binding)."),

    ("Describe type erasure in Java generics and explain why "
     "`List<String>` and `List<Integer>` have the same runtime type.",
     "Java erases generic type parameters at compile time, replacing "
     "them with their bounds or Object. Both become List at runtime; "
     "casts are inserted by the compiler for type safety."),

    ("Explain the difference between stack and heap allocation, including "
     "when each is used and their performance characteristics.",
     "Stack: LIFO, fast, automatic cleanup, limited size, value types. "
     "Heap: dynamic allocation, slower, manual/GC-managed, larger, "
     "reference types and large objects."),

    # --- Distributed Systems ---
    ("Describe the Raft consensus algorithm's leader election process and "
     "how it ensures exactly one leader per term.",
     "Followers timeout and become candidates, increment term, request "
     "votes. A candidate winning majority becomes leader. Terms prevent "
     "split-brain; randomized timeouts reduce election collisions."),

    ("Explain the difference between linearizability and sequential "
     "consistency in distributed system memory models.",
     "Linearizability: operations appear to execute atomically at some "
     "point between invocation and response (real-time ordering). "
     "Sequential consistency: operations appear in some total order "
     "consistent with each thread's program order."),

    ("What is the difference between a distributed hash table (DHT) and "
     "a consistent hashing ring, and how does Chord implement lookups?",
     "DHT distributes key-value pairs across nodes. Consistent hashing "
     "maps keys to a ring. Chord uses finger tables for O(log N) "
     "lookups, where each node knows nodes at distances 2^i."),

    # --- Architecture & Hardware ---
    ("Explain the difference between RISC and CISC instruction set "
     "architectures and why ARM (RISC) dominates mobile while x86 (CISC) "
     "dominates desktop.",
     "RISC: simple fixed-length instructions, more registers, lower power "
     "(ideal for mobile). CISC: complex variable-length instructions, "
     "fewer instructions per program (ideal for desktop performance)."),

    ("What is the difference between SRAM and DRAM in terms of speed, "
     "cost, density, and where each is used in a computer system?",
     "SRAM: fast, expensive, low density (CPU caches L1/L2/L3). "
     "DRAM: slower, cheap, high density (main system memory/RAM)."),

    ("Describe how a CPU pipeline works and explain the three classic "
     "types of pipeline hazards: structural, data, and control.",
     "Pipeline overlaps instruction stages (IF/ID/EX/MEM/WB). "
     "Structural: resource conflicts. Data: read-after-write dependencies. "
     "Control: branch prediction failures cause pipeline flushes."),

    # --- Containers & DevOps ---
    ("Explain how Linux containers achieve isolation using namespaces and "
     "resource control using cgroups.",
     "Namespaces isolate: PID, network, mount, user, IPC, UTS. "
     "Cgroups limit: CPU, memory, I/O, network bandwidth. Together "
     "they create lightweight virtual environments without a hypervisor."),

    ("What is the difference between blue-green deployment and canary "
     "release strategies, and when would you choose each?",
     "Blue-green: two identical environments, instant switch (safe, "
     "expensive). Canary: gradual rollout to a subset (cheaper, "
     "real-user testing, slower full rollout)."),

    # --- Algorithms ---
    ("Explain the difference between Dijkstra's algorithm and Bellman-Ford "
     "in terms of time complexity and the types of graphs they support.",
     "Dijkstra: O((V+E)log V) with min-heap, non-negative weights only. "
     "Bellman-Ford: O(VE), handles negative weights and detects negative "
     "cycles."),

    ("Describe how a Bloom filter works, its false positive rate formula, "
     "and why it can never produce false negatives.",
     "Bloom filter uses k hash functions to set bits in a bit array. "
     "Lookup checks all k bits. False positive rate: (1-e^(-kn/m))^k. "
     "No false negatives: if any bit is 0, the element was never added."),
]


# ============== Lock Screen Theme ==============
LOCK_THEME = Theme({
    "lock.face":     "#d7e6f2",
    "lock.dim":      "#8fa8bf",
    "lock.edge":     "#5b7a96",
    "lock.border":   "#3a5a7a",
    "lc":            "bold #7ff0ff",     # lock cyan
    "lc.hot":        "bold #b9f2ff",     # bright
    "lc.deep":       "#4fc3e8",          # deeper
    "lc.dim":        "#4a90a8",          # muted
    "lock.ok":       "bold #8effc8",
    "lock.warn":     "bold #ffe08a",
    "lock.err":      "bold #ff9aa8",
    "lock.gold":     "bold #ffd700",
})

# Unicode wing for lock screen
_LOCK_WING = (
    "\u2550\u2550\u2550\u2550\u2550"
    "\u2550\u2563 "
    "\u25c6\u2500\u2500\u2500\u2500\u2500"
    "\u25c6\u2500\u2500\u2500\u2500\u2500\u25c6"
    " \u2560"
    "\u2550\u2550\u2550\u2550\u2550"
    "\u2550"
)


class LockScreen:
    """
    Fullscreen security challenge for boot-time protection.
    No hints are shown. User must figure out the passphrase.
    
    Valid answers:
    - Cetharis  → unlock and proceed to Mythos
    - Dissa     → close the terminal
    """

    ANSWER_UNLOCK = "cetharis"
    ANSWER_CLOSE = "dissa"
    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 60

    def __init__(self, use_guardian: bool = True) -> None:
        self.console = Console(theme=LOCK_THEME, highlight=False)
        self._attempts: int = 0
        self._questions: List[Tuple[str, str]] = list(QUESTIONS)
        # Anti-bypass guardian (keyboard hook + Task Manager killer).
        self._guardian = None
        self._use_guardian = use_guardian
        if use_guardian:
            try:
                from .guardian import MythosGuardian
                self._guardian = MythosGuardian(on_focus_lost=self._regrab_focus)
            except Exception:
                self._guardian = None

    def _regrab_focus(self) -> None:
        """Re-assert foreground if the lock window loses focus."""
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd and self._guardian:
                self._guardian.force_foreground(hwnd)
        except Exception:
            pass

    # ======================= Public API ======================= #
    def run(self) -> str:
        """
        Run the lock screen challenge.

        Returns:
            "unlock" — user answered correctly (proceed to Mythos)
            "close"  — user chose to close the terminal
        """
        # Arm anti-bypass guardian BEFORE fullscreen (block escape keys first).
        # v2 returns a status dict so we know exactly what protection is active.
        self._protection_status = {"hook": False, "watcher": False,
                                   "registry": False, "errors": []}
        if self._guardian:
            self._protection_status = self._guardian.arm()

        self._go_fullscreen()
        random.shuffle(self._questions)
        q_idx = 0

        try:
            return self._run_loop(q_idx)
        finally:
            # Always disarm on exit, even on crash/interrupt.
            if self._guardian:
                self._guardian.disarm()

    def _run_loop(self, q_idx: int) -> str:
        """Inner challenge loop (split out so disarm always runs in finally)."""
        while True:
            self._attempts = 0

            while self._attempts < self.MAX_ATTEMPTS:
                self.console.clear()
                question_text, hint_text = self._questions[q_idx % len(self._questions)]

                self._render_screen(
                    question=question_text,
                    attempt=self._attempts + 1,
                    max_attempts=self.MAX_ATTEMPTS,
                )

                # Get password input (hidden).
                answer = self._secure_input()

                if answer.lower() == self.ANSWER_UNLOCK:
                    self.console.clear()
                    self._render_unlocked()
                    time.sleep(1.5)
                    return "unlock"

                elif answer.lower() == self.ANSWER_CLOSE:
                    return "close"

                else:
                    self._attempts += 1
                    self.console.clear()
                    self._render_wrong(answer, self._attempts, self.MAX_ATTEMPTS)
                    time.sleep(2.0)

                    # Rotate question on wrong answer.
                    q_idx = (q_idx + 1) % len(self._questions)

            # All attempts failed — lockout.
            self._lockout_sequence()

            # After lockout, pick a new question and retry.
            q_idx = (q_idx + 1) % len(self._questions)

    # ======================= Fullscreen ======================= #
    def _go_fullscreen(self) -> None:
        """
        Maximize the terminal and DISABLE all window controls:
        - No close button (X)
        - No minimize button
        - No maximize button
        - Alt+F4 disabled
        """
        try:
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                user32 = ctypes.windll.user32
                hwnd = kernel32.GetConsoleWindow()
                if hwnd:
                    # Maximize window.
                    SW_MAXIMIZE = 3
                    user32.ShowWindow(hwnd, SW_MAXIMIZE)

                    # Disable close, minimize, maximize buttons.
                    # SC_CLOSE=0xF060, SC_MINIMIZE=0xF020, SC_MAXIMIZE=0xF030
                    MENU = user32.GetSystemMenu(hwnd, False)
                    if MENU:
                        SC_CLOSE = 0xF060
                        SC_MINIMIZE = 0xF020
                        SC_MAXIMIZE = 0xF030
                        MF_BYCOMMAND = 0x00000000
                        # Remove all window control buttons.
                        user32.RemoveMenu(MENU, SC_CLOSE, MF_BYCOMMAND)
                        user32.RemoveMenu(MENU, SC_MINIMIZE, MF_BYCOMMAND)
                        user32.RemoveMenu(MENU, SC_MAXIMIZE, MF_BYCOMMAND)

                    # Disable Alt+F4 via SetWindowLong.
                    GWL_STYLE = -16
                    WS_SYSMENU = 0x00080000
                    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                    # Remove WS_SYSMENU (removes system menu entirely).
                    user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_SYSMENU)
                    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                       0x0001 | 0x0002 | 0x0010)  # SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED

                    # Also disable Ctrl+C / Ctrl+Break on console.
                    kernel32.SetConsoleCtrlHandler(None, True)

            else:
                # POSIX: try alternate screen buffer.
                sys.stdout.write("\033[?1049h")
                sys.stdout.flush()
        except Exception:
            pass
        self.console.clear()

    def _leave_fullscreen(self) -> None:
        """Restore normal terminal (POSIX only)."""
        if sys.platform != "win32":
            try:
                sys.stdout.write("\033[?1049l")
                sys.stdout.flush()
            except Exception:
                pass

    # ======================= Rendering ======================= #
    def _render_screen(self, question: str, attempt: int,
                       max_attempts: int) -> None:
        """Render the main lock screen challenge."""
        # Top decorative rule.
        rule_top = Rule(style="lc.dim", characters="\u2550")

        # Brand.
        brand = Text.assemble(
            ("M", "lc.hot"), ("Y", "lc"), ("T", "lc"),
            ("H", "lc"), ("O", "lc"), ("S", "lc.hot"),
        )
        subtitle = Text("SECURITY GATEWAY", style="lc.deep")

        # Wing separator.
        wing = Text(_LOCK_WING, style="lc.dim")

        # Question panel.
        q_panel = Panel(
            Text(question, style="lock.face"),
            border_style="lc.dim", box=DOUBLE,
            title=Text.assemble(
                ("\u25c6 ", "lc"), ("CHALLENGE", "lc.hot")),
            title_align="left",
            padding=(2, 3),
        )

        # Mystery panel (no password hints — user must figure it out).
        mystery_panel = Panel(
            Group(
                Text.assemble(
                    ("\u26a0 ", "lock.warn"),
                    ("ACCESS CONTROLLED", "lock.face"),
                ),
                Text(
                    "\u2726 This system is protected by Mythos Security Gateway.\n"
                    "\u2726 Prove your identity to proceed.\n\n"
                    "\u2726 Type the correct passphrase to unlock.",
                    style="lock.dim",
                ),
            ),
            border_style="lock.warn", box=ROUNDED,
            title=Text.assemble(
                ("\u26a0 ", "lock.warn"), ("SYSTEM STATUS", "lock.face")),
            title_align="left",
            padding=(1, 3),
        )

        # Attempt counter.
        remaining = max_attempts - attempt
        attempt_text = Text.assemble(
            ("ATTEMPT ", "lock.dim"),
            (str(attempt), "lock.warn" if remaining <= 1 else "lc"),
            (" / ", "lock.dim"),
            (str(max_attempts), "lock.dim"),
        )

        # Bottom rule.
        rule_bot = Rule(style="lc.dim", characters="\u2550")

        # Metadata.
        meta = Text.assemble(
            ("v1.0.0", "lock.dim"),
            ("  \u00b7  ", "lock.edge"),
            ("Mythos Security Gateway", "lc.dim"),
            ("  \u00b7  ", "lock.edge"),
            ("Layer 2 Protection", "lock.dim"),
        )

        # Compose the full screen.
        content = Group(
            rule_top, Text(""),
            Align.center(brand),
            Align.center(subtitle),
            Text(""),
            Align.center(wing),
            Text(""),
            q_panel,
            Text(""),
            mystery_panel,
            Text(""),
            Align.center(attempt_text),
            Text(""),
            rule_bot,
            Align.center(meta),
        )

        self.console.print(Align.center(content))

    def _secure_input(self) -> str:
        """Get hidden password input (handles Ctrl+C gracefully)."""
        try:
            self.console.print()
            self.console.print(
                Text("  \u25b6 ", style="lc.hot"),
                Text("answer ", style="lc"),
                Text("\u276f ", style="lc.deep"),
                sep="", end="",
            )
            # Use raw_input with timeout to handle Ctrl+C.
            return getpass.getpass(prompt="")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+C is disabled at console level, but just in case.
            return ""
        except Exception:
            return ""

    def _render_wrong(self, answer: str, attempt: int,
                      max_attempts: int) -> None:
        """Render the wrong-answer feedback screen."""
        self.console.clear()

        rule = Rule(style="lock.err", characters="\u2550")
        remaining = max_attempts - attempt

        # Error panel.
        err_content = Group(
            Text(""),
            Text.assemble(
                ("\u2717  ", "lock.err"),
                ("ACCESS DENIED", "lock.err"),
            ),
            Text(""),
            Text(f'   Your answer was incorrect.', style="lock.face"),
            Text(""),
            Text.assemble(
                ("   Attempts remaining: ", "lock.dim"),
                (str(remaining), "lock.warn" if remaining <= 2 else "lock.face"),
            ),
            Text(""),
        )

        if remaining <= 1:
            err_content = Group(
                err_content,
                Text.assemble(
                    ("   \u26a0  ", "lock.warn"),
                    ("WARNING: One attempt remaining before lockout!",
                     "lock.warn"),
                ),
                Text(""),
            )

        panel = Panel(
            err_content,
            border_style="lock.err", box=HEAVY,
            title=Text.assemble(
                ("\u2717 ", "lock.err"), ("SECURITY BREACH ATTEMPT", "lock.err")),
            title_align="left",
            padding=(1, 3),
        )

        brand = Text.assemble(
            ("M", "lc.hot"), ("Y", "lc"), ("T", "lc"),
            ("H", "lc"), ("O", "lc"), ("S", "lc.hot"),
        )

        content = Group(
            rule, Text(""),
            Align.center(brand),
            Text(""),
            panel,
            Text(""),
            Align.center(
                Text("Preparing new challenge...", style="lock.dim")),
            Text(""),
            rule,
        )

        self.console.print(Align.center(content))

    def _lockout_sequence(self) -> None:
        """Show lockout screen with countdown timer."""
        self.console.clear()

        rule = Rule(style="lock.err", characters="\u2550")
        brand = Text.assemble(
            ("M", "lc.hot"), ("Y", "lc"), ("T", "lc"),
            ("H", "lc"), ("O", "lc"), ("S", "lc.hot"),
        )

        lockout_panel = Panel(
            Group(
                Text(""),
                Text.assemble(
                    ("\u26d4  ", "lock.err"),
                    ("SYSTEM LOCKED", "lock.err"),
                ),
                Text(""),
                Text("   Too many failed attempts.", style="lock.face"),
                Text("   Security lockout initiated.", style="lock.face"),
                Text(""),
            ),
            border_style="lock.err", box=HEAVY,
            title=Text.assemble(
                ("\u26d4 ", "lock.err"), ("LOCKOUT", "lock.err")),
            title_align="left",
            padding=(1, 3),
        )

        self.console.print(Align.center(Group(
            rule, Text(""),
            Align.center(brand),
            Text(""),
            lockout_panel,
            Text(""),
            rule,
        )))

        # Countdown.
        for remaining in range(self.LOCKOUT_SECONDS, 0, -1):
            mins = remaining // 60
            secs = remaining % 60
            timer = Text.assemble(
                ("   \u23f1  ", "lock.warn"),
                (f"Unlock in {mins:02d}:{secs:02d}", "lock.warn"),
            )
            # Clear the line and print new timer.
            self.console.print(f"\r{timer}", end="", highlight=False)
            time.sleep(1)

        self.console.print()  # newline after countdown.

    def _render_unlocked(self) -> None:
        """Render the success/unlock screen."""
        rule = Rule(style="lock.ok", characters="\u2550")
        brand = Text.assemble(
            ("M", "lc.hot"), ("Y", "lc"), ("T", "lc"),
            ("H", "lc"), ("O", "lc"), ("S", "lc.hot"),
        )

        success_panel = Panel(
            Group(
                Text(""),
                Text.assemble(
                    ("\u2713  ", "lock.ok"),
                    ("IDENTITY VERIFIED", "lock.ok"),
                ),
                Text(""),
                Text("   Access granted.", style="lock.face"),
                Text("   Loading Mythos Glasswing...", style="lc"),
                Text(""),
            ),
            border_style="lock.ok", box=DOUBLE,
            title=Text.assemble(
                ("\u2713 ", "lock.ok"), ("UNLOCKED", "lock.ok")),
            title_align="left",
            padding=(1, 3),
        )

        content = Group(
            rule, Text(""),
            Align.center(brand),
            Text(""),
            success_panel,
            Text(""),
            Align.center(
                Text("crystalline intelligence", style="lc.dim")),
            Text(""),
            rule,
        )

        self.console.print(Align.center(content))


# ======================= Auto-Start Installer ======================= #
def get_startup_script_path() -> str:
    """Return the path to the lock screen launcher script."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "mythos_lock.cmd")


def install_autostart() -> bool:
    """
    Install Mythos lock screen to run automatically on Windows boot.
    Creates a robust .cmd launcher in the user's Startup folder.
    """
    try:
        import shutil
        import subprocess as _sp

        # Find the Mythos installation.
        mythos_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mythos_py = os.path.join(mythos_dir, "mythos.py")
        if not os.path.isfile(mythos_py):
            print(f"[Mythos] Entry point not found: {mythos_py}")
            return False

        # ---- Robust Python discovery ----
        # Priority: dedicated Mythos venv > current interpreter > system Python
        python_candidates = []

        # 0) Dedicated Mythos venv (most reliable for boot — standalone).
        mythos_venv = os.path.join(mythos_dir, ".mythos_venv", "Scripts", "python.exe")
        if os.path.isfile(mythos_venv):
            python_candidates.append(os.path.abspath(mythos_venv))

        # 1) Current interpreter.
        if sys.executable and os.path.isfile(sys.executable):
            python_candidates.append(os.path.abspath(sys.executable))

        # 2) Base Python (for venv — the real system install).
        base = getattr(sys, "_base_executable", None)
        if base and os.path.isfile(base):
            python_candidates.append(os.path.abspath(base))

        # 3) Search PATH.
        for name in ("python.exe", "python3.exe", "py.exe"):
            p = shutil.which(name)
            if p:
                python_candidates.append(os.path.abspath(p))

        # 4) Common install paths.
        import glob
        for pattern in (
            r"C:\Python3*\python.exe",
            r"C:\Program Files\Python3*\python.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python3*\python.exe"),
        ):
            python_candidates.extend(glob.glob(pattern))

        # De-duplicate while preserving order.
        seen = set()
        unique_candidates = []
        for c in python_candidates:
            cl = c.lower()
            if cl not in seen:
                seen.add(cl)
                unique_candidates.append(c)

        # Test each candidate for required deps.
        python_exe = ""
        for candidate in unique_candidates:
            try:
                r = _sp.run(
                    [candidate, "-c",
                     "import rich; import colorama; print('ok')"],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode == 0 and "ok" in r.stdout:
                    python_exe = candidate
                    print(f"[Mythos] Found Python with deps: {candidate}")
                    break
            except Exception:
                continue

        if not python_exe:
            # Last resort: use current executable even without dep check.
            python_exe = sys.executable or "python"
            print(f"[Mythos] WARNING: Could not verify deps. Using: {python_exe}")

        # ---- Create the robust launcher script ----
        # Use forward slashes in paths to avoid CMD escaping issues.
        mythos_dir_clean = mythos_dir.replace("/", "\\")
        python_clean = python_exe.replace("/", "\\")

        launcher_content = f"""\
@echo off
title Mythos Security Gateway
mode con cols=140 lines=45
color 0B

REM ============================================================
REM  Mythos Lock Screen - Auto-Start Launcher
REM  Layer 2 Security - Runs on Windows boot
REM ============================================================

set "MYTHOS_HOME={mythos_dir_clean}"
set "PYTHON_EXE={python_clean}"

echo.
echo   ============================================
echo     MYTHOS SECURITY GATEWAY
echo   ============================================
echo.
echo   [Mythos] Starting Security Gateway...
echo.

cd /d "%MYTHOS_HOME%"
if errorlevel 1 (
    echo   [ERROR] Cannot access Mythos directory: %MYTHOS_HOME%
    echo.
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo   [ERROR] Python not found at: %PYTHON_EXE%
    echo   [Mythos] Searching for Python on PATH...
    for %%P in (python py python3) do (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%%P"
            echo   [Mythos] Found: %%P
            goto :run_lock
        )
    )
    echo   [ERROR] No Python interpreter found!
    echo.
    pause
    exit /b 1
)

:run_lock
echo   [Mythos] Python: %PYTHON_EXE%
echo   [Mythos] Launching lock screen...
echo.

REM Run Python DIRECTLY in this window (no 'start' — keeps the window open).
"%PYTHON_EXE%" "%MYTHOS_HOME%\mythos.py" --lock

if errorlevel 1 (
    echo.
    echo   [ERROR] Mythos lock screen exited with error!
    echo   Python: %PYTHON_EXE%
    echo   Script: %MYTHOS_HOME%\mythos.py
    echo.
    pause
)
"""
        # ---- Write launcher to Mythos directory ----
        launcher_path = os.path.join(mythos_dir, "mythos_lock.cmd")
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_content)
        print(f"[Mythos] Launcher created: {launcher_path}")

        # ---- Install into Windows Startup folder ----
        startup_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
        )
        if not os.path.isdir(startup_dir):
            print(f"[Mythos] Startup folder not found: {startup_dir}")
            print("         Copy mythos_lock.cmd to Startup manually.")
            return True

        startup_link = os.path.join(startup_dir, "mythos_lock.cmd")
        with open(startup_link, "w", encoding="utf-8") as f:
            f.write(launcher_content)
        print(f"[Mythos] Auto-start installed: {startup_link}")
        print()
        print("  The lock screen will appear on next boot.")
        print("  Answers: Cetharis (unlock) or Dissa (close)")
        print()
        print("  If the window appears blank, it means Python")
        print("  dependencies are missing. Run: python install.py")
        return True

    except Exception as e:
        print(f"[Mythos] Auto-start install failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def uninstall_autostart() -> bool:
    """Remove the lock screen from Windows auto-start."""
    removed = []
    try:
        # Remove from Startup folder.
        startup_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
        )
        startup_link = os.path.join(startup_dir, "mythos_lock.cmd")
        if os.path.isfile(startup_link):
            os.unlink(startup_link)
            removed.append(startup_link)

        # Remove launcher from Mythos dir.
        mythos_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        launcher_path = os.path.join(mythos_dir, "mythos_lock.cmd")
        if os.path.isfile(launcher_path):
            os.unlink(launcher_path)
            removed.append(launcher_path)

        if removed:
            print("[Mythos] Auto-start removed:")
            for r in removed:
                print(f"  - {r}")
        else:
            print("[Mythos] No auto-start files found.")
        return True
    except Exception as e:
        print(f"[Mythos] Failed to remove auto-start: {e}")
        return False
