"""
Multi-Bot Telegram Group Chat — each agent is its own bot.
Big Head (Supervisor) routes messages, the correct agent's bot responds.

Run: python telegram_group_bot.py
"""

import os
import sys
import asyncio
import signal
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

from bot_config import BOT_CONFIG
from bot_registry import BotRegistry, send_long_message
from agents.supervisor import SupervisorAgent
from agents.chat_history import chat_history

# Shared instances
registry = BotRegistry()
supervisor = SupervisorAgent()


# ── Big Head (Supervisor) Handlers ───────────────────────────────────────

async def bighead_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start in the group — Big Head introduces the team."""
    await update.message.reply_text(
        "Welcome to the Ximen Nao Agent Hub!\n\n"
        "I'm Big Head — the final reincarnation. I carry all memories "
        "and I'll route your messages to the right agent.\n\n"
        "The Team:\n"
        f"  @ximen_donkey_bot — Donkey (AI News & Intelligence)\n"
        f"  @ximen_ox_bot — Ox (Task Management)\n"
        f"  @ximen_piggie_bot — Pig (Market Research)\n"
        f"  @ximen_dog_bot — Dog (Healthcare & Medical)\n"
        f"  @Lamboeye_bot — Big Head (Supervisor & General Chat)\n\n"
        "Just send a message and I'll route it.\n"
        "Or @mention any agent directly to talk to them.\n\n"
        "Remote control:\n"
        "  /remote <command> — run Claude Code on the Mac\n"
        "  e.g. /remote push changes to github\n"
        "  e.g. /remote what files changed today\n"
        "  e.g. /remote restart the bots"
    )


async def remote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remote — send commands to Claude Code on the Mac."""
    command = " ".join(context.args) if context.args else ""
    if not command:
        await update.message.reply_text(
            "Usage: /remote <command>\n\n"
            "Examples:\n"
            "  /remote push changes to github\n"
            "  /remote what files changed today\n"
            "  /remote show me the last git log\n"
            "  /remote restart the bots\n"
            "  /remote read agents/kk_agent.py and summarize it"
        )
        return

    import json as _json
    from pathlib import Path as _Path
    from datetime import datetime as _dt

    inbox = _Path(__file__).parent / "data" / "remote_inbox.json"
    outbox = _Path(__file__).parent / "data" / "remote_outbox.json"
    cmd_id = str(int(_dt.now().timestamp()))

    # Write command to inbox
    with open(inbox, "w") as f:
        _json.dump({
            "id": cmd_id,
            "command": command,
            "timestamp": _dt.now().isoformat(),
        }, f)

    bot = registry.bots.get("bighead") or update.message.bot
    chat_id = update.message.chat_id
    thinking_msg = await bot.send_message(
        chat_id=chat_id,
        text=f"🖥️ Remote session executing: {command[:100]}..."
    )

    # Poll for result
    loop = asyncio.get_event_loop()

    def wait_for_result():
        for _ in range(600):  # Wait up to 5 minutes
            if outbox.exists():
                try:
                    with open(outbox) as f:
                        data = _json.load(f)
                    if data.get("id") == cmd_id:
                        outbox.unlink()
                        return data.get("result", "No result")
                except Exception:
                    pass
            time.sleep(0.5)
        return "Remote command timed out. Is remote_bridge.py running?"

    import time
    result = await loop.run_in_executor(None, wait_for_result)

    # Delete thinking message
    try:
        await bot.delete_message(chat_id=chat_id, message_id=thinking_msg.message_id)
    except Exception:
        pass

    await send_long_message(bot, chat_id, f"🖥️ Remote result:\n\n{result}")


