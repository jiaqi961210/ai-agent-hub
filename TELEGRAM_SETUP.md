# Telegram Setup Guide

Follow these steps to connect your multi-agent system to Telegram.
Takes about 5 minutes.

---

## Step 1: Create a Bot with BotFather

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a **name** for your bot (e.g., "AI Agent Hub")
4. Choose a **username** (must end in `bot`, e.g., `my_ai_agent_hub_bot`)
5. BotFather will give you a **token** — copy it

---

## Step 2: Update your .env

Add this to your `.env` file:

```
TELEGRAM_BOT_TOKEN=your-bot-token-here
```

---

## Step 3: Install dependencies and run

```bash
pip install -r requirements.txt
python telegram_bot.py
```

You should see:
```
Starting Telegram bot (polling)...
   Send messages to your bot or use /news, /todo, /ask, /research
```

---

## How to use it in Telegram

| What you type | What happens |
|---------------|--------------|
| Any message | Supervisor routes to right agent |
| `/news LLM fine-tuning` | Intelligence agent searches |
| `/todo add: review Claude docs` | Todo agent adds the task |
| `/todo list my tasks` | Todo agent lists everything |
| `/ask summarize AI news this week` | Supervisor handles it |
| `/research AI code review tool` | Market research agent |
| `/start` | Show help message |

---

## Optional: Set Bot Commands in BotFather

Send `/setcommands` to @BotFather, select your bot, then paste:

```
news - Get latest AI news
todo - Manage your tasks
ask - Ask the supervisor anything
research - Market research on ideas
start - Show help
```

This adds a nice command menu in Telegram.

---

## Troubleshooting

**Bot not responding?**
→ Make sure `telegram_bot.py` is running and your token is correct

**Timeout errors?**
→ Agent processing can take time. The bot sends "Thinking..." first, then the full response.

**Long messages cut off?**
→ Messages over 4000 chars are automatically split into multiple messages.
