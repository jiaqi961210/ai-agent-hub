"""
Bot Registry — holds all bot Application instances and provides
routing helpers, message dedup, and cross-bot messaging.
"""

from __future__ import annotations

import os
from typing import Optional
from telegram import Bot
from telegram.ext import Application
from bot_config import BOT_CONFIG, AGENT_TO_BOT, USERNAME_TO_BOT


class BotRegistry:
    """Central registry for all bot instances."""

    def __init__(self):
        self.apps: dict[str, Application] = {}
        self.bots: dict[str, Bot] = {}
        self._processing_lock: dict[int, str] = {}

    def build_apps(self):
        """Create Application instances for all configured bots."""
        for key, cfg in BOT_CONFIG.items():
            token = os.getenv(cfg["token_env"])
            if not token:
                print(f"  WARNING: {cfg['token_env']} not set, skipping {cfg['display_name']}")
                continue
            app = Application.builder().token(token).build()
            self.apps[key] = app

    def store_bots(self):
        """Store Bot objects after initialization (call after app.initialize())."""
        for key, app in self.apps.items():
            self.bots[key] = app.bot

    def claim_message(self, message_id: int, bot_key: str) -> bool:
        """Claim a message for processing. Returns True if this bot got the claim."""
        if message_id in self._processing_lock:
            return False
        self._processing_lock[message_id] = bot_key
        # Prune old entries (keep last 500)
        if len(self._processing_lock) > 500:
            keys = list(self._processing_lock.keys())
            for k in keys[:-500]:
                del self._processing_lock[k]
        return True

    def resolve_mention(self, text: str) -> str | None:
        """Check if text contains @BotUsername, return bot_key or None."""
        text_lower = text.lower()
        for username, bot_key in USERNAME_TO_BOT.items():
            if f"@{username}" in text_lower:
                return bot_key
        return None

    def get_bot_for_agent(self, agent_key: str) -> Bot | None:
        """Get the Bot instance for a given agent key."""
        bot_key = AGENT_TO_BOT.get(agent_key)
        if bot_key:
            return self.bots.get(bot_key)
        return None

    def get_bot_key_for_agent(self, agent_key: str) -> str | None:
        """Get the bot key for a given agent key."""
        return AGENT_TO_BOT.get(agent_key)


async def send_long_message(bot: Bot, chat_id: int, text: str):
    """Send a message via a Bot, splitting if it exceeds Telegram's 4096 char limit."""
    max_len = 4000
    if len(text) <= max_len:
        await bot.send_message(chat_id=chat_id, text=text)
        return

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    for chunk in chunks:
        await bot.send_message(chat_id=chat_id, text=chunk)
