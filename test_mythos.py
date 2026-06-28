"""
Mythos AI - Test Suite
======================
Comprehensive unit tests for every module. Runs without network.
Run:  python test_mythos.py
"""
from __future__ import annotations
import os
import sys
import time
import json
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.config import config, load_config
from core.key_manager import KeyManager, KeyRing
from core.executor import ShellExecutor
from core.ai_brain import MythosBrain, Intent
from core.ui import MythosUI

PASS = 0
FAIL = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {detail}")


def section(title: str) -> None:
    print(f"\n— {title} —")


# ----------------------------------------------------------- #
def test_config() -> None:
    section("Config")
    ok("config loads", config.llm is not None)
    ok("base_url present", "openrouter.ai" in config.base_url)
    ok("openrouter_keys count", len(config.openrouter_keys) >= 20,
       f"got {len(config.openrouter_keys)}")
    ok("zai_keys count", len(config.zai_keys) >= 10,
       f"got {len(config.zai_keys)}")
    ok("model alias: code", "code" in config.models)
    ok("model alias: ultra", "ultra" in config.models)
    ok("model alias: vision", "vision" in config.models)
    ok("temperature float", isinstance(config.temperature, float))
    ok("timeout int", isinstance(config.timeout, int))
    ok("notify_rolling default false", config.notify_rolling is False)


def test_keyring() -> None:
    section("KeyRing / KeyManager")
    ring = KeyRing(["k1", "k2", "k3", "k4"], notify=False)
    ok("ring size", len(ring) == 4)
    # Round-robin.
    k1 = ring.get()
    k2 = ring.get()
    k3 = ring.get()
    k4 = ring.get()
    ok("round-robin returns all distinct",
       len({k1, k2, k3, k4}) == 4, f"{[k1,k2,k3,k4]}")
    ok("5th wraps around", ring.get() == k1)
    ok("alive count", ring.alive_count() == 4)
    # Rate limit one key.
    ring.report_rate_limit("k2", cooldown=10)
    ok("rate-limited key unavailable", ring.peek() != "k2")
    ok("available drops to 3", ring.available_count() == 3)
    # Dead key.
    ring.report_dead("k3")
    ok("dead key removed", ring.alive_count() == 3)
    # Success resets.
    ring.report_success("k1")
    ok("success resets fails", ring._states["k1"].fails == 0)

    km = KeyManager(["a", "b"], ["c", "d"])
    ok("manager has openrouter ring", km.openrouter is not None)
    ok("manager has zai ring", km.zai is not None)
    ok("manager get_openrouter_key", km.get_openrouter_key() in ("a", "b"))
    ok("manager get_zai_key", km.get_zai_key() in ("c", "d"))
    status = km.status()
    ok("status dict keys", "openrouter_alive" in status and "zai_alive" in status)


def test_executor() -> None:
    section("ShellExecutor")
    ex = ShellExecutor()
    shells = ex.detect_shells()
    ok("detect_shells returns dict", isinstance(shells, dict))
    ok("cmd available", bool(shells.get("cmd")))
    ok("powershell available", bool(shells.get("powershell")))

    # CMD echo.
    r = ex.run("echo mythos_test_123", shell="cmd")
    ok("cmd echo success", r.success, f"exit={r.exit_code}")
    ok("cmd echo content", "mythos_test_123" in r.stdout, r.stdout)
    ok("cmd records shell name", r.shell == "cmd")

    # PowerShell.
    r = ex.run("Write-Output 'ps_hello'", shell="powershell")
    ok("ps echo success", r.success, f"exit={r.exit_code} stderr={r.stderr}")
    ok("ps echo content", "ps_hello" in r.stdout, r.stdout)

    # PowerShell with exit code.
    r = ex.run("$LASTEXITCODE=0; Write-Output 'ok'", shell="powershell")
    ok("ps exit code 0", r.success and r.exit_code == 0,
       f"exit={r.exit_code}")

    # Failure case.
    r = ex.run("this_command_does_not_exist_xyz", shell="cmd")
    ok("cmd failure captured", not r.success or "not recognized" in (r.stdout + r.stderr).lower(),
       f"exit={r.exit_code}")

    # Timeout.
    r = ex.run("ping -n 10 127.0.0.1", shell="cmd", timeout=0.5)
    ok("timeout detected", r.timed_out, f"timed_out={r.timed_out}")

    # Auto-detect picks powershell for PS-style cmd.
    shell = ex._auto_detect("Get-Process")
    ok("auto-detect PS verb", shell == "powershell", shell)

    # Atomic write.
    tmp = tempfile.mktemp(suffix=".txt")
    content = "line1\nline2\nunicode: café ☕\n"
    wrote = ex.atomic_write(tmp, content)
    ok("atomic_write returns True", wrote)
    with open(tmp, "r", encoding="utf-8") as f:
        read_back = f.read()
    ok("atomic_write content correct", read_back == content)
    os.unlink(tmp)

    # safe_read.
    tmp2 = tempfile.mktemp(suffix=".txt")
    with open(tmp2, "w", encoding="utf-8") as f:
        f.write("hello mythos")
    ok("safe_read returns content", ex.safe_read(tmp2) == "hello mythos")
    ok("safe_read missing returns None", ex.safe_read(tmp2 + "_nope") is None)
    os.unlink(tmp2)


