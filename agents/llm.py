"""
LLM helper — calls Claude via the `claude` CLI (Claude Code),
so no API key is needed. Uses the user's Max subscription.
"""

import os
import json
import subprocess


def claude_chat(system_prompt: str, user_message: str, max_tokens: int = 1500) -> str:
    """Send a message to Claude via the claude CLI and return the response text."""
    full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"

    # Remove CLAUDECODE env var to allow nested CLI calls
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    result = subprocess.run(
        [
            "claude", "-p", full_prompt,
            "--output-format", "json",
            "--model", "sonnet",
            "--no-session-persistence",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd="/tmp",  # avoid loading project CLAUDE.md
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")

    # Parse the JSON output from claude CLI
    data = json.loads(result.stdout)
    # The JSON output has a "result" field with the text
    return data.get("result", result.stdout).strip()
