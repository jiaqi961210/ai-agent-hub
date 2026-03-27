"""
Message Bus — shared communication channel for inter-agent messaging.
Agents can send messages to each other, request help, and share context.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BUS_FILE = DATA_DIR / "message_bus.json"


class MessageBus:
    """Central message bus that all agents share."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._messages = self._load()

    def _load(self) -> list:
        if BUS_FILE.exists():
            try:
                with open(BUS_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        return []

    def _save(self):
        # Keep last 100 messages
        with open(BUS_FILE, "w") as f:
            json.dump(self._messages[-100:], f, indent=2)

    def send(self, from_agent: str, to_agent: str, message: str, msg_type: str = "info"):
        """Send a message from one agent to another.

        msg_type: "info", "request", "handoff", "review", "alert"
        """
        self._messages.append({
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "type": msg_type,
            "message": message,
            "read": False,
        })
        self._save()

    def get_messages_for(self, agent_name: str, unread_only: bool = True) -> list:
        """Get messages addressed to a specific agent."""
        msgs = []
        for m in self._messages:
            if m["to"] in (agent_name, "all"):
                if unread_only and m["read"]:
                    continue
                msgs.append(m)
        return msgs

    def mark_read(self, agent_name: str):
        """Mark all messages for an agent as read."""
        for m in self._messages:
            if m["to"] in (agent_name, "all"):
                m["read"] = True
        self._save()

    def get_recent(self, count: int = 10) -> list:
        """Get the most recent messages on the bus."""
        return self._messages[-count:]

    def broadcast(self, from_agent: str, message: str):
        """Send a message to all agents."""
        self.send(from_agent, "all", message, msg_type="info")


# Singleton instance shared by all agents
bus = MessageBus()