def test_brain_parsing() -> None:
    section("MythosBrain parsing")
    # Build a brain with a fake api to avoid network.
    class FakeAPI:
        def __init__(self): self.last = None
        def chat(self, messages, model_alias="mythos-code", **kw):
            self.last = (messages, model_alias)
            return (
                "Here is the plan.\n\n"
                "```mythos-shell\n# shell: powershell\nGet-Process | Select-Object -First 3\n```\n\n"
                "```mythos-file\n# path: out/hello.py\nprint('hi')\n```\n"
            )
        def vision(self, *a, **kw): return "vision-response"

    brain = MythosBrain(FakeAPI())
    # Classification.
    ok("classify coding default", brain.classify("write a function") == "mythos-code")
    ok("classify ultra for complex",
       brain.classify("design the architecture and plan step by step for this complex system") == "mythos-ultra")
    ok("classify not triggered for short",
       brain.classify("plan") == "mythos-code")  # too short

    intent = brain.ask("test request")
    ok("ask returns Intent", isinstance(intent, Intent))
    ok("parsed one shell block", len(intent.shell_blocks) == 1,
       f"got {intent.shell_blocks}")
    ok("shell block shell is powershell",
       intent.shell_blocks[0][0] == "powershell")
    ok("shell block has command", "Get-Process" in intent.shell_blocks[0][1])
    ok("parsed one file block", len(intent.file_blocks) == 1)
    ok("file block path correct", intent.file_blocks[0][0] == "out/hello.py")
    ok("file block content correct", "print('hi')" in intent.file_blocks[0][1])
    ok("intent.has_actions true", intent.has_actions)
    ok("display text cleaned", "mythos-shell" not in intent.text)
    ok("history grew", len(brain.history) == 2)  # user + assistant

    # set_model.
    ok("set_model valid", brain.set_model("mythos-ultra"))
    ok("set_model invalid", not brain.set_model("bogus"))


def test_ui() -> None:
    section("MythosUI")
    ui = MythosUI()
    ok("console created", ui.console is not None)
    # Render methods should not raise.
    try:
        ui.info("test info")
        ui.success("test success")
        ui.warn("test warn")
        ui.error("test error")
        ui.divider("test")
        ui.file_written("/tmp/x.py", 10, 200)
        ok("ui status methods render without error", True)
    except Exception as e:
        ok("ui status methods render without error", False, str(e))

    # help_table / status_table.
    try:
        ui.help_table()
        ui.status_table(
            {"openrouter_alive": 26, "openrouter_available": 26,
             "zai_alive": 12, "zai_available": 12},
            "mythos-code",
            {"cmd": "cmd.exe", "powershell": "powershell.exe"},
        )
        ok("ui tables render without error", True)
    except Exception as e:
        ok("ui tables render without error", False, str(e))

    # assistant with mixed content.
    try:
        ui.assistant(
            "Here is code:\n```python\nprint('x')\n```\nDone.",
            model="mythos-code", tools_used=2,
        )
        ok("ui.assistant renders mixed content", True)
    except Exception as e:
        ok("ui.assistant renders mixed content", False, str(e))

    # Glasswing-specific renderers.
    try:
        ui.boot_screen(version="9.9", keys_alive=7, model="mythos-code")
        ui.header_bar("mythos-code", 26, "C:/test/path")
        ui.tool_call("run_shell", {"command": "echo hi", "shell": "cmd"}, 1)
        ui.observation("hello\nworld", True, 1)
        ui.observation("error!", False, 2)
        ok("ui glasswing renderers work", True)
    except Exception as e:
        ok("ui glasswing renderers work", False, str(e))

    try:
        ui.tools_table(["read_file", "run_shell"],
                       "- read_file(path): Read a file\n- run_shell(command, shell): Run cmd")
        ok("ui tools_table renders", True)
    except Exception as e:
        ok("ui tools_table renders", False, str(e))


