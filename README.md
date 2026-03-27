# AI Agent Hub

A multi-agent AI system that runs on Telegram. Four specialized agents with distinct personalities work together — routing, collaborating, and handing off tasks to give you AI news, task management, market research, and system-level insights, all from a single chat.

Built on the Claude CLI. No API key management needed.

---

## Meet the Team

| Agent | Name | What They Do | Personality |
|-------|------|-------------|-------------|
| Intelligence | **Nova** | Fetches AI news from RSS, Reddit, YouTube, X/Twitter | Hyperactive news junkie who texts at 2am about arxiv papers |
| Todo | **Chip** | Manages tasks — add, complete, delete, prioritize | Supportive life coach with dad joke energy |
| Research | **Max** | Market research, competitor analysis, idea validation | Street-smart analyst who tells it like it is, with a wink |
| Meta | **KK** | System oversight, agent reviews, health checks, strategy | Wise mentor with dry wit who sees the big picture |

A **Supervisor** silently routes every message to the right agent. You just talk naturally.

---

## Architecture

```
You (Telegram)
  |
  v
Telegram Bot (polling)
  |
  v
Supervisor (routes via Claude)
  |
  +--> Nova (Intelligence)  -- RSS, Reddit, YouTube, X/Twitter
  +--> Chip (Todo)           -- JSON persistence, CRUD
  +--> Max  (Research)       -- Web search via Claude CLI
  +--> KK   (Meta)           -- Logs, reviews, health checks
         |
    Message Bus  <-- agents communicate and hand off work
```

**Inter-Agent Communication**: Agents talk to each other through a shared message bus. The supervisor can chain agents together — for example, "get AI news and add the top story to my todo" routes through Nova first, then hands off to Chip.

**Activity Logging**: Every agent interaction is logged. KK can review any agent's recent work and give you an honest assessment.

---

## Quick Start

### Prerequisites

- Python 3.9+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))

### Setup

```bash
# Clone the repo
git clone https://github.com/jiaqi961210/ai-agent-hub.git
cd ai-agent-hub

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env  # or create manually
```

Add your credentials to `.env`:

```env
# Required
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Optional (for full Intelligence Agent functionality)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
YOUTUBE_API_KEY=your-youtube-api-key
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
```

### Run

**Telegram bot** (primary):
```bash
python telegram_bot.py
```

**CLI mode** (no Telegram needed):
```bash
python main.py
```

**Daily news digest** (via cron):
```bash
python daily_news.py
```

---

## Telegram Commands

| Command | Agent | Description |
|---------|-------|-------------|
| `/start` | — | Show available commands |
| `/news [topic]` | Nova | Get latest AI news |
| `/todo [instruction]` | Chip | Manage your task list |
| `/ask [question]` | Supervisor | Auto-route to the best agent |
| `/research [idea]` | Max | Market research and competitor analysis |
| `/kk [question]` | KK | System insights, agent reviews, advice |
| `/status` | KK | Quick system health check |
| `/review` | KK | Audit the last agent's output |
| Any message | Supervisor | Automatically routed |

### Example Conversations

```
You: hey what's up
KK: Hey! Good to see you. Here's what's been happening...

You: what's the latest in AI
Nova: OH BOY do I have news for you! Here are today's top stories...

You: add "read the Claude docs" to my list
Chip: Added it! You've got 3 tasks now — look at you being productive!

You: is there a market for AI code review tools
Max: Pull up a chair, let's talk about this market...

You: get AI news and add anything interesting to my todo
Nova: [fetches news] → hands off to → Chip: [adds tasks]
```

---

## Project Structure

```
ai-agent-hub/
├── telegram_bot.py           # Telegram bot (main entry point)
├── main.py                   # CLI entry point
├── daily_news.py             # Cron-triggered daily AI digest
├── daily_news_runner.sh      # Shell wrapper with retry logic
├── requirements.txt
├── .env                      # Your API keys (git-ignored)
├── agents/
│   ├── supervisor.py         # Routes messages, manages handoffs
│   ├── intelligence_agent.py # Nova — AI news aggregation
│   ├── todo_agent.py         # Chip — task management
│   ├── research_agent.py     # Max — market research
│   ├── kk_agent.py           # KK — meta-agent, system oversight
│   ├── message_bus.py        # Inter-agent communication
│   └── llm.py                # Claude CLI wrapper
└── data/
    ├── todos.json            # Persistent task storage
    ├── agent_logs.json       # Agent activity history
    ├── message_bus.json      # Inter-agent messages
    └── daily_news.md         # Latest news digest
```

---

## How It Works

1. **You send a message** via Telegram (or CLI)
2. **Supervisor** asks Claude to classify the intent and pick the right agent
3. **One agent responds** with its unique personality and expertise
4. **If needed**, the supervisor chains a second agent via handoff (e.g., Nova fetches news, Chip adds a task)
5. **KK logs everything** — you can ask KK to review, audit, or reflect on any agent's work at any time

All LLM calls go through the Claude CLI (`agents/llm.py`), so there's no API key to manage — it uses your existing Claude authentication.

---

## Optional: Daily News Cron

Set up a daily AI news digest at 9am:

```bash
crontab -e
```

Add this line:

```
*/12 9-10 * * * /path/to/ai-agent-hub/daily_news_runner.sh
```

The digest saves to `data/daily_news.md` with a dated archive.

---

## Tech Stack

- **Python 3.9+**
- **Claude CLI** — all LLM interactions (no direct API calls)
- **python-telegram-bot** — Telegram integration (polling, no webhook needed)
- **Rich** — terminal UI for CLI mode
- **feedparser / praw / tweepy** — news source integrations

---

## License

MIT
