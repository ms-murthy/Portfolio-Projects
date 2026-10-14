"""PreToolUse hook: blocks Claude Code from reading, searching, editing or printing .env secrets.

Claude Code sends the pending tool call as JSON on stdin. Exit code 2 blocks the call
and the message on stderr is shown to Claude. Exit code 0 lets it through.

Allowed: .env.example / .env.sample / .env.template (names only, no secrets).
"""
import json
import re
import sys

SAFE = {".env.example", ".env.sample", ".env.template"}
# a ".env" file name (optionally .env.local etc.) appearing anywhere in a path or command
ENV_NAME = re.compile(r"(?<![\w.-])\.env(?:\.[\w-]+)?(?![\w-])")
# shell commands that dump environment variables
DUMP_SHELL = re.compile(r"(^|[;&|]\s*)(printenv\b|env\s*($|[;&|])|set\s*($|[;&|])|export\s+-p|"
                        r"Get-ChildItem\s+env:|gci\s+env:|dir\s+env:|ls\s+env:)|\$env:", re.IGNORECASE)
# inline Python that reads or prints environment values
DUMP_PY = re.compile(r"python[0-9.]*\s+(-\w+\s+)*-c\b.*(os\.environ|getenv|dotenv)", re.IGNORECASE | re.DOTALL)
# recursive / hidden-file searches that would sweep up .env
SWEEP = re.compile(r"\bgrep\b[^|;&]*\s-(\w*[rR]\w*)\b|\bgrep\b[^|;&]*--recursive|"
                   r"\brg\b[^|;&]*(--hidden|-uu|--no-ignore)|\bfindstr\b[^|;&]*/s|"
                   r"Select-String\b[^|;&]*-Recurse|-Recurse\b[^|;&]*\|\s*Select-String|"
                   r"\b(cat|type|head|tail|less|more|Get-Content|gc)\s+[^|;&]*\.\*|\b(cat|type|Get-Content)\s+\.[eE]\*", re.IGNORECASE)


def blocked_env_mentions(text: str) -> list[str]:
    return [m for m in ENV_NAME.findall(text) if m.lower() not in SAFE]


def check(payload: dict):
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    texts = [str(v) for v in tool_input.values() if isinstance(v, (str, int, float))]
    joined = " ".join(texts)

    if blocked_env_mentions(joined):
        return f"Blocked: {tool} would touch a .env secrets file. Project rule: never read, search, edit or print .env. Use `python scripts/check_env.py` to check credentials."
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        if DUMP_SHELL.search(cmd) or DUMP_PY.search(cmd):
            return "Blocked: this command could print environment variables or credential values. Use `python scripts/check_env.py`, which shows only set/MISSING."
        if SWEEP.search(cmd):
            return "Blocked: a recursive or hidden-file search could read .env. Search a named folder (buddy/, scripts/, tests/, Data/) or use the Grep tool instead."
    return None


if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    reason = check(payload)
    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