def test_tools() -> None:
    section("ToolRegistry + parser")
    from core.tools import ToolRegistry, ToolCall, ToolResult, parse_tool_calls
    from core.executor import ShellExecutor
    import tempfile, os

    ex = ShellExecutor()
    reg = ToolRegistry(ex, cwd=tempfile.gettempdir())

    ok("registry has >=10 tools", len(reg.names) >= 10, f"got {len(reg.names)}")
    ok("schema for prompt non-empty", len(reg.schema_for_prompt()) > 50)
    # Check core tools are always present (extras like pdf allowed).
    required = {"read_file", "write_file", "list_dir", "search",
                "run_shell", "ask_user", "ask_choice", "ask_confirm",
                "web_search", "web_fetch"}
    missing = required - set(reg.names)
    ok("core tools present", not missing, f"missing {missing}")

    # write_file then read_file round-trip.
    tmpf = os.path.join(tempfile.gettempdir(), "mythos_tooltest.txt")
    r = reg.execute(ToolCall("write_file", {"path": tmpf, "content": "hello glass"}))
    ok("write_file success", r.ok, r.error)
    r = reg.execute(ToolCall("read_file", {"path": tmpf}))
    ok("read_file returns content", r.ok and "hello glass" in r.output, r.output)
    os.unlink(tmpf)

    # read_file on missing path -> error (not crash).
    r = reg.execute(ToolCall("read_file", {"path": tmpf + "_nope"}))
    ok("read_file missing -> error", not r.ok)

    # list_dir.
    r = reg.execute(ToolCall("list_dir", {"path": tempfile.gettempdir()}))
    ok("list_dir success", r.ok, r.error[:80])

    # run_shell.
    r = reg.execute(ToolCall("run_shell", {"command": "echo mythostool", "shell": "cmd"}))
    ok("run_shell success", r.ok and "mythostool" in r.output, r.output[:100])

    # search.
    sf = os.path.join(tempfile.gettempdir(), "mythos_search.py")
    reg.execute(ToolCall("write_file", {"path": sf, "content": "x = 1\nMYTHOS_MARK = 42\n"}))
    r = reg.execute(ToolCall("search", {"pattern": "MYTHOS_MARK", "path": tempfile.gettempdir(), "glob": "*.py"}))
    ok("search finds match", r.ok and "MYTHOS_MARK" in r.output, r.output[:100])
    os.unlink(sf)

    # unknown tool -> error.
    r = reg.execute(ToolCall("bogus_tool", {}))
    ok("unknown tool -> error", not r.ok)

    # bad args -> error not crash.
    r = reg.execute(ToolCall("run_shell", {}))  # missing command
    ok("missing required arg -> error", not r.ok)

    # ---- interactive tools (with mock hooks) ----
    # ask_choice needs a choice_hook; registry without one -> error.
    ok("ask_choice no hook -> error",
       not reg.execute(ToolCall("ask_choice",
                                {"question": "q", "options": ["a", "b"]})).ok)
    ok("ask_confirm no hook -> error",
       not reg.execute(ToolCall("ask_confirm", {"question": "q"})).ok)
    # ask_choice with bad options (too few / too many / wrong type).
    reg2 = ToolRegistry(ex,
                        choice_hook=lambda q, o: 0,
                        confirm_hook=lambda q: True)
    ok("ask_choice single option -> error",
       not reg2.execute(ToolCall("ask_choice",
                                 {"question": "q", "options": ["only"]})).ok)
    ok("ask_choice too many options -> error",
       not reg2.execute(ToolCall("ask_choice",
                                 {"question": "q",
                                  "options": [str(i) for i in range(20)]})).ok)
    ok("ask_choice bad options type -> error",
       not reg2.execute(ToolCall("ask_choice",
                                 {"question": "q", "options": 42})).ok)
    # ask_choice with valid options + mock returning index 1.
    r = reg2.execute(ToolCall("ask_choice",
                              {"question": "pick", "options": ["alpha", "beta"]}))
    ok("ask_choice valid -> ok", r.ok, r.error)
    ok("ask_choice returns chosen option text", "beta" in r.output, r.output)
    # ask_choice accepts pipe-separated string.
    r = reg2.execute(ToolCall("ask_choice",
                              {"question": "pick", "options": "x|y|z"}))
    ok("ask_choice pipe-string options -> ok", r.ok)
    # ask_confirm mock returning True.
    r = reg2.execute(ToolCall("ask_confirm", {"question": "sure?"}))
    ok("ask_confirm -> ok with YES", r.ok and "YES" in r.output, r.output)
    # ask_confirm mock returning False.
    reg3 = ToolRegistry(ex, confirm_hook=lambda q: False)
    r = reg3.execute(ToolCall("ask_confirm", {"question": "sure?"}))
    ok("ask_confirm -> ok with NO", r.ok and "NO" in r.output, r.output)

    # ---- web tools (offline: parsers only) ----
    ok("web_search empty query -> error",
       not reg.execute(ToolCall("web_search", {"query": ""})).ok)
    ok("web_fetch invalid scheme -> error",
       not reg.execute(ToolCall("web_fetch", {"url": "ftp://x"})).ok)
    ok("web_fetch empty url -> error",
       not reg.execute(ToolCall("web_fetch", {"url": ""})).ok)
    # Invalid max_results falls back to default (not crash).
    r = reg.execute(ToolCall("web_search", {"query": "x", "max_results": "junk"}))
    ok("web_search bad max_results handled (not crash)", isinstance(r, ToolResult))

    # HTML -> text stripping.
    sample = ("<html><head><style>x{}</style><script>bad()</script></head>"
              "<body><h1>Title</h1><p>Para &amp; more</p><div>line2</div></body>")
    txt = reg._html_to_text(sample)
    ok("html_to_text strips script/style", "bad()" not in txt and "x{}" not in txt)
    ok("html_to_text decodes entities", "Para & more" in txt, txt)
    ok("html_to_text keeps content", "Title" in txt and "line2" in txt)

    # ---- parser ----
    text = 'Before\n```mythos-tool\n{"name": "run_shell", "args": {"command": "dir", "shell": "cmd"}}\n```\nAfter'
    calls, cleaned = parse_tool_calls(text)
    ok("parser extracts 1 call", len(calls) == 1, f"got {len(calls)}")
    ok("parsed call name", calls[0].name == "run_shell")
    ok("parsed call command arg", calls[0].args.get("command") == "dir")
    ok("cleaned text retains before/after", "Before" in cleaned and "After" in cleaned)

    # Multiple calls in one block (array form).
    text2 = '```mythos-tool\n[{"name":"read_file","args":{"path":"a"}},{"name":"list_dir","args":{"path":"."}}]\n```'
    calls2, _ = parse_tool_calls(text2)
    ok("parser handles array of calls", len(calls2) == 2, f"got {len(calls2)}")

    # No tool blocks -> empty list, text unchanged.
    calls3, cleaned3 = parse_tool_calls("just plain text")
    ok("no tools -> empty list", calls3 == [])
    ok("no tools -> text unchanged", cleaned3 == "just plain text")


