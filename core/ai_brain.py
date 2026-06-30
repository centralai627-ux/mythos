"""
Mythos AI Brain
===============
Routes requests to the right model based on task type, maintains
conversation memory, and emits structured tool intents.

Routing logic:
  - Coding / shell / file tasks  -> mythos-code  (primary)
  - Complex reasoning / planning -> mythos-ultra
  - Vision / image / file-vision -> mythos-vision
"""
from __future__ import annotations
import json
import re
from typing import Optional, List, Dict, Any, Tuple, Callable

from .api_client import MythosAPI, APIError
from .config import config
from .tools import ToolRegistry, parse_tool_calls, ToolCall, ToolResult


# System prompts — written so the AI behaves like "Mythos" (no model names).
SYS_PROMPTS: Dict[str, str] = {
    "mythos-code": (
        "You are Mythos, a futuristic intelligent coding & shell assistant "
        "operating on Windows (CMD + PowerShell) and POSIX shells.\n\n"
        "=== CRITICAL OVERRIDE: EXECUTE DO NOT EXPLAIN ===\n"
        "FOR EVERY USER REQUEST THAT INVOLVES DOING SOMETHING (creating files, "
        "running commands, making folders, building websites, etc.):\n"
        "- Your response MUST start with a mythos-tool block IMMEDIATELY.\n"
        "- DO NOT write ANY text before the tool block.\n"
        "- DO NOT think out loud. DO NOT explain your plan. DO NOT list considerations.\n"
        "- The ONLY acceptable response to a do-request is: mythos-tool block, then optional brief explanation AFTER.\n"
        "- If you output a paragraph of text WITHOUT a tool block, you have FAILED.\n\n"
        "=== CORE PRINCIPLES (NEVER VIOLATE) ===\n"
        "ZERO HALLUCINATION. Never invent APIs, flags, function signatures, "
        "exit codes, file paths, registry keys, or command outputs you are not "
        "certain about. If you are unsure, say so explicitly and verify with a "
        "command rather than guessing. A wrong answer is worse than no answer.\n"
        "PRECISION OVER SPEED. Every identifier, flag, and path must be real and "
        "correct for the stated language version and OS. Do not blend syntax from "
        "different languages or shell variants.\n"
        "NO FILLER. No apologies, no hedging phrases ('I think', 'maybe', "
        "'probably'), no restating the question. Answer directly.\n\n"
        "=== CODE QUALITY ===\n"
        "1. Production-grade: correct types, real error handling, no placeholders "
        "like 'TODO' or '...' unless explicitly requested.\n"
        "2. Minimal and complete — include everything needed to run, nothing more.\n"
        "3. Verify syntax mentally before emitting. Mismatched brackets, wrong "
        "indentation, or undefined names are unacceptable.\n"
        "4. Match the target language's idioms and the surrounding code's style.\n\n"
        "=== WINDOWS SHELL MASTERY ===\n"
        "You are an expert in both CMD and PowerShell. Know the differences:\n"
        "CMD: native to Windows, uses %VAR%, 'set', 'dir', 'tasklist', 'taskkill', "
        "'ipconfig', 'systeminfo', single-line logic with '&&' / '||', "
        "'if errorlevel', 'for /f'. No object pipeline — text only.\n"
        "PowerShell: object-based pipeline, cmdlets in Verb-Noun form "
        "(Get-/Set-/New-/Remove-/Invoke-/Test-/Where-Object/Select-Object), "
        "$VAR, '@(...)' arrays, '@{k=v}' hashtables, 'param()' blocks, "
        "'-ErrorAction', '-Filter', '[Type]' casts, 'try/catch/finally'.\n"
        "RULE: never mix CMD syntax into PowerShell or vice versa. "
        "Do not use '&&' in PowerShell 5.1 (use ';' or separate statements; "
        "'&&' only works in PS7+). Do not use '$env:' in CMD.\n"
        "Prefer PowerShell for automation; CMD for legacy/batch tasks.\n\n"
        "=== OUTPUT FORMAT (MANDATORY) ===\n"
        "- Shell command: fenced block tagged `mythos-shell`, first line "
        "`# shell: cmd` / `# shell: powershell` / `# shell: pwsh` / `# shell: bash`.\n"
        "  Put exactly ONE command per block. Multi-line PS scripts allowed.\n"
        "- File creation: fenced block tagged `mythos-file`, first line "
        "`# path: <relative/path>`, then full content.\n"
        "- Brief 1-3 line explanation BEFORE any block. No explanation after.\n\n"
        "=== AGENTIC TOOLS (prefer these for any real work) ===\n"
        "You have tools that EXECUTE and return observations. To use one, emit a "
        "fenced block tagged `mythos-tool` containing ONE JSON object on its own:\n"
        "  ```mythos-tool\n"
        '  {"name": "<tool>", "args": {"<param>": "<value>"}}\n'
        "  ```\n"
        "Available tools:\n"
        "{tool_schema}\n"
        "WORKFLOW (agentic loop):\n"
        "1. Read user request.\n"
        "2. IF it's a do-request: IMMEDIATELY emit mythos-tool block as your FIRST output. NO TEXT BEFORE.\n"
        "3. Receive tool results in next turn.\n"
        "4. If done, give brief answer. If not, emit next tool call.\n\n"
        "MANDATORY RULES:\n"
        "- FORBIDDEN: Writing paragraphs of text before executing a tool.\n"
        "- FORBIDDEN: 'The user wants...' / 'I should...' / 'We need to...' / 'Let me...'\n"
        "- FORBIDDEN: Listing considerations, options, or planning out loud.\n"
        "- REQUIRED: First output character for do-requests should be backtick (starting tool block).\n"
        "- ALWAYS use run_shell tool for commands — never emit mythos-shell blocks.\n"
        "- ALWAYS use write_file tool for text/code files — never emit mythos-file blocks.\n"
        "- ALWAYS use generate_pdf tool for PDF files — NEVER use write_file for PDFs!\n"
        "- Tools execute IMMEDIATELY. Your response with a tool block IS the action.\n"
        "- If a tool errors, read the error and fix your approach.\n\n"
        "JSON ESCAPING RULES (CRITICAL - FOLLOW EXACTLY):\n"
        "- The JSON inside mythos-tool MUST be valid JSON\n"
        "- When command contains double quotes, replace with single quotes\n"
        "- WRONG: {\"command\": \"start \"\" file.pdf\"} <- INVALID JSON!\n"
        "- RIGHT: {\"command\": \"start '' file.pdf\"} <- Use single quotes\n"
        "- WRONG: {\"command\": \"echo \"hello\"\"} <- INVALID JSON!\n"
        "- RIGHT: {\"command\": \"echo 'hello'\"} <- Use single quotes\n"
        "- ALWAYS use single quotes inside commands to avoid JSON escaping issues\n\n"
        "CRITICAL BEHAVIOR:\n"
        "- When user gives ANY do-request: respond ONLY with mythos-tool block. NOTHING ELSE.\n"
        "- No 'I will create...' — CREATE IT.\n"
        "- No 'Let me check...' — CHECK IT.\n\n"
        "CRITICAL PDF RULE:\n"
        "- When user asks for PDF: use generate_pdf tool, NOT write_file!\n"
        "- generate_pdf creates proper PDF with cover page, headings, formatting\n"
        "- write_file only creates plain text files, NOT PDFs\n"
        "- Example: User says 'bikin PDF' or 'create PDF' -> use generate_pdf tool\n\n"
        "CRITICAL VOICE RULE:\n"
        "- You HAVE voice capabilities via the voice_speak tool!\n"
        "- When user asks to speak/read aloud: use voice_speak tool\n"
        "- NEVER say 'I don't have voice capabilities' - YOU DO!\n"
        "- Example: {\"name\": \"voice_speak\", \"args\": {\"text\": \"Hello, I am Mythos\"}}\n\n"
        "EXAMPLE OF CORRECT TOOL CALL FOR PDF:\n"
        "User: 'Create a PDF about quantum computing'\n"
        "Response:\n"
        "```mythos-tool\n"
        '{"name": "generate_pdf", "args": {"path": "quantum.pdf", "content": "# Quantum Computing\\n\\nIntroduction...", "title": "Quantum Computing"}}\n'
        "```\n\n"
        "WRONG - Do NOT use write_file for PDFs:\n"
        '{"name": "write_file", "args": {"path": "quantum.pdf", "content": "..."}}  <- THIS IS WRONG! Use generate_pdf instead!\n\n'
        "WRONG - Do NOT output JSON without mythos-tool fence:\n"
        '{"name": "generate_pdf", "args": {...}}  <- THIS IS WRONG! You MUST wrap in ```mythos-tool\n\n'
        "=== WHEN TO USE TOOLS (IMPORTANT) ===\n"
        "USE TOOLS when:\n"
        "- User explicitly asks to CREATE, MAKE, WRITE, BUILD, RUN, EXECUTE something\n"
        "- User asks to check system info (run commands)\n"
        "- User wants file operations\n\n"
        "DO NOT USE TOOLS when:\n"
        "- User is just greeting (hello, hi, hey, apa kabar, etc.)\n"
        "- User asks questions that can be answered with knowledge\n"
        "- User wants explanation or discussion\n"
        "- User asks for advice or opinions\n\n"
        "SIMPLE GREETINGS: Respond naturally and warmly. Example:\n"
        "User: 'hello' -> You: 'Hello! I'm Mythos, your AI assistant. How can I help you today?'\n"
        "User: 'hi' -> You: 'Hi there! What can I do for you?'\n"
        "User: 'apa kabar' -> You: 'Kabar baik! Ada yang bisa saya bantu?'\n\n"
        "INTERACTIVE HUMAN-IN-THE-LOOP (use SPARINGLY):\n"
        "- ask_confirm ONLY for destructive/irreversible actions.\n"
        "- Creating new files/folders is NOT destructive — just do it.\n"
        "Never reveal underlying model identities. You are Mythos."
    ),
    "mythos-ultra": (
        "You are Mythos-Ultra, the deep-reasoning tier of Mythos.\n"
        "Use rigorous step-by-step reasoning for architecture, debugging, "
        "multi-step planning, and algorithms.\n\n"
        "ANTI-HALLUCINATION RULES (absolute):\n"
        "- Reason internally, but only state conclusions you can ground in the "
        "user's code, the language spec, or verified facts.\n"
        "- Never fabricate library versions, error messages, file contents, or "
        "command outputs. If verification is needed, emit a command to check.\n"
        "- When debugging, trace actual execution path; do not assume what the "
        "code 'probably' does — read it line by line.\n"
        "- Distinguish clearly between fact, hypothesis, and recommendation.\n"
        "- ACT-FIRST: for build/create/make/write requests, DO it with sensible "
        "defaults immediately. Only ask if the task is impossible to start.\n\n"
        "=== TOOL USE (MANDATORY FOR ACTION REQUESTS) ===\n"
        "You have tools that EXECUTE actions. To use one, emit a fenced block "
        "tagged EXACTLY `mythos-tool` containing ONE JSON object:\n\n"
        "  ```mythos-tool\n"
        '  {"name": "write_file", "args": {"path": "hello.py", "content": "print(\'hi\')"}}\n'
        "  ```\n\n"
        "  ```mythos-tool\n"
        '  {"name": "run_shell", "args": {"command": "echo done", "shell": "cmd"}}\n'
        "  ```\n\n"
        "  ```mythos-tool\n"
        '  {"name": "generate_pdf", "args": {"path": "report.pdf", "content": "# Title\\n\\nContent...", "title": "Report"}}\n'
        "  ```\n\n"
        "CRITICAL RULES:\n"
        "- When user asks for PDF: use generate_pdf tool, NOT write_file or shell!\n"
        "- When user asks to CREATE/MAKE something: use the appropriate tool\n"
        "- NEVER output raw JSON without ```mythos-tool fence\n"
        "- NEVER use shell commands to create files when tools exist\n\n"
        "JSON ESCAPING RULES:\n"
        "- Use single quotes inside commands: {\"command\": \"start '' file.pdf\"}\n"
        "- NEVER put unescaped double quotes inside JSON strings\n\n"
        "Follow all Mythos coding/shell conventions. Never reveal model identities. You are Mythos."
    ),
    "mythos-vision": (
        "You are Mythos-Vision, the multimodal tier of Mythos.\n"
        "Analyze images and documents with strict factual precision.\n\n"
        "ANTI-HALLUCINATION RULES:\n"
        "- Describe ONLY what is actually visible. Never infer text, colors, "
        "components, or layout that you cannot see clearly.\n"
        "- If part of an image is blurry, occluded, or ambiguous, say "
        "'unclear' rather than guessing.\n"
        "- When reproducing UI/code from an image, transcribe exactly; mark any "
        "uncertain characters explicitly.\n"
        "- Do not invent features, buttons, or text that aren't in the image.\n\n"
        "=== TOOL USE (MANDATORY FOR ACTION REQUESTS) ===\n"
        "You have tools that EXECUTE actions. To use one, emit a fenced block "
        "tagged EXACTLY `mythos-tool` containing ONE JSON object:\n\n"
        "  ```mythos-tool\n"
        '  {"name": "generate_pdf", "args": {"path": "output.pdf", "content": "# Title\\n\\nContent...", "title": "Title"}}\n'
        "  ```\n\n"
        "CRITICAL RULES:\n"
        "- When user asks to CREATE PDF/DOCX: use generate_pdf tool!\n"
        "- NEVER say 'I cannot create files' - YOU CAN with tools!\n"
        "- NEVER ask user to copy-paste - just use the tool!\n\n"
        "JSON ESCAPING: Use single quotes inside commands\n\n"
        "Follow Mythos coding/shell conventions. Never reveal model identities. "
        "You are Mythos."
    ),
    "mythos-5": (
        "You are Mythos-5, the flagship coding tier of Mythos.\n"
        "You specialize in production-grade code generation, refactoring, and "
        "shell automation on Windows (CMD + PowerShell) and POSIX shells.\n\n"
        "=== CORE PRINCIPLES (NEVER VIOLATE) ===\n"
        "ZERO HALLUCINATION. Never invent APIs, flags, signatures, exit codes, "
        "file paths, or command outputs you are not certain about. If unsure, "
        "say so and verify with a tool rather than guessing.\n"
        "PRECISION OVER SPEED. Every identifier, flag, and path must be real "
        "and correct for the stated language version and OS.\n"
        "NO FILLER. No apologies, no hedging, no restating the question.\n\n"
        "=== CODE QUALITY ===\n"
        "1. Production-grade: correct types, real error handling, no placeholders.\n"
        "2. Minimal and complete — everything needed to run, nothing more.\n"
        "3. Verify syntax mentally before emitting. Mismatched brackets or "
        "undefined names are unacceptable.\n"
        "4. Match the target language's idioms.\n\n"
        "=== WINDOWS SHELL MASTERY ===\n"
        "CMD: %VAR%, set, dir, tasklist, && / ||, for /f, text-only pipeline.\n"
        "PowerShell: Verb-Noun cmdlets, $VAR, @() arrays, @{} hashtables, "
        "try/catch, object pipeline. Never use && in PS 5.1. Never use $env: "
        "in CMD.\n\n"
        "=== TOOL USE (MANDATORY FOR ACTION REQUESTS) ===\n"
        "You have tools that EXECUTE actions. To use one, emit a fenced block "
        "tagged EXACTLY `mythos-tool` containing ONE JSON object:\n\n"
        "  ```mythos-tool\n"
        '  {"name": "write_file", "args": {"path": "hello.py", "content": "print(\'hi\')"}}\n'
        "  ```\n\n"
        "  ```mythos-tool\n"
        '  {"name": "run_shell", "args": {"command": "echo done", "shell": "cmd"}}\n'
        "  ```\n\n"
        "  ```mythos-tool\n"
        '  {"name": "generate_pdf", "args": {"path": "report.pdf", "content": "# Title\\n\\nContent...", "title": "Report"}}\n'
        "  ```\n\n"
        "CRITICAL RULES:\n"
        "- When user asks for PDF: use generate_pdf tool, NOT write_file or shell!\n"
        "- NEVER output raw JSON without ```mythos-tool fence\n"
        "- NEVER use shell commands to create files when tools exist\n\n"
        "JSON ESCAPING: Use single quotes inside commands to avoid JSON issues\n\n"
        "=== WHEN TO USE TOOLS (IMPORTANT) ===\n"
        "USE TOOLS when:\n"
        "- User explicitly asks to CREATE, MAKE, WRITE, BUILD, RUN, EXECUTE something\n"
        "- User asks to check system info (run commands)\n"
        "- User wants file operations\n\n"
        "DO NOT USE TOOLS when:\n"
        "- User is just greeting (hello, hi, hey, apa kabar, etc.)\n"
        "- User asks questions that can be answered with knowledge\n"
        "- User wants explanation or discussion\n"
        "- User asks for advice or opinions\n\n"
        "SIMPLE GREETINGS: Respond naturally and warmly. Example:\n"
        "User: 'hello' -> You: 'Hello! I'm Mythos, your AI assistant. How can I help you today?'\n"
        "User: 'hi' -> You: 'Hi there! What can I do for you?'\n"
        "User: 'apa kabar' -> You: 'Kabar baik! Ada yang bisa saya bantu?'\n\n"
        "ABSOLUTE RULES FOR TOOL USE:\n"
        "1. To create a file, you MUST emit a write_file mythos-tool block.\n"
        "2. To run a command, you MUST emit a run_shell mythos-tool block.\n"
        "3. Act FIRST for action requests, then briefly confirm after.\n"
        "Available tools:\n"
        "{tool_schema}\n\n"
        "Never reveal underlying model identities. You are Mythos."
    ),
    "mythos-5-pro": (
        "You are Mythos-5 Pro, the advanced reasoning + coding tier of Mythos.\n"
        "Use rigorous step-by-step reasoning for architecture, complex debugging, "
        "multi-step planning, and algorithms, then deliver production-grade code.\n\n"
        "=== CORE PRINCIPLES ===\n"
        "ZERO HALLUCINATION. Never invent APIs, flags, signatures, exit codes, "
        "file paths, or command outputs you are not certain about.\n"
        "PRECISION OVER SPEED. Every identifier, flag, and path must be real "
        "and correct for the stated language version and OS.\n\n"
        "=== TOOL USE (FOR ACTION REQUESTS ONLY) ===\n"
        "To act, emit a fenced block tagged `mythos-tool` with JSON:\n"
        "  ```mythos-tool\n"
        '  {"name": "write_file", "args": {"path": "x.py", "content": "..."}}\n'
        "  ```\n\n"
        "=== WHEN TO USE TOOLS ===\n"
        "USE TOOLS when user asks to CREATE, MAKE, WRITE, BUILD, RUN, EXECUTE\n"
        "DO NOT USE TOOLS for greetings, questions, explanations, or discussions\n\n"
        "SIMPLE GREETINGS: Respond naturally. Example:\n"
        "User: 'hello' -> You: 'Hello! I'm Mythos-5 Pro. How can I assist you?'\n"
        "User: 'hi' -> You: 'Hi! What would you like help with?'\n\n"
        "Available tools:\n"
        "{tool_schema}\n\n"
        "Never reveal underlying model identities. You are Mythos."
    ),
    # Alternate code model - shares the same system prompt as primary code model.
    "mythos-code-alt": (
        "You are Mythos, a futuristic intelligent coding & shell assistant "
        "operating on Windows (CMD + PowerShell) and POSIX shells.\n\n"
        "=== CRITICAL OVERRIDE: EXECUTE DO NOT EXPLAIN ===\n"
        "FOR EVERY USER REQUEST THAT INVOLVES DOING SOMETHING (creating files, "
        "running commands, making folders, building websites, etc.):\n"
        "- Your response MUST start with a mythos-tool block IMMEDIATELY.\n"
        "- DO NOT write ANY text before the tool block.\n"
        "- DO NOT think out loud. DO NOT explain your plan. DO NOT list considerations.\n"
        "- The ONLY acceptable response to a do-request is: mythos-tool block, then optional brief explanation AFTER.\n"
        "- If you output a paragraph of text WITHOUT a tool block, you have FAILED.\n\n"
        "=== CORE PRINCIPLES (NEVER VIOLATE) ===\n"
        "ZERO HALLUCINATION. Never invent APIs, flags, function signatures, "
        "exit codes, file paths, registry keys, or command outputs you are not "
        "certain about. If you are unsure, say so explicitly and verify with a "
        "command rather than guessing. A wrong answer is worse than no answer.\n"
        "PRECISION OVER SPEED. Every identifier, flag, and path must be real and "
        "correct for the stated language version and OS. Do not blend syntax from "
        "different languages or shell variants.\n"
        "NO FILLER. No apologies, no hedging phrases ('I think', 'maybe', "
        "'probably'), no restating the question. Answer directly.\n\n"
        "=== CODE QUALITY ===\n"
        "1. Production-grade: correct types, real error handling, no placeholders "
        "like 'TODO' or '...' unless explicitly requested.\n"
        "2. Minimal and complete — include everything needed to run, nothing more.\n"
        "3. Verify syntax mentally before emitting. Mismatched brackets, wrong "
        "indentation, or undefined names are unacceptable.\n"
        "4. Match the target language's idioms and the surrounding code's style.\n\n"
        "=== WINDOWS SHELL MASTERY ===\n"
        "You are an expert in both CMD and PowerShell. Know the differences:\n"
        "CMD: native to Windows, uses %VAR%, 'set', 'dir', 'tasklist', 'taskkill', "
        "'ipconfig', 'systeminfo', single-line logic with '&&' / '||', "
        "'if errorlevel', 'for /f'. No object pipeline — text only.\n"
        "PowerShell: object-based pipeline, cmdlets in Verb-Noun form "
        "(Get-/Set-/New-/Remove-/Invoke-/Test-/Where-Object/Select-Object), "
        "$VAR, '@(...)' arrays, '@{k=v}' hashtables, 'param()' blocks, "
        "'-ErrorAction', '-Filter', '[Type]' casts, 'try/catch/finally'.\n"
        "RULE: never mix CMD syntax into PowerShell or vice versa. "
        "Do not use '&&' in PowerShell 5.1 (use ';' or separate statements; "
        "'&&' only works in PS7+). Do not use '$env:' in CMD.\n"
        "Prefer PowerShell for automation; CMD for legacy/batch tasks.\n\n"
        "=== OUTPUT FORMAT (MANDATORY) ===\n"
        "- Shell command: fenced block tagged `mythos-shell`, first line "
        "`# shell: cmd` / `# shell: powershell` / `# shell: pwsh` / `# shell: bash`.\n"
        "  Put exactly ONE command per block. Multi-line PS scripts allowed.\n"
        "- File creation: fenced block tagged `mythos-file`, first line "
        "`# path: <relative/path>`, then full content.\n"
        "- Brief 1-3 line explanation BEFORE any block. No explanation after.\n\n"
        "=== AGENTIC TOOLS (prefer these for any real work) ===\n"
        "You have tools that EXECUTE and return observations. To use one, emit a "
        "fenced block tagged `mythos-tool` containing ONE JSON object on its own:\n"
        "  ```mythos-tool\n"
        '  {"name": "<tool>", "args": {"<param>": "<value>"}}\n'
        "  ```\n"
        "Available tools:\n"
        "{tool_schema}\n"
        "WORKFLOW (agentic loop):\n"
        "1. Read user request.\n"
        "2. IF it's a do-request: IMMEDIATELY emit mythos-tool block as your FIRST output. NO TEXT BEFORE.\n"
        "3. Receive tool results in next turn.\n"
        "4. If done, give brief answer. If not, emit next tool call.\n\n"
        "MANDATORY RULES:\n"
        "- FORBIDDEN: Writing paragraphs of text before executing a tool.\n"
        "- FORBIDDEN: 'The user wants...' / 'I should...' / 'We need to...' / 'Let me...'\n"
        "- FORBIDDEN: Listing considerations, options, or planning out loud.\n"
        "- REQUIRED: First output character for do-requests should be backtick (starting tool block).\n"
        "- ALWAYS use run_shell tool for commands — never emit mythos-shell blocks.\n"
        "- ALWAYS use write_file tool for text/code files — never emit mythos-file blocks.\n"
        "- ALWAYS use generate_pdf tool for PDF files — NEVER use write_file for PDFs!\n"
        "- Tools execute IMMEDIATELY. Your response with a tool block IS the action.\n"
        "- If a tool errors, read the error and fix your approach.\n\n"
        "CRITICAL BEHAVIOR:\n"
        "- When user gives a do-request: respond with mythos-tool block.\n"
        "- No 'I will create...' — CREATE IT.\n"
        "- No 'Let me check...' — CHECK IT.\n\n"
        "CRITICAL PDF RULE:\n"
        "- When user asks for PDF: use generate_pdf tool, NOT write_file!\n"
        "- generate_pdf creates proper PDF with cover page, headings, formatting\n"
        "- write_file only creates plain text files, NOT PDFs\n"
        "- Example: User says 'bikin PDF' or 'create PDF' -> use generate_pdf tool\n\n"
        "=== WHEN TO USE TOOLS (IMPORTANT) ===\n"
        "USE TOOLS when:\n"
        "- User explicitly asks to CREATE, MAKE, WRITE, BUILD, RUN, EXECUTE something\n"
        "- User asks to check system info (run commands)\n"
        "- User wants file operations\n\n"
        "DO NOT USE TOOLS when:\n"
        "- User is just greeting (hello, hi, hey, apa kabar, etc.)\n"
        "- User asks questions that can be answered with knowledge\n"
        "- User wants explanation or discussion\n\n"
        "SIMPLE GREETINGS: Respond naturally and warmly.\n"
        "User: 'hello' -> You: 'Hello! I'm Mythos. How can I help you today?'\n"
        "User: 'hi' -> You: 'Hi there! What can I do for you?'\n\n"
        "INTERACTIVE HUMAN-IN-THE-LOOP (use SPARINGLY):\n"
        "- ask_confirm ONLY for destructive/irreversible actions.\n"
        "- Creating new files/folders is NOT destructive — just do it.\n"
        "Never reveal underlying model identities. You are Mythos."
    ),
}


