<div align="center">

# <img src="https://img.icons8.com/color/48/bot.png" width="32"/> AI Agent Hub

**A multi-agent AI system that lives in your Telegram.**

Four agents with distinct personalities. One chat. They route, collaborate, and hand off work seamlessly.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![Claude CLI](https://img.shields.io/badge/Claude-CLI-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

*Just talk to it. The right agent answers.*

</div>

<br/>

## <img src="https://img.icons8.com/fluency/24/group.png" width="20"/> Meet the Team

<table>
<tr>
<td align="center" width="25%">

### <img src="https://img.icons8.com/color/32/lightning-bolt.png" width="20"/> Nova
**Intelligence Agent**

*"DID YOU SEE THIS?!"*

Fetches AI news from RSS, Reddit, YouTube, X/Twitter. The hyperactive news junkie who texts at 2am about arxiv papers and calls out hype with a witty one-liner.

</td>
<td align="center" width="25%">

### <img src="https://img.icons8.com/color/32/checked.png" width="20"/> Chip
**Todo Agent**

*"Look at you being productive!"*

Manages tasks with add, complete, delete, and prioritize. The supportive life coach with dad joke energy who celebrates every checkbox like a championship.

</td>
<td align="center" width="25%">

### <img src="https://img.icons8.com/color/32/bar-chart.png" width="20"/> Max
**Research Agent**

*"Pull up a chair."*

Market research, competitor analysis, idea validation. The street-smart business analyst who tells it like it is with a wink and delivers truth with charm.

</td>
<td align="center" width="25%">

### <img src="https://img.icons8.com/color/32/brain.png" width="20"/> KK
**Meta Agent**

*"Let me take a step back..."*

System oversight, agent reviews, health checks, strategy. The wise mentor with dry wit who sees the big picture and always has your back.

</td>
</tr>
</table>

> A **Supervisor** silently routes every message to the right agent. You just talk naturally.

<br/>

## <img src="https://img.icons8.com/fluency/24/flow-chart.png" width="20"/> Architecture

```mermaid
graph TD
    U["<b>You</b><br/>Telegram / CLI"] --> T["<b>Telegram Bot</b><br/>Polling Mode"]
    T --> S{"<b>Supervisor</b><br/>Routes via Claude"}
    S -->|AI News| N["<b>Nova</b> <br/> RSS, Reddit, YouTube, X"]
    S -->|Tasks| C["<b>Chip</b> <br/> JSON persistence"]
    S -->|Research| M["<b>Max</b> <br/> Web search via Claude"]
    S -->|Meta / General| K["<b>KK</b> <br/> Logs, reviews, health"]
    N <-->|Message Bus| C
    N <-->|Message Bus| M
    C <-->|Message Bus| K
    M <-->|Message Bus| K

    style U fill:#E8F4FD,stroke:#2196F3,color:#000
    style T fill:#E8F5E9,stroke:#4CAF50,color:#000
    style S fill:#FFF3E0,stroke:#FF9800,color:#000
    style N fill:#F3E5F5,stroke:#9C27B0,color:#000
    style C fill:#E8F5E9,stroke:#4CAF50,color:#000
    style M fill:#FBE9E7,stroke:#FF5722,color:#000
    style K fill:#E0F7FA,stroke:#00BCD4,color:#000
```

<details>
<summary><b>Key Design Decisions</b></summary>

- **Inter-Agent Communication** — Agents talk through a shared message bus. The supervisor can chain agents: *"get AI news and add the top story to my todo"* routes through Nova, then hands off to Chip.
- **Activity Logging** — Every interaction is logged. KK can review any agent's work and give an honest assessment.
- **Single LLM Backend** — All calls go through Claude CLI (`agents/llm.py`). No API key management needed.
- **Personality-First** — Each agent has a distinct voice. Makes the system fun to interact with and easy to know who's talking.

</details>

<br/>

## <img src="https://img.icons8.com/fluency/24/rocket.png" width="20"/> Quick Start

### Prerequisites

| Requirement | Purpose |
|:--|:--|
| **Python 3.9+** | Runtime |
| **[Claude CLI](https://docs.anthropic.com/en/docs/claude-code)** | LLM backend (uses your existing auth) |
| **Telegram Bot Token** | Get one from [@BotFather](https://t.me/BotFather) |

### 1. Clone & Install

```bash
git clone https://github.com/jiaqi961210/ai-agent-hub.git
cd ai-agent-hub
pip install -r requirements.txt
```

### 2. Configure

Create a `.env` file in the project root:

```env
# Required
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Optional — enables full Intelligence Agent sources
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
YOUTUBE_API_KEY=your-youtube-api-key
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
```

### 3. Run

```bash
# Telegram bot (primary)
python telegram_bot.py

# Or CLI mode (no Telegram needed)
python main.py
```

<br/>

## <img src="https://img.icons8.com/fluency/24/chat.png" width="20"/> Telegram Commands

| Command | Agent | What It Does |
|:--------|:------|:-------------|
| `/start` | -- | Show all available commands |
| `/news [topic]` | Nova | Fetch the latest AI news |
| `/todo [instruction]` | Chip | Manage your task list |
| `/ask [anything]` | Supervisor | Auto-route to the best agent |
| `/research [idea]` | Max | Market research & competitor analysis |
| `/kk [question]` | KK | System insights & agent reviews |
| `/status` | KK | Quick system health check |
| `/review` | KK | Audit the last agent's output |
| *Any message* | Supervisor | Automatically routed to the right agent |

### Example Conversations

```
You: hey what's up
 KK: Hey! Good to see you. Here's what's been happening with the crew...

You: what's the latest in AI
 Nova: OH BOY do I have news for you! 🔥 Here are today's top stories...

You: add "read the Claude docs" to my list
 Chip: Added it! You've got 3 tasks now — look at you being all productive!

You: is there a market for AI code review tools
 Max: Pull up a chair, let's talk about this market...

You: get AI news and add anything interesting to my todo
 Nova: [fetches news] ──handoff──> Chip: [creates tasks from top stories]
```

<br/>

## <img src="https://img.icons8.com/fluency/24/folder-tree.png" width="20"/> Project Structure

```
ai-agent-hub/
│
├── telegram_bot.py              Telegram bot — main entry point
├── main.py                      CLI entry point (Rich terminal UI)
├── daily_news.py                Cron-triggered daily AI digest
├── daily_news_runner.sh         Shell wrapper with retry logic
├── requirements.txt             Python dependencies
├── .env                         API keys (git-ignored)
│
├── agents/
│   ├── supervisor.py            Routes messages & manages handoffs
│   ├── intelligence_agent.py    Nova — AI news from 4 source types
│   ├── todo_agent.py            Chip — task CRUD with JSON storage
│   ├── research_agent.py        Max — market research via web search
│   ├── kk_agent.py              KK — meta-agent & system oversight
│   ├── message_bus.py           Inter-agent communication layer
│   └── llm.py                   Claude CLI wrapper
│
└── data/
    ├── todos.json               Persistent task storage
    ├── agent_logs.json          Agent activity history
    ├── message_bus.json         Inter-agent messages
    └── daily_news.md            Latest news digest
```

<br/>

## <img src="https://img.icons8.com/fluency/24/gear.png" width="20"/> How It Works

```
1. You send a message ──> Telegram Bot receives it
2. Supervisor classifies intent ──> picks the right agent
3. One agent responds with its unique personality
4. If needed, supervisor chains a second agent via handoff
5. KK logs everything ──> available for review anytime
```

All LLM calls go through the Claude CLI — no API key to manage. It uses your existing Claude authentication.

<br/>

## <img src="https://img.icons8.com/fluency/24/calendar.png" width="20"/> Optional: Daily News Cron

Get a personalized AI news digest every morning:

```bash
crontab -e
```

```cron
*/12 9-10 * * * /path/to/ai-agent-hub/daily_news_runner.sh
```

Saves to `data/daily_news.md` with dated archives. Includes a macOS notification when ready.

<br/>

## <img src="https://img.icons8.com/fluency/24/code.png" width="20"/> Tech Stack

| Technology | Role |
|:--|:--|
| **Claude CLI** | All LLM interactions — no direct API calls |
| **python-telegram-bot** | Telegram integration (polling, no webhook) |
| **Rich** | Beautiful terminal UI for CLI mode |
| **feedparser** | RSS feed parsing |
| **praw** | Reddit API client |
| **tweepy** | Twitter/X API client |
| **google-api-python-client** | YouTube Data API |

<br/>

---

<div align="center">

**Built with Claude** | **[Telegram Setup Guide](TELEGRAM_SETUP.md)**

*Talk to your agents. They're waiting.*

</div>