def test_agentic_loop() -> None:
    section("Agentic loop (mocked)")
    import tempfile
    from core.tools import ToolRegistry
    from core.executor import ShellExecutor
    from core.ai_brain import MythosBrain

    ex = ShellExecutor(cwd=tempfile.gettempdir())
    reg = ToolRegistry(ex, cwd=tempfile.gettempdir())

    # Mock API: first turn emits a tool call; second turn gives final answer.
    class MockAPI:
        def __init__(self):
            self.turn = 0
        def chat(self, messages, model_alias="mythos-code", **kw):
            self.turn += 1
            if self.turn == 1:
                return ('Let me check.\n```mythos-tool\n'
                        '{"name": "run_shell", "args": {"command": "echo glass_ok", "shell": "cmd"}}\n```')
            # Turn 2+: final answer (no tools).
            return "Verified. The command output confirms glass_ok."

    brain = MythosBrain(MockAPI(), tools=reg)
    intent, steps = brain.run_with_tools("echo glass_ok and confirm")
    ok("loop executes 1 tool step", steps == 1, f"steps={steps}")
    ok("loop returns final intent", isinstance(intent, Intent))
    ok("final text has no tool block", "mythos-tool" not in intent.text)
    ok("last_tool_results populated", len(brain.last_tool_results) == 1)
    ok("tool result was success", brain.last_tool_results[0].ok)

    # Loop that hits the safety cap.
    class LoopingAPI:
        def __init__(self): self.n = 0
        def chat(self, messages, model_alias="mythos-code", **kw):
            self.n += 1
            return ('```mythos-tool\n{"name":"run_shell","args":{"command":"echo x","shell":"cmd"}}\n```')
    brain2 = MythosBrain(LoopingAPI(), tools=reg)
    brain2.max_tool_steps = 3  # small cap for test speed
    intent2, steps2 = brain2.run_with_tools("loop forever")
    ok("loop respects safety cap", steps2 == 3 + 1 or steps2 == brain2.max_tool_steps,
       f"steps={steps2}")

    # No tools wired -> falls back to single ask().
    class AskAPI:
        def chat(self, messages, model_alias="mythos-code", **kw):
            return "direct answer"
    brain3 = MythosBrain(AskAPI(), tools=None)
    intent3, steps3 = brain3.run_with_tools("hi")
    ok("no tools -> 0 steps, single ask", steps3 == 0)


def main() -> int:
    print("=" * 52)
    print("  MYTHOS AI  ·  TEST SUITE")
    print("=" * 52)
    test_config()
    test_keyring()
    test_executor()
    test_brain_parsing()
    test_tools()
    test_agentic_loop()
    test_ui()

    print("\n" + "=" * 52)
    print(f"  RESULT:  {PASS} passed,  {FAIL} failed")
    print("=" * 52)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
