# Multi-Agent AI System Overview

This project implements a Python-based multi-agent architecture with three specialized components:

1. **SupervisorAgent** — Routes incoming user queries to appropriate agents using Claude's routing capability
2. **IntelligenceAgent** — Aggregates AI news from multiple sources including Reddit, YouTube, X/Twitter, OpenAI/Anthropic/Databricks blogs
3. **TodoAgent** — Manages task lists through conversational interaction with persistent JSON storage
4. **ResearchAgent** — Conducts market research on product/business ideas

## Quick Start

Launch the system via `python main.py` (CLI) or `python telegram_bot.py` (Telegram bot) after installing dependencies and configuring environment variables.

## Technical Stack

The implementation relies on the Claude CLI for all language model interactions. The supervisor employs `claude-opus-4-5` for routing decisions, while both intelligence and todo agents utilize `claude-sonnet-4-5` for efficiency. The front-end leverages the Rich library for terminal styling.

## Required Credentials

- **TELEGRAM_BOT_TOKEN** — from @BotFather (required for Telegram bot)
- **ANTHROPIC_API_KEY** — for Claude (optional if using Claude CLI)
- **REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET** — for Reddit data
- **YOUTUBE_API_KEY** — for YouTube data
- **TWITTER_BEARER_TOKEN** — for Twitter/X data

## Data Persistence

Task state lives in `data/todos.json`, with all agent responses structured as JSON for programmatic handling.
