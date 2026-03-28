"""
Telegram Bot — connects your Multi-Agent System to Telegram
Uses python-telegram-bot with polling (no public URL needed).

Run: python telegram_bot.py
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
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

# Import your supervisor
from agents.supervisor import SupervisorAgent

supervisor = SupervisorAgent()


def think(user_input: str) -> str:
    """Run supervisor and return response string."""
    try:
        return supervisor.run(user_input)
    except Exception as e:
        return f"Error from agent: {e}"


# ── Command Handlers ─────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "Multi-Agent AI System\n\n"
        "Commands:\n"
        "/news [topic] - Get latest AI news\n"
        "/todo [instruction] - Manage your tasks\n"
        "/ask [question] - Ask the supervisor anything\n"
        "/research [idea] - Market research on ideas\n"
        "/health [question] - Doc: healthcare research & advice\n"
        "/kk [question] - KK Agent: system insights & agent reviews\n"
        "/status - Check system health & agent activity\n\n"
        "Or just send me any message and I'll route it to the right agent!"
    )


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /news command."""
    query = " ".join(context.args) if context.args else "latest AI news"
    await update.message.reply_text("Fetching AI news...")

    from agents.intelligence_agent import IntelligenceAgent
    agent = IntelligenceAgent()
    result = agent.run(query)
    await send_long_message(update, result)


async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /todo command."""
    instruction = " ".join(context.args) if context.args else "list my tasks"

    from agents.todo_agent import TodoAgent
    agent = TodoAgent()
    result = agent.run(instruction)
    await send_long_message(update, result)


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask command — goes through supervisor."""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /ask what are the latest LLM releases?")
        return

    await update.message.reply_text("Thinking...")
    response = think(query)
    await send_long_message(update, response)


async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /research command."""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /research AI-powered code review tool")
        return

    await update.message.reply_text("Researching...")

    from agents.research_agent import ResearchAgent
    agent = ResearchAgent()
    result = agent.run(query)
    await send_long_message(update, result)


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command — Doc agent for healthcare research."""
    query = " ".join(context.args) if context.args else "give me an overview of the current care plan and recommendations for grandpa"
    await update.message.reply_text("Doc is researching... (this may take a moment for thorough answers)")

    from agents.health_agent import HealthAgent
    agent = HealthAgent()
    result = agent.run(query)
    await send_long_message(update, result)


async def kk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kk command — KK Agent for system insights and reviews."""
    query = " ".join(context.args) if context.args else "give me a quick overview of the system and what's been happening"
    await update.message.reply_text("KK Agent thinking...")

    from agents.kk_agent import KKAgent
    agent = KKAgent()
    result = agent.run(query)
    await send_long_message(update, result)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command — quick system health check."""
    from agents.kk_agent import KKAgent
    agent = KKAgent()
    result = agent.run("Give me a concise system health check: which APIs are configured, what's the todo list status, any recent agent activity, and any issues I should know about.")
    await send_long_message(update, result)


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /review command — KK Agent reviews last agent output."""
    query = " ".join(context.args) if context.args else "review the most recent agent activity and give me your honest assessment"
    await update.message.reply_text("KK Agent reviewing...")

    from agents.kk_agent import KKAgent
    agent = KKAgent()
    result = agent.run(query)
    await send_long_message(update, result)


# ── Message Handler (DMs and group messages) ─────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message — routes through the supervisor."""
    text = update.message.text.strip()
    if not text:
        return

    await update.message.reply_text("Thinking...")
    response = think(text)
    await send_long_message(update, response)


# ── Helpers ───────────────────────────────────────────────────────────────

async def send_long_message(update: Update, text: str):
    """Send a message, splitting if it exceeds Telegram's 4096 char limit."""
    # Convert markdown bold **text** to Telegram-friendly format
    max_len = 4000
    if len(text) <= max_len:
        await update.message.reply_text(text)
    else:
        # Split into chunks
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            # Find a good split point
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip()

        for chunk in chunks:
            await update.message.reply_text(chunk)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error: {context.error}")


# ── Start ─────────────────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("Missing TELEGRAM_BOT_TOKEN in .env")
        print("   Get one from @BotFather on Telegram")
        exit(1)

    print("Starting Telegram bot (polling)...")
    print("   Send messages to your bot or use /news, /todo, /ask, /research, /kk, /status, /review")

    app = Application.builder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("todo", todo_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("kk", kk_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("review", review_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Start polling (no webhook/public URL needed)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
