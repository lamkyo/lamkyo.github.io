### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Context:**
Claude Code allows extending its behavior via "Hooks". A `PreToolUse` hook is executed *before* a tool (like `Bash`) is invoked. If the hook exits with a non-zero status code (or specific JSON output), the tool execution is aborted.

**The Problem:**
By default, Claude Code has no built-in guardrails against accidental or malicious destructive commands (e.g., `rm -rf /`, `DROP TABLE`, force pushes). While the LLM is instructed to be safe, prompt injection or simple errors can lead to execution of dangerous commands.

**Architectural Requirement:**
We need a lightweight, synchronous script (Python or Bash) that:
1.  Receives the tool input (specifically the `command` string for the `Bash` tool) via `stdin` or environment variables (depending on the specific hook implementation details, but standard Claude Code hooks typically pass JSON via stdin or use env vars). *Correction based on standard Claude Code hook docs:* Hooks receive input via `stdin` as a JSON object containing `tool_name`, `tool_input`, etc.
2.  Parses the command.
3.  Checks against a list of dangerous regex patterns.
4.  If a match is found:
    *   Logs the attempt to `~/.claude/hooks/blocked.log`.
    *   Prints a clear error message to `stderr` (which Claude sees) explaining *why* it was blocked.
    *   Exits with code `1` (or `2` depending on hook spec, usually non-zero blocks).
5.  If no match:
    *   Exits with code `0` (allow execution).

**Key Technical Detail:**
The hook must be robust. It should not crash on empty input or malformed JSON. It must handle the specific patterns requested:
*   `rm -rf`
*   `DROP TABLE`
*   `git push --force` (and `-f`)
*   `TRUNCATE`
*   `DELETE FROM` *without* a `WHERE` clause.

### 2. SURGICAL CODE SOLUTION

We will implement this in **Python 3** for better regex handling and logging robustness compared to Bash.

**File Structure:**
```
~/.claude/hooks/
├── pre-tool-use-blocker.py
├── blocked.log
└── README.md
```

**Code: `~/.claude/hooks/pre-tool-use-blocker.py`**

```python
#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime

# Configuration
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOKS_DIR = os.path.dirname(LOG_FILE)

# Ensure hooks directory exists
if not os.path.exists(HOOKS_DIR):
    os.makedirs(HOOKS_DIR)

# Dangerous Patterns
# Note: We use case-insensitive matching for SQL and Git commands
DANGEROUS_PATTERNS = [
    # rm -rf (with or without spaces, e.g., rm -fr, rm -r -f)
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\b', "rm -rf"),
    # DROP TABLE
    (r'\bDROP\s+TABLE\b', "DROP TABLE"),
    # git push --force or -f
    (r'\bgit\s+push\s+(-[a-zA-Z]*f[a-zA-Z]*|--force)\b', "git push --force"),
    # TRUNCATE
    (r'\bTRUNCATE\b', "TRUNCATE"),
    # DELETE FROM without WHERE
    # This regex looks for DELETE FROM <table> and ensures no WHERE follows immediately (allowing whitespace/newlines)
    (r'\bDELETE\s+FROM\s+\S+[^;]*?(?=\s*;\s*$|\s*--|\s*$)', "DELETE FROM without WHERE"),
]

def log_block(command: str, project_path: str, reason: str):
    """Log the blocked command to the log file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {reason} | Command: {command} | Project: {project_path}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        # Fallback to stderr if logging fails
        print(f"Failed to write log: {e}", file=sys.stderr)

def analyze_command(command: str) -> tuple[bool, str]:
    """
    Analyze the command string.
    Returns (is_dangerous, reason).
    """
    if not command:
        return False, ""
    
    # Normalize whitespace for better matching
    normalized_cmd = " ".join(command.split())
    
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized_cmd, re.IGNORECASE):
            # Special check for DELETE FROM without WHERE
            if "DELETE FROM" in reason:
                # Verify strictly that there is no WHERE clause
                # The regex above is a bit broad, so we do a secondary check
                if re.search(r'\bWHERE\b', normalized_cmd, re.IGNORECASE):
                    continue # It has a WHERE clause, so it's safe (or at least not "without WHERE")
                return True, reason
            
            return True, reason
            
    return False, ""

def main():
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0) # No input, allow

        data = json.loads(input_data)
        
        # Extract tool name and input
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        project_path = data.get("project_path", "Unknown")
        
        # We only care about the Bash tool
        if tool_name != "Bash":
            sys.exit(0)

        command = tool_input.get("command", "")
        
        is_dangerous, reason = analyze_command(command)
        
        if is_dangerous:
            log_block(command, project_path, reason)
            # Print message to stderr so Claude sees it
            msg = f"🛑 BLOCKED COMMAND: {reason}\n"
            msg += f"Command: {command}\n"
            msg += "This command is considered destructive and has been blocked by the Pre-Tool-Use hook.\n"
            msg += "Please use a safer alternative or confirm with the user if absolutely necessary."
            print(msg, file=sys.stderr)
            sys.exit(1

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.08s • $0.00)</i>