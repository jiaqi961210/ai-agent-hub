"""
LLM helper — calls Claude via the `claude` CLI (Claude Code),
so no API key is needed. Uses the user's Max subscription.

Supports two modes:
- claude_chat(): stateless one-shot calls (for routing, etc.)
- claude_session(): persistent session per agent (remembers conversation)
"""

import os
import json
import subprocess
import uuid

# Generate stable UUIDs per session name (deterministic from name)
def _session_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ximen-nao.{name}"))


def _run_claude(cmd: list, input_text: str, env: dict, timeout: int = 180, cwd: str = "/tmp"):
    """Run claude CLI with stdin piping to handle long prompts."""
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=env, cwd=cwd,
    )
    try:
        stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        raise
    return type('R', (), {'returncode': proc.returncode, 'stdout': stdout, 'stderr': stderr})()


def claude_chat(system_prompt: str, user_message: str, max_tokens: int = 1500) -> str:
    """Stateless one-shot call. No memory between calls."""
    full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    result = _run_claude(
        ["claude", "-p", "-", "--output-format", "json", "--model", "sonnet", "--no-session-persistence"],
        input_text=full_prompt, env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    return data.get("result", result.stdout).strip()


# Track which sessions have been initialized with their system prompt
_initialized_sessions = set()


def claude_session(session_id: str, system_prompt: str, user_message: str) -> str:
    """Persistent session call. Each session_id maintains its own conversation history.

    First call with a new session_id includes the system prompt to establish persona.
    Subsequent calls just send the user message — Claude remembers the context.
    """
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    # First call: include system prompt to establish persona
    if session_id not in _initialized_sessions:
        prompt = f"{system_prompt}\n\n---\n\n{user_message}"
        _initialized_sessions.add(session_id)
    else:
        # Subsequent calls: just the user message, session has context
        prompt = user_message

    cmd = [
        "claude", "-p", "-",
        "--output-format", "json",
        "--model", "sonnet",
        "--session-id", _session_uuid(session_id),
    ]

    result = _run_claude(cmd, input_text=prompt, env=env)

    if result.returncode != 0:
        # If session fails, fall back to stateless
        return claude_chat(system_prompt, user_message)

    data = json.loads(result.stdout)
    return data.get("result", result.stdout).strip()


def claude_session_inject(session_id: str, system_prompt: str, message: str, from_agent: str) -> str:
    """Send a message into a session as if it came from another agent.
    Used for inter-agent communication within sessions.
    """
    injected = f"[Message from {from_agent}]: {message}\n\nRespond to this in character."
    return claude_session(session_id, system_prompt, injected)


# Project root for code sessions
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def claude_code_session(session_id: str, prompt: str, allowed_tools: str = "Read,Edit,Write,Bash") -> str:
    """Full Claude Code session with file access. Agents can read, edit, and write code.

    This gives agents the ability to:
    - Read their own source code and prompts
    - Modify system prompts and agent behavior
    - Create new files or features
    - Run commands to inspect the system

    The session runs in the project directory with access to specified tools.
    """
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    cmd = [
        "claude", "-p", "-",
        "--output-format", "json",
        "--model", "sonnet",
        "--dangerously-skip-permissions",
    ]

    result = _run_claude(cmd, input_text=prompt, env=env, timeout=300, cwd=PROJECT_DIR)

    if result.returncode != 0:
        return f"Code session error: {result.stderr.strip()[:500]}"

    data = json.loads(result.stdout)
    return data.get("result", result.stdout).strip()