async def bighead_handle_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Big Head's main handler — routes all non-mentioned group messages."""
    message = update.message
    if not message or not message.text:
        return
    # Skip bot messages
    if message.from_user and message.from_user.is_bot:
        return

    text = message.text.strip()
    if not text:
        return

    msg_id = message.message_id
    chat_id = message.chat_id

    # Log user message to shared chat history
    user_name = message.from_user.first_name or "User"
    chat_history.add_user_message(user_name, text)

    # If another bot is @mentioned, let that bot handle it
    mentioned_bot = registry.resolve_mention(text)
    if mentioned_bot and mentioned_bot != "bighead":
        return

    # Claim the message
    if not registry.claim_message(msg_id, "bighead"):
        return

    # Fast path — skip supervisor for obvious routes
    text_lower = text.lower().strip()
    fast_route = None
    if text_lower in ("hi", "hello", "hey", "yo", "sup", "hola", "start", "help"):
        fast_route = {"route": "kk", "transformed_query": text}
    elif any(kw in text_lower for kw in ["news", "ai update", "what's new", "latest in ai"]):
        fast_route = {"route": "intelligence", "transformed_query": text}
    elif any(kw in text_lower for kw in ["todo", "task", "add to list", "my list"]):
        fast_route = {"route": "todo", "transformed_query": text}
    elif any(kw in text_lower for kw in ["health", "supplement", "medicine", "gout", "cancer", "grandpa", "doctor"]):
        fast_route = {"route": "health", "transformed_query": text}
    elif any(kw in text_lower for kw in ["research", "market", "competitor", "business idea"]):
        fast_route = {"route": "research", "transformed_query": text}
    elif any(kw in text_lower for kw in ["build", "create", "code", "implement", "develop",
                                          "website", "reflect", "improve", "modify", "upgrade",
                                          "evolve", "self-improve", "look at your code",
                                          "edit code", "change the system", "fix"]):
        fast_route = {"route": "kk", "transformed_query": text}

    loop = asyncio.get_event_loop()
    if fast_route:
        routing = fast_route
    else:
        # Full supervisor routing for ambiguous messages
        try:
            routing = await loop.run_in_executor(None, supervisor.route, text)
        except Exception:
            routing = {"route": "kk", "transformed_query": text}

    agent_key = routing.get("route", "kk")
    query = routing.get("transformed_query", text)
    handoff_to = routing.get("handoff_to")
    handoff_instruction = routing.get("handoff_instruction")

    # Find the right bot to respond
    bot = registry.get_bot_for_agent(agent_key)
    if not bot:
        # Fallback to Big Head
        bot = registry.bots.get("bighead")

    # Send a "thinking" message so user knows we're working
    agent_name = supervisor.agents.get(agent_key, (None, "Big Head"))[1]
    is_code_request = any(kw in text.lower() for kw in ["build", "create", "code", "implement",
                                                         "website", "reflect", "improve", "modify",
                                                         "upgrade", "evolve", "develop"])
    if is_code_request:
        thinking_msg = await bot.send_message(chat_id=chat_id,
            text=f"🔧 {agent_name} is spinning up a code session... This may take a couple minutes.")
    else:
        thinking_msg = await bot.send_message(chat_id=chat_id,
            text=f"💭 {agent_name} is thinking...")

    # Keep typing indicator alive in background
    async def keep_typing():
        try:
            while True:
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
    typing_task = asyncio.create_task(keep_typing())

    # Run the primary agent
    try:
        result = await loop.run_in_executor(None, supervisor._run_agent, agent_key, query)
    except Exception as e:
        logger.error(f"Agent {agent_key} error: {e}")
        result = f"Sorry, I hit an error processing that: {str(e)[:200]}"
    finally:
        typing_task.cancel()

    # Delete the "thinking" message
    try:
        await bot.delete_message(chat_id=chat_id, message_id=thinking_msg.message_id)
    except Exception:
        pass

    # Send as the correct bot
    await send_long_message(bot, chat_id, result)

    # Log agent response to shared chat history
    chat_history.add_agent_message(agent_name, result[:500])

    # Handle handoff if present
    if handoff_to and handoff_to in supervisor.agents:
        second_bot = registry.get_bot_for_agent(handoff_to)
        if not second_bot:
            second_bot = registry.bots.get("bighead")

        try:
            await second_bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            pass

        handoff_query = (
            f"{handoff_instruction or 'Continue based on this'}\n\n"
            f"--- Output from previous agent ---\n{result}"
        )
        second_result = await loop.run_in_executor(
            None, supervisor._run_agent, handoff_to, handoff_query
        )
        await send_long_message(second_bot, chat_id, second_result)


# ── Agent Bot Handlers (Donkey, Ox, Pig, Dog) ───────────────────────────

def make_agent_start_handler(bot_key: str):
    """Create a /start handler for an agent bot."""
    cfg = BOT_CONFIG[bot_key]
    intros = {
        "donkey": (
            "I'm Donkey — the first reincarnation of Ximen Nao. "
            "Alert ears, always the first to sense what's coming. "
            "I fetch AI news from RSS, Reddit, YouTube, and X/Twitter.\n\n"
            "Mention me with @ximen_donkey_bot or just ask about AI news!"
        ),
        "ox": (
            "I'm Ox — steady and tireless, I plow through your task list. "
            "Add tasks, mark them done, prioritize — I've got you.\n\n"
            "Mention me with @ximen_ox_bot or ask about your todos!"
        ),
        "pig": (
            "I'm Pig — don't let the name fool you. I'm surprisingly cunning. "
            "Market research, competitor analysis, idea validation — I dig deep.\n\n"
            "Mention me with @ximen_piggie_bot or ask me to research something!"
        ),
        "dog": (
            "I'm Dog — loyal companion, always by your side. "
            "I specialize in healthcare research, supplements, nutrition, "
            "and medical guidance.\n\n"
            "Mention me with @ximen_dog_bot or ask any health question!"
        ),
    }

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(intros.get(bot_key, "Hello!"))

    return handler


