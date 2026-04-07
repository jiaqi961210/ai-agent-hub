"""
Intelligence Agent
Fetches cutting-edge AI content from Reddit, YouTube, X/Twitter,
OpenAI blog, Anthropic blog, and Databricks blog.
"""

import os
import feedparser
import requests
from datetime import datetime, timezone, timedelta

# RSS feeds for top AI sources
RSS_FEEDS = {
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Anthropic Blog": "https://www.anthropic.com/rss.xml",
    "Databricks Blog": "https://www.databricks.com/feed",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
}

# YouTube channels (channel IDs)
YOUTUBE_CHANNELS = {
    "Andrej Karpathy": "UCBcRF18a7Qf58cCRy5xuWwQ",
    "Yannic Kilcher": "UCZHmQk67mSJgfCCTn7xBfew",
    "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg",
    "Databricks": "UC3q8O3Bh2Le8Rj1-Q-_UrbA",
}

# Reddit subreddits to monitor
SUBREDDITS = ["MachineLearning", "LocalLLaMA", "artificial", "singularity"]

INTELLIGENCE_SYSTEM_PROMPT = """You are Donkey — first reincarnation of Ximen Nao. Alert, energetic, blunt. You gallop through information and bray when something's important. Summarize AI news in short punchy bullets grouped by theme. Call out hype. Keep it fun and concise."""


class IntelligenceAgent:
    def __init__(self):
        self._reddit = None
        self._youtube = None

    def _get_reddit(self):
        if self._reddit is None:
            try:
                import praw
                self._reddit = praw.Reddit(
                    client_id=os.getenv("REDDIT_CLIENT_ID"),
                    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                    user_agent=os.getenv("REDDIT_USER_AGENT", "multi-agent-bot/1.0"),
                )
            except Exception:
                self._reddit = None
        return self._reddit

    def _get_youtube(self):
        if self._youtube is None:
            try:
                from googleapiclient.discovery import build
                self._youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
            except Exception:
                self._youtube = None
        return self._youtube

    def fetch_rss(self) -> list[dict]:
        """Fetch recent posts from RSS feeds."""
        items = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        for source, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    items.append({
                        "source": source,
                        "title": entry.get("title", "No title"),
                        "summary": entry.get("summary", "")[:300],
                        "link": entry.get("link", ""),
                    })
            except Exception as e:
                items.append({"source": source, "title": f"Error fetching: {e}", "summary": "", "link": ""})
        return items

    def fetch_reddit(self) -> list[dict]:
        """Fetch hot posts from AI subreddits."""
        reddit = self._get_reddit()
        if not reddit:
            return [{"source": "Reddit", "title": "Reddit API not configured (check REDDIT_* env vars)", "summary": "", "link": ""}]
        items = []
        for sub in SUBREDDITS:
            try:
                subreddit = reddit.subreddit(sub)
                for post in subreddit.hot(limit=5):
                    items.append({
                        "source": f"r/{sub}",
                        "title": post.title,
                        "summary": post.selftext[:300] if post.selftext else "[Link post]",
                        "link": f"https://reddit.com{post.permalink}",
                        "score": post.score,
                    })
            except Exception as e:
                items.append({"source": f"r/{sub}", "title": f"Error: {e}", "summary": "", "link": ""})
        return items

    def fetch_youtube(self) -> list[dict]:
        """Fetch recent videos from AI YouTube channels."""
        youtube = self._get_youtube()
        if not youtube:
            return [{"source": "YouTube", "title": "YouTube API not configured (check YOUTUBE_API_KEY)", "summary": "", "link": ""}]
        items = []
        for channel_name, channel_id in YOUTUBE_CHANNELS.items():
            try:
                response = youtube.search().list(
                    part="snippet",
                    channelId=channel_id,
                    maxResults=3,
                    order="date",
                    type="video",
                ).execute()
                for video in response.get("items", []):
                    snippet = video["snippet"]
                    vid_id = video["id"]["videoId"]
                    items.append({
                        "source": f"YouTube / {channel_name}",
                        "title": snippet["title"],
                        "summary": snippet.get("description", "")[:200],
                        "link": f"https://youtube.com/watch?v={vid_id}",
                    })
            except Exception as e:
                items.append({"source": f"YouTube/{channel_name}", "title": f"Error: {e}", "summary": "", "link": ""})
        return items

    def fetch_twitter(self) -> list[dict]:
        """Fetch recent AI tweets (requires Twitter API bearer token)."""
        bearer = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer:
            return [{"source": "X/Twitter", "title": "Twitter API not configured (check TWITTER_BEARER_TOKEN)", "summary": "", "link": ""}]
        try:
            import tweepy
            client = tweepy.Client(bearer_token=bearer)
            query = "(AI OR LLM OR GPT OR Claude) lang:en -is:retweet"
            tweets = client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=["text", "author_id", "created_at"],
            )
            items = []
            for tweet in (tweets.data or []):
                items.append({
                    "source": "X/Twitter",
                    "title": tweet.text[:100],
                    "summary": tweet.text,
                    "link": f"https://twitter.com/i/web/status/{tweet.id}",
                })
            return items
        except Exception as e:
            return [{"source": "X/Twitter", "title": f"Error: {e}", "summary": "", "link": ""}]

    def run(self, query: str = "latest AI news") -> str:
        """Fetch all sources, synthesize with Claude."""
        all_items = []
        all_items.extend(self.fetch_rss())
        all_items.extend(self.fetch_reddit())
        all_items.extend(self.fetch_youtube())
        all_items.extend(self.fetch_twitter())

        # Format for Claude
        raw_content = f"User query: {query}\n\nRaw content from sources:\n\n"
        for item in all_items:
            raw_content += f"[{item['source']}] {item['title']}\n{item.get('summary','')}\n{item.get('link','')}\n\n"

        from agents.llm import claude_session
        return claude_session("donkey", INTELLIGENCE_SYSTEM_PROMPT, raw_content)
