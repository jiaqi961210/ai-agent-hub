"""
Remote Bridge — watches for commands from Telegram and executes them
in a persistent Claude Code session on this Mac.

This runs alongside telegram_group_bot.py as a separate process.
Commands come in via data/remote_inbox.json, results go to data/remote_outbox.json.
"""

import json
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
INBOX = DATA_DIR / "remote_inbox.json"
OUTBOX = DATA_DIR / "remote_outbox.json"

DATA_DIR.mkdir(exist_ok=True)


def run_command(command: str) -> str:
    """Execute a command via Claude Code with full project access."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    prompt = (
        f"You are working in the project: {PROJECT_DIR}\n"
        f"Execute this command from the user: {command}\n"
        f"Keep your response concise for Telegram (under 3000 chars)."
    )

    proc = subprocess.Popen(
        [
            "claude", "-p", "-",
            "--output-format", "json",
            "--model", "sonnet",
            "--dangerously-skip-permissions",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(PROJECT_DIR),
    )

    try:
        stdout, stderr = proc.communicate(input=prompt, timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        return "Command timed out after 5 minutes."

    if proc.returncode != 0:
        return f"Error: {stderr[:500]}"

    try:
        data = json.loads(stdout)
        return data.get("result", stdout)[:3000]
    except json.JSONDecodeError:
        return stdout[:3000]


def main():
    print(f"Remote Bridge running. Watching {INBOX}")
    print(f"Project: {PROJECT_DIR}")
    print("Waiting for commands from Telegram...\n")

    # Clear any stale inbox
    if INBOX.exists():
        INBOX.unlink()

    while True:
        try:
            if INBOX.exists():
                with open(INBOX) as f:
                    cmd_data = json.load(f)

                # Remove inbox immediately so we don't re-process
                INBOX.unlink()

                command = cmd_data.get("command", "")
                cmd_id = cmd_data.get("id", "unknown")
                timestamp = cmd_data.get("timestamp", "")

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Received: {command[:80]}...")

                # Execute
                result = run_command(command)

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Done. Result: {result[:80]}...")

                # Write result to outbox
                with open(OUTBOX, "w") as f:
                    json.dump({
                        "id": cmd_id,
                        "command": command,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }, f, indent=2)

            time.sleep(1)  # Poll every second

        except KeyboardInterrupt:
            print("\nRemote Bridge stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