def make_agent_mention_handler(bot_key: str):
    """Create a handler that only responds to @mentions for this bot."""
    cfg = BOT_CONFIG[bot_key]
    agent_key = cfg["agent_key"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not message.text:
            return
        if message.from_user and message.from_user.is_bot:
            return

        text = message.text.strip()
        msg_id = message.message_id
        chat_id = message.chat_id

        # Only respond if @mentioned
        mentioned = registry.resolve_mention(text)
        if mentioned != bot_key:
            return

        # Claim the message
        if not registry.claim_message(msg_id, bot_key):
            return

        # Strip the @mention
        clean_text = text
        for username_variant in [f"@{cfg['username']}", f"@{cfg['username'].lower()}"]:
            clean_text = clean_text.replace(username_variant, "").strip()
        if not clean_text:
            clean_text = "hello"

        # Send thinking message
        bot = registry.bots[bot_key]
        display_name = BOT_CONFIG[bot_key]["display_name"]
        thinking_msg = await bot.send_message(chat_id=chat_id,
            text=f"💭 {display_name} is thinking...")

        # Run the agent
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, supervisor._run_agent, agent_key, clean_text
            )
        except Exception as e:
            result = f"Sorry, I hit an error: {str(e)[:200]}"

        # Delete thinking message and send result
        try:
            await bot.delete_message(chat_id=chat_id, message_id=thinking_msg.message_id)
        except Exception:
            pass
        await send_long_message(bot, chat_id, result)

    return handler


def make_agent_dm_handler(bot_key: str):
    """Create a handler for DMs to an agent bot (private chat)."""
    cfg = BOT_CONFIG[bot_key]
    agent_key = cfg["agent_key"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not message.text:
            return

        text = message.text.strip()
        if not text:
            return

        chat_id = message.chat_id
        bot = registry.bots[bot_key]

        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            pass

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, supervisor._run_agent, agent_key, text
        )
        await send_long_message(bot, chat_id, result)

    return handler


# ── Setup Handlers ───────────────────────────────────────────────────────

def setup_all_handlers():
    """Register handlers for all bots."""
    # Big Head — handles all group messages (routes them)
    bighead_app = registry.apps.get("bighead")
    if bighead_app:
        bighead_app.add_handler(CommandHandler("start", bighead_start))
        bighead_app.add_handler(CommandHandler("remote", remote_command))
        bighead_app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
                bighead_handle_group,
            )
        )
        # Big Head also handles DMs directly (as KK)
        bighead_app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                make_agent_dm_handler("bighead"),
            )
        )

    # Agent bots — only respond to @mentions in groups, or DMs
    for bot_key in ["donkey", "ox", "pig", "dog"]:
        app = registry.apps.get(bot_key)
        if not app:
            continue

        app.add_handler(CommandHandler("start", make_agent_start_handler(bot_key)))

        # Group: only respond to @mentions
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
                make_agent_mention_handler(bot_key),
            )
        )

        # DMs: respond to everything
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                make_agent_dm_handler(bot_key),
            )
        )


# ── Main ─────────────────────────────────────────────────────────────────

async def main():
    """Start all 5 bots in a single asyncio loop."""
    print("Building bot instances...")
    registry.build_apps()

    if not registry.apps:
        print("No bot tokens configured. Check your .env file.")
        return

    print(f"  {len(registry.apps)} bots configured:")
    for key in registry.apps:
        cfg = BOT_CONFIG[key]
        print(f"    - {cfg['display_name']} (@{cfg['username']})")

    # Setup handlers before initialization
    setup_all_handlers()

    # Initialize all apps
    print("Initializing bots...")
    for key, app in registry.apps.items():
        await app.initialize()
    registry.store_bots()

    # Start polling for all bots
    print("Starting polling...")
    for key, app in registry.apps.items():
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Start all apps
    for key, app in registry.apps.items():
        await app.start()

    print("\nAll bots are live!")
    print("  Send a message in your group chat to test.")
    print("  Press Ctrl+C to stop.\n")

    # Wait for shutdown signal
    stop_event = asyncio.Event()

    def signal_handler():
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    await stop_event.wait()

    # Graceful shutdown
    print("\nShutting down bots...")
    for key, app in reversed(list(registry.apps.items())):
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
    print("All bots stopped.")


if __name__ == "__main__":
    asyncio.run(main())
