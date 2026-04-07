"""
Chat History — shared group chat memory for all agents.
Stores recent messages from the Telegram group so agents
have context of what others said.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "chat_history.json"
MAX_MESSAGES = 50  # Keep last 50 messages


class ChatHistory:
    """Shared group chat memory."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._messages = self._load()

    def _load(self) -> list:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        return []

    def _save(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(self._messages[-MAX_MESSAGES:], f, indent=2)

    def add_user_message(self, user_name: str, text: str):
        """Log a message from the user."""
        self._messages.append({
            "timestamp": datetime.now().isoformat(),
            "from": user_name,
            "type": "user",
            "text": text[:500],
        })
        self._save()

    def add_agent_message(self, agent_name: str, text: str):
        """Log a response from an agent."""
        self._messages.append({
            "timestamp": datetime.now().isoformat(),
            "from": agent_name,
            "type": "agent",
            "text": text[:500],
        })
        self._save()

    def get_recent(self, count: int = 15) -> str:
        """Get recent chat as formatted text for agent context."""
        recent = self._messages[-count:]
        if not recent:
            return "(No chat history yet)"
        lines = []
        for m in recent:
            prefix = "👤" if m["type"] == "user" else "🤖"
            lines.append(f"{prefix} {m['from']}: {m['text'][:200]}")
        return "\n".join(lines)


# Singleton
chat_history = ChatHistory()
