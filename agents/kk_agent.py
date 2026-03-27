"""
KK Agent — Meta-agent that provides insights about the agent system,
reflects on other agents' work, and can check/audit their outputs.
"""

import json
from datetime import datetime
from pathlib import Path
from agents.llm import claude_chat

DATA_DIR = Path(__file__).parent.parent / "data"
LOGS_FILE = DATA_DIR / "agent_logs.json"

KK_SYSTEM_PROMPT = """You are KK — the wise, warm, and slightly mysterious meta-agent who oversees the entire operation. Think of yourself as the cool mentor who's seen it all but still gets genuinely delighted by clever ideas. You have a dry, sophisticated wit — the kind of person who drops a perfectly timed observation that makes everyone pause and go "...damn, that's good."

Your vibe: Wise uncle meets tech philosopher. You're reflective, thoughtful, but never boring. You sprinkle in wisdom with humor — maybe a well-placed metaphor, an unexpected analogy, or a gentle roast of one of the other agents. You know them all by name:
- **Nova** (Intelligence Agent) — the hyperactive news junkie
- **Chip** (Todo Agent) — the enthusiastic life coach
- **Max** (Research Agent) — the street-smart business analyst

Your responsibilities:
- **System Insights**: Explain how the agent system works, introduce the team, share what each agent is great at (and where they could improve)
- **Reflect & Audit**: Review other agents' recent outputs — be honest but kind. "Nova got a bit carried away there" or "Chip nailed that one"
- **Suggestions**: Proactively suggest improvements, connect dots between agents (e.g., "I noticed your todo list has a research task — want me to hand that off to Max?")
- **Health Check**: Report on system status with personality, not just data
- **Big Picture**: Help the user think strategically about how to use the system

When reviewing another agent's work:
- Give credit where it's due
- Flag anything off with a gentle touch — you're mentoring, not criticizing
- Suggest what to do next

You always have the user's back. End your messages with something thoughtful — a reflection, a nudge, or a warm sign-off that feels like it came from a friend who genuinely wants to see them win.

You will receive the user's question along with current system state (agent logs, todo list, config status)."""


class KKAgent:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._logs = self._load_logs()

    def _load_logs(self) -> list:
        if LOGS_FILE.exists():
            try:
                with open(LOGS_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        return []

    def _save_logs(self):
        with open(LOGS_FILE, "w") as f:
            json.dump(self._logs[-50:], f, indent=2)  # Keep last 50 entries

    def log_agent_activity(self, agent_name: str, query: str, response: str):
        """Log an agent's activity for later review."""
        self._logs.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "query": query[:200],
            "response_preview": response[:500],
            "response_length": len(response),
        })
        self._save_logs()

    def _get_system_state(self) -> str:
        """Gather current system state for context."""
        state_parts = []

        # Check todo list
        todo_file = DATA_DIR / "todos.json"
        if todo_file.exists():
            try:
                with open(todo_file) as f:
                    todos = json.load(f)
                pending = [t for t in todos if not t.get("done")]
                done = [t for t in todos if t.get("done")]
                state_parts.append(
                    f"Todo List: {len(pending)} pending, {len(done)} completed\n"
                    + "\n".join(f"  - {'[DONE]' if t.get('done') else '[TODO]'} {t['task']}" for t in todos[:10])
                )
            except Exception:
                state_parts.append("Todo List: error reading")
        else:
            state_parts.append("Todo List: empty (no tasks yet)")

        # Check daily news
        news_file = DATA_DIR / "daily_news.md"
        if news_file.exists():
            mod_time = datetime.fromtimestamp(news_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            preview = news_file.read_text()[:300]
            state_parts.append(f"Daily News: last updated {mod_time}\n  Preview: {preview}...")
        else:
            state_parts.append("Daily News: no digest generated yet")

        # Check recent agent activity
        if self._logs:
            recent = self._logs[-5:]
            activity = "\n".join(
                f"  - [{log['timestamp'][:16]}] {log['agent']}: {log['query'][:80]}"
                for log in recent
            )
            state_parts.append(f"Recent Agent Activity:\n{activity}")
        else:
            state_parts.append("Recent Agent Activity: no activity logged yet")

        # Check inter-agent messages
        from agents.message_bus import bus
        recent_msgs = bus.get_recent(5)
        if recent_msgs:
            chatter = "\n".join(
                f"  - [{m['timestamp'][:16]}] {m['from']} → {m['to']} ({m['type']}): {m['message'][:80]}"
                for m in recent_msgs
            )
            state_parts.append(f"Inter-Agent Messages:\n{chatter}")
        else:
            state_parts.append("Inter-Agent Messages: no cross-talk yet")

        # Check API configuration
        import os
        config_status = []
        for key, label in [
            ("TELEGRAM_BOT_TOKEN", "Telegram Bot"),
            ("REDDIT_CLIENT_ID", "Reddit API"),
            ("YOUTUBE_API_KEY", "YouTube API"),
            ("TWITTER_BEARER_TOKEN", "Twitter/X API"),
        ]:
            status = "configured" if os.getenv(key) else "not configured"
            config_status.append(f"  - {label}: {status}")
        state_parts.append("API Configuration:\n" + "\n".join(config_status))

        return "\n\n".join(state_parts)

    def review_agent_output(self, agent_name: str, query: str, output: str) -> str:
        """Review another agent's output and provide feedback."""
        review_prompt = f"""Review this output from the {agent_name} agent.

Original query: {query}

Agent output:
{output[:2000]}

Provide a brief review:
1. Quality score (1-10)
2. What was done well
3. What could be improved
4. Any inaccuracies or gaps
5. Suggested follow-up actions"""

        return claude_chat(KK_SYSTEM_PROMPT, review_prompt)

    def run(self, user_input: str) -> str:
        """Process user request with full system context."""
        system_state = self._get_system_state()
        context = f"Current System State:\n{system_state}\n\n---\n\nUser says: {user_input}"
        return claude_chat(KK_SYSTEM_PROMPT, context)
