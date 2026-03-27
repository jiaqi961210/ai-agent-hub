#!/usr/bin/env python3
"""
Daily AI News — fetches news from each source separately,
analyzes each with a personal lens, and saves the digest.
Triggered by cron at 9am daily.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Ensure we're in the project directory
PROJECT_DIR = Path(__file__).parent
os.chdir(PROJECT_DIR)

sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv
load_dotenv()

from agents.intelligence_agent import IntelligenceAgent
from agents.llm import claude_chat

OUTPUT_DIR = PROJECT_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

DAILY_NEWS_PROMPT = """You are a personal AI advisor who curates AI news with a deeply practical and reflective lens.

You will receive raw content organized by source. For EACH source, pick the Top 5 most significant items.

For each news item, provide:
1. **Headline** — clear, concise title
2. **What happened** — 2-3 sentence summary of the development
3. **How this can help you make money** — concrete ways this could create income opportunities, career advantages, business ideas, or investment signals. Be specific and actionable, not generic.
4. **How this can help you grow as a person** — how this development connects to self-discovery, learning new skills, expanding your thinking, creativity, or living a more intentional life. Be thoughtful and genuine.

Format the output as:

## [Source Name]

### 1. Headline
**What happened:** ...
**Money opportunity:** ...
**Personal growth:** ...

(repeat for each item)

At the end, include a section:

## Today's Key Takeaway
A brief, motivating paragraph that ties together the biggest themes of the day — what they mean for someone who wants to stay ahead financially and live a meaningful life.

Be honest and specific. Skip hype. If something isn't relevant to money or growth, say so briefly and move on. The reader is smart and wants real insight, not fluff."""


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = OUTPUT_DIR / "daily_news.md"
    archive_file = OUTPUT_DIR / f"news_{today}.md"

    print(f"[{today}] Fetching AI news from all sources...")

    agent = IntelligenceAgent()

    # Fetch from each source separately
    sections = {}

    print("  Fetching RSS feeds...")
    rss_items = agent.fetch_rss()
    sections["RSS Feeds"] = rss_items

    print("  Fetching Reddit...")
    reddit_items = agent.fetch_reddit()
    sections["Reddit"] = reddit_items

    print("  Fetching YouTube...")
    youtube_items = agent.fetch_youtube()
    sections["YouTube"] = youtube_items

    print("  Fetching X/Twitter...")
    twitter_items = agent.fetch_twitter()
    sections["X/Twitter"] = twitter_items

    # Format raw content organized by source
    raw_content = f"Date: {today}\n\n"
    for source_group, items in sections.items():
        raw_content += f"=== {source_group} ===\n\n"
        for item in items:
            raw_content += f"[{item['source']}] {item['title']}\n"
            raw_content += f"{item.get('summary', '')}\n"
            raw_content += f"{item.get('link', '')}\n\n"

    print("  Analyzing with Claude...")
    result = claude_chat(DAILY_NEWS_PROMPT, raw_content)

    # Build the markdown output
    content = f"# Daily AI Intelligence Brief — {today}\n\n{result}\n"

    # Save to both current and archive files
    output_file.write_text(content)
    archive_file.write_text(content)

    print(f"Saved to {output_file}")
    print(f"Archived to {archive_file}")

    # macOS notification
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "Your daily AI intelligence brief is ready!" '
            f'with title "AI News" subtitle "{today}"'
        ], timeout=5)
    except Exception:
        pass


if __name__ == "__main__":
    main()