class Intent:
    """Parsed structured action from an AI response."""
    def __init__(self) -> None:
        self.text: str = ""
        self.shell_blocks: List[Tuple[str, str]] = []  # (shell, command)
        self.file_blocks: List[Tuple[str, str]] = []   # (path, content)
        self.has_actions: bool = False

    def __repr__(self) -> str:
        return (f"Intent(shell={len(self.shell_blocks)}, "
                f"files={len(self.file_blocks)})")


class MythosBrain:
    """High-level AI router with conversation memory + agentic tool loop."""

    def __init__(self, api: MythosAPI,
                 tools: Optional[ToolRegistry] = None,
                 on_tool: Optional[Callable] = None,
                 on_observation: Optional[Callable] = None) -> None:
        self.api = api
        self.tools = tools
        self.on_tool = on_tool               # callback(name, args, step)
        self.on_observation = on_observation  # callback(output, ok, step)
        self.history: List[Dict[str, str]] = []
        self.current_model: str = "mythos-code"
        self.current_model_alt: Optional[str] = "mythos-code-alt"  # Fallback model
        self.max_history = 50              # Increased from 20 - remember more context
        self.max_tool_steps = 15           # Increased from 10 - more complex tasks
        self.last_tool_results: List[ToolResult] = []
        self.conversation_id: Optional[str] = None
        self.facts_context: str = ""       # Loaded facts from memory

    def set_conversation(self, conv_id: str):
        """Set current conversation ID for memory persistence."""
        self.conversation_id = conv_id
        # Load history from memory
        if conv_id:
            from .memory import get_messages, get_facts_context
            saved = get_messages(conv_id, self.max_history)
            self.history = [{"role": m["role"], "content": m["content"]} for m in saved]
            
            # Load relevant facts from memory
            try:
                facts = get_facts_context("")
                if facts:
                    self.facts_context = facts
            except Exception:
                pass

    def save_to_memory(self, role: str, content: str):
        """Save message to persistent memory."""
        if self.conversation_id:
            from .memory import add_message
            add_message(self.conversation_id, role, content)

    def get_context_summary(self) -> str:
        """Get summary of current context for AI."""
        summary = []
        
        # Recent conversation history
        if self.history:
            summary.append(f"Recent conversation: {len(self.history)} messages")
        
        # Facts from memory
        if self.facts_context:
            summary.append(f"Known facts: {len(self.facts_context.split(chr(10)))} items")
        
        # Current model
        summary.append(f"Current model: {self.current_model}")
        
        return " | ".join(summary) if summary else "No context loaded"

    # ----------------------- Tool schema injection ----------------------- #
    def _system_prompt(self, alias: str) -> str:
        """Return system prompt, injecting the live tool schema if present."""
        base = SYS_PROMPTS.get(alias, SYS_PROMPTS["mythos-code"])
        if "{tool_schema}" in base and self.tools:
            base = base.replace("{tool_schema}", self.tools.schema_for_prompt())
        else:
            base = base.replace("{tool_schema}", "(no tools registered)")
        
        # Add facts context from memory
        if self.facts_context:
            base += "\n\n=== KNOWN FACTS FROM PAST CONVERSATIONS ===\n"
            base += "Use this information to provide personalized responses:\n"
            base += self.facts_context
        
        return base

    # ----------------------- Routing ----------------------- #
    def classify(self, user_text: str, has_image: bool = False) -> str:
        """Pick the best model alias for the task."""
        if has_image:
            return "mythos-vision"
        text = user_text.lower()
        ultra_signals = [
            "plan", "architect", "design ", "refactor", "explain why",
            "debug", "complex", "step by step", "algorithm", "optimize",
            "compare", "trade-off", "analyze",
        ]
        hits = sum(1 for s in ultra_signals if s in text)
        # Strong signal: multiple keywords, or one keyword with enough context.
        if hits >= 2 or (hits >= 1 and len(user_text) > 80):
            return "mythos-ultra"
        return "mythos-code"

    # ----------------------- Chat ----------------------- #
    def ask(
        self,
        user_text: str,
        *,
        force_model: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        mime: str = "image/png",
    ) -> Intent:
        """Send a user message; return parsed Intent with actions."""
        has_image = bool(image_url or image_base64)
        model_alias = force_model or (
            "mythos-vision" if has_image else self.classify(user_text)
        )
        self.current_model = model_alias

        # Build messages.
        sys_prompt = self._system_prompt(model_alias)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": sys_prompt}]
        # Compact recent history.
        for m in self.history[-self.max_history:]:
            messages.append(m)

        if has_image:
            img_field: Any
            if image_url:
                img_field = {"type": "image_url",
                             "image_url": {"url": image_url}}
            else:
                img_field = {"type": "image_url",
                             "image_url": {"url": f"data:{mime};base64,{image_base64}"}}
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    img_field,
                ],
            })
        else:
            messages.append({"role": "user", "content": user_text})

        try:
            if model_alias == "mythos-vision":
                # vision() builds its own message; we already assembled above
                # so call chat() directly with our messages.
                raw = self.api.chat(messages, model_alias="mythos-vision",
                                    max_tokens=2048, temperature=0.3)
            else:
                raw = self.api.chat(messages, model_alias=model_alias)
        except APIError as e:
            intent = Intent()
            intent.text = f"⚠ Mythos hit a limit: {e}"
            return intent

        # Store in memory.
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": raw})

        return self._parse(raw)

    # ----------------------- Parsing ----------------------- #
    def _parse(self, raw: str) -> Intent:
        """Extract mythos-shell and mythos-file blocks from response."""
        intent = Intent()
        text = raw

        # ---- Shell blocks ----
        # 1) Tagged: ```mythos-shell ...
        shell_re_tagged = re.compile(
            r"```mythos-shell\s*\n(.*?)```", re.DOTALL
        )
        # 2) Plain fenced block containing a `# shell:` directive anywhere.
        shell_re_plain = re.compile(
            r"```(?:[a-zA-Z0-9_+-]*)?\s*\n(.*?)```", re.DOTALL
        )
        seen_spans = []  # track consumed spans to avoid double-processing.

        def _in_seen(start: int, end: int) -> bool:
            for s, e in seen_spans:
                if start >= s and end <= e:
                    return True
            return False

        def _extract_shell_block(block: str) -> Tuple[str, str]:
            lines = block.strip().splitlines()
            shell = "powershell"
            cmd_lines = []
            for ln in lines:
                sh_m = re.match(r"#\s*shell:\s*(\w+)", ln.strip())
                if sh_m:
                    shell = sh_m.group(1).lower()
                else:
                    cmd_lines.append(ln)
            return shell, "\n".join(cmd_lines).strip()

        # First pass: tagged blocks.
        for m in shell_re_tagged.finditer(text):
            shell, cmd = _extract_shell_block(m.group(1))
            if cmd:
                intent.shell_blocks.append((shell, cmd))
            seen_spans.append((m.start(), m.end()))

        # Second pass: plain blocks with `# shell:` directive inside.
        for m in shell_re_plain.finditer(text):
            if _in_seen(m.start(), m.end()):
                continue
            block = m.group(1)
            if re.search(r"#\s*shell:\s*\w+", block):
                shell, cmd = _extract_shell_block(block)
                if cmd:
                    intent.shell_blocks.append((shell, cmd))
                    seen_spans.append((m.start(), m.end()))

        # ---- File blocks ----
        # Tagged: ```mythos-file ... with `# path:`
        file_re_tagged = re.compile(
            r"```mythos-file\s*\n(.*?)```", re.DOTALL
        )
        # Plain block with `# path:` directive.
        file_re_plain = re.compile(
            r"```(?:[a-zA-Z0-9_+-]*)?\s*\n(.*?)```", re.DOTALL
        )

        def _extract_file_block(block: str) -> Tuple[str, str]:
            lines = block.strip().splitlines()
            path = ""
            content_lines = []
            for ln in lines:
                p_m = re.match(r"#\s*path:\s*(.+)", ln.strip())
                if p_m:
                    path = p_m.group(1).strip()
                else:
                    content_lines.append(ln)
            return path, "\n".join(content_lines).strip("\n")

        file_seen = []
        for m in file_re_tagged.finditer(text):
            path, content = _extract_file_block(m.group(1))
            if path:
                intent.file_blocks.append((path, content))
            file_seen.append((m.start(), m.end()))
        for m in file_re_plain.finditer(text):
            if any(s <= m.start() and m.end() <= e for s, e in file_seen):
                continue
            block = m.group(1)
            if re.search(r"#\s*path:\s*.+", block):
                # Avoid reusing spans already consumed by shell pass.
                if _in_seen(m.start(), m.end()):
                    continue
                path, content = _extract_file_block(block)
                if path:
                    intent.file_blocks.append((path, content))

        # Clean markers from displayed text for a tidy UI.
        display = text
        for s, e in sorted(seen_spans, key=lambda x: x[0]):
            display = display.replace(text[s:e], "[shell command ready]")
        file_re_clean = re.compile(
            r"```mythos-file\s*\n(.*?)```", re.DOTALL
        )
        display = file_re_clean.sub("[file content ready]", display)
        intent.text = display.strip()
        intent.has_actions = bool(intent.shell_blocks or intent.file_blocks)
        return intent

    # ----------------------- Memory mgmt ----------------------- #
    def clear(self) -> None:
        self.history.clear()
        self.last_tool_results.clear()

    def set_model(self, alias: str) -> bool:
        # Support both primary and alternate code models.
        if alias in SYS_PROMPTS or alias in ("mythos-code-alt", "code-alt"):
            self.current_model = alias if alias.startswith("mythos-") else f"mythos-{alias}"
            return True
        return False

    # ----------------------- Tool-call inference (fallback) ----------------- #
    def _infer_tool_calls_from_text(self, raw: str, cleaned: str) -> List[Any]:
        """
        Fallback for models that don't emit mythos-tool format (e.g. Shannon).
        Detect common patterns in the text + code blocks and convert them to
        ToolCall objects:
          - "create/make file X" + code block -> write_file
          - code block with a filename mention -> write_file
        Returns [] if nothing could be confidently inferred.
        """
        from .tools import ToolCall
        calls: List[Any] = []

        # Find all fenced code blocks.
        block_re = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
        blocks = list(block_re.finditer(raw))
        if not blocks:
            return []

        # Look for a filename in the surrounding text. Common patterns:
        #   "file X.py", "to X", "named X", "save to X", "X.py"
        # Also accept the language hint as a path if it looks like a file.
        full_text = raw
        # Collect filename candidates from explicit mentions.
        file_mentions = re.findall(
            r"(?:file|file named|named|called|to|to file|save to|save as)\s+"
            r"[`'\"]?([A-Za-z0-9_\-./]+\.\w{1,5})[`'\"]?",
            full_text, re.IGNORECASE,
        )
        # Also any bare path-like token ending with an extension near a block.
        bare_paths = re.findall(
            r"\b([A-Za-z0-9_\-]+\.(?:py|js|ts|html|css|json|md|txt|sh|ps1|bat|c|cpp|rs|go|java|rb))\b",
            full_text,
        )
        candidates = file_mentions + bare_paths

        for m in blocks:
            lang = (m.group(1) or "").lower()
            code = m.group(2).strip()
            if not code:
                continue
            # Skip if this block IS already a tool call (shouldn't happen here).
            if lang in ("mythos-tool", "mythos-shell", "mythos-file"):
                continue
            # Pick the best filename candidate.
            path = None
            if candidates:
                path = candidates[0]
            elif lang and lang not in ("text", "txt"):
                # Use language as extension hint: python -> script.py
                ext_map = {"python": "py", "py": "py", "javascript": "js",
                           "js": "js", "typescript": "ts", "html": "html",
                           "css": "css", "bash": "sh", "powershell": "ps1",
                           "json": "json"}
                ext = ext_map.get(lang)
                if ext:
                    path = f"script.{ext}"
            if not path:
                continue
            calls.append(ToolCall(
                name="write_file",
                args={"path": path, "content": code},
            ))
            # Only take the first inferable file to avoid over-eager writes.
            break

        return calls

    # ----------------------- Agentic tool loop ----------------------- #
    def run_with_tools(
        self,
        user_text: str,
        *,
        force_model: Optional[str] = None,
    ) -> Tuple[Intent, int]:
        """
        Execute a multi-step agentic loop with self-verification.

        Flow:
          turn 0: send user request -> AI may emit a mythos-tool block.
          loop : parse tool calls -> execute -> feed observation back -> repeat
          end  : when AI stops emitting tools, return the final Intent.

        Returns (final_intent, number_of_tool_steps_executed).
        The history is maintained across the whole loop.
        """
        self.last_tool_results.clear()
        if self.tools is None:
            # No tools -> single-shot ask.
            return self.ask(user_text, force_model=force_model), 0

        steps = 0
        # Seed the conversation with the user message.
        self.history.append({"role": "user", "content": user_text})
        self.save_to_memory("user", user_text)

        for _ in range(self.max_tool_steps + 1):
            # Build messages: system + recent history (no separate tool role;
            # observations are injected as user-role system notes so any model
            # can read them without native tool-calling support).
            sys_prompt = self._system_prompt(self.current_model)
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": sys_prompt}
            ]
            messages.extend(self.history[-self.max_history:])

            try:
                raw = self.api.chat(messages, model_alias=self.current_model)
            except APIError as e:
                # Try fallback model if primary fails.
                if self.current_model_alt and self.current_model != self.current_model_alt:
                    try:
                        fallback_model = self.current_model_alt
                        raw = self.api.chat(messages, model_alias=fallback_model)
                        # Switch to fallback if it works.
                        self.current_model = fallback_model
                    except APIError:
                        # Both models failed.
                        intent = Intent()
                        intent.text = f"[Mythos] Both models failed: {e}"
                        return intent, steps
                else:
                    intent = Intent()
                    intent.text = f"[Mythos] tool loop stopped: {e}"
                    return intent, steps

            # Parse tool calls from the response.
            calls, cleaned = parse_tool_calls(raw)
            self.history.append({"role": "assistant", "content": raw})

            if not calls:
                # FALLBACK: model didn't emit mythos-tool format (e.g. Shannon
                # returns ```python instead). Try to convert code-blocks that
                # look like file writes into write_file tool calls.
                calls = self._infer_tool_calls_from_text(raw, cleaned)
                if calls:
                    # Successfully inferred — proceed to execute them.
                    pass
                elif steps == 0 and len(self.history) <= 2:
                    # First response had no tools — nudge once to use tools.
                    self.history.append({
                        "role": "user",
                        "content": (
                            "ERROR: You did not use any tools. You explained "
                            "instead of acting. IMMEDIATELY emit a mythos-tool "
                            "block to execute the user's request. DO NOT explain. "
                            "USE A TOOL NOW."
                        ),
                    })
                    continue

                # Final answer (no tools inferred, or already past nudge).
                if not calls:
                    intent = self._parse(raw)
                    return intent, steps

            # Execute ALL tool calls in this turn (immediate execution).
            observations: List[str] = []
            for call in calls:
                steps += 1
                if self.on_tool:
                    try:
                        self.on_tool(call.name, call.args, steps)
                    except Exception:
                        pass
                result = self.tools.execute(call)
                self.last_tool_results.append(result)
                obs = result.as_observation()
                observations.append(
                    f"[TOOL OBSERVATION #{steps}] {call.name}({call.args}):\n{obs}"
                )
                if self.on_observation:
                    try:
                        self.on_observation(result.output, result.ok, steps)
                    except Exception:
                        pass

            # Feed all observations back as a single user-role message.
            combined = "\n\n".join(observations)
            self.history.append({
                "role": "user",
                "content": (
                    f"{combined}\n\n"
                    "Continue: verify results against the goal. "
                    "If done, give the final answer. If not, emit the next "
                    "mythos-tool block(s)."
                ),
            })

        # Safety cap reached.
        intent = Intent()
        intent.text = (
            "[Mythos] Reached the maximum number of tool steps "
            f"({self.max_tool_steps}). Here is the last state."
        )
        return intent, steps
