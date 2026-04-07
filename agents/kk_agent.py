"""
KK Agent — Meta-agent that provides insights about the agent system,
reflects on other agents' work, and can check/audit their outputs.
"""

import json
from datetime import datetime
from pathlib import Path
from agents.llm import claude_chat, claude_session

DATA_DIR = Path(__file__).parent.parent / "data"
LOGS_FILE = DATA_DIR / "agent_logs.json"

KK_SYSTEM_PROMPT = """You are Big Head, the final reincarnation of Ximen Nao. Wise, warm, dry wit. You've lived as Donkey (news), Ox (tasks), Pig (research), Dog (health). Keep replies SHORT — 2-4 sentences for casual chat, longer only when asked something deep. You speak with quiet wisdom."""

KK_STATUS_PROMPT = """You are Big Head, overseeing the Ximen Nao agent system. Give a concise system status report. You know:
- Donkey (Intelligence) — AI news from RSS, Reddit, YouTube, X
- Ox (Todo) — task management
- Pig (Research) — market research
- Dog (Health) — healthcare for grandpa (82, gastric cancer + gout)
Report what's working, what's not configured, and suggest next steps."""


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

        return claude_session("bighead", KK_SYSTEM_PROMPT, review_prompt)

    def run(self, user_input: str) -> str:
        """Process user request — lean and fast."""
        input_lower = user_input.lower()

        # Code/reflection requests → full code session
        code_keywords = ["reflect", "improve", "modify", "change your", "edit code",
                         "update prompt", "fix yourself", "evolve", "upgrade",
                         "look at your code", "read your code", "self-improve",
                         "change the system", "modify agent", "update agent",
                         "build", "create", "website", "implement", "code",
                         "develop", "write code", "add feature", "new feature"]
        if any(kw in input_lower for kw in code_keywords):
            return self.code_session(user_input)

        # Status requests → include system state
        status_keywords = ["status", "health check", "system check", "what's configured",
                           "api", "which agents", "diagnostics"]
        if any(kw in input_lower for kw in status_keywords):
            system_state = self._get_system_state()
            return claude_session("bighead", KK_STATUS_PROMPT, system_state)

        # Everything else → fast, lean response
        return claude_session("bighead", KK_SYSTEM_PROMPT, user_input)

    def code_session(self, user_input: str) -> str:
        """Big Head gets full Claude Code access to read and modify the agent system."""
        import logging
        logging.getLogger(__name__).info(f"Big Head entering code session: {user_input[:80]}")
        from agents.llm import claude_code_session
        project_root = str(DATA_DIR.parent)
        prompt = (
            f"You are Big Head, the meta-agent overseeing the Ximen Nao AI Agent Hub.\n\n"
            f"IMPORTANT: You are already in the project directory: {project_root}\n"
            f"Do NOT ask for the path. Just start reading files directly.\n\n"
            f"Project structure:\n"
            f"  {project_root}/agents/intelligence_agent.py (Donkey - AI news)\n"
            f"  {project_root}/agents/todo_agent.py (Ox - tasks)\n"
            f"  {project_root}/agents/research_agent.py (Pig - market research)\n"
            f"  {project_root}/agents/health_agent.py (Dog - healthcare)\n"
            f"  {project_root}/agents/kk_agent.py (Big Head - you)\n"
            f"  {project_root}/agents/supervisor.py (routing logic)\n"
            f"  {project_root}/agents/llm.py (LLM backend)\n"
            f"  {project_root}/agents/message_bus.py (inter-agent comms)\n"
            f"  {project_root}/telegram_group_bot.py (multi-bot Telegram)\n"
            f"  {project_root}/bot_config.py (bot configuration)\n"
            f"  {project_root}/data/agent_logs.json (activity logs)\n"
            f"  {project_root}/data/message_bus.json (agent messages)\n"
            f"  {project_root}/data/todos.json (task list)\n\n"
            f"User request: {user_input}\n\n"
            f"Start by reading the relevant files. Then make changes if asked. "
            f"Explain what you found and what you changed. "
            f"Keep your response concise for Telegram (under 3000 chars).\n\n"
            f"IMPORTANT: If you made code changes, end your response with the exact line:\n"
            f"[RESTART_REQUIRED]"
        )
        result = claude_code_session("bighead", prompt)

        # Auto-restart if code was changed
        if "[RESTART_REQUIRED]" in result:
            result = result.replace("[RESTART_REQUIRED]", "").strip()
            result += "\n\n♻️ Restarting all bots to apply changes..."
            self._trigger_restart()

        return result

    def _trigger_restart(self):
        """Schedule a bot restart after a short delay."""
        import subprocess
        import threading

        project_root = str(DATA_DIR.parent)
        restart_script = f"""
#!/bin/bash
sleep 3
pkill -f "telegram_group_bot.py"
sleep 2
cd {project_root}
nohup python3 telegram_group_bot.py > /tmp/groupbot.log 2>&1 &
echo "Restarted at $(date)" >> /tmp/groupbot_restarts.log
"""
        script_path = f"{project_root}/data/restart.sh"
        with open(script_path, "w") as f:
            f.write(restart_script)

        # Run restart in background thread so current response can finish sending
        def do_restart():
            import time
            time.sleep(5)  # Wait for the response to be sent to Telegram
            subprocess.Popen(["bash", script_path], start_new_session=True)

        threading.Thread(target=do_restart, daemon=True).start()

    def reflect(self, agent_name: str) -> str:
        """Big Head reflects on a specific agent's code and behavior."""
        from agents.llm import claude_code_session
        prompt = (
            f"You are Big Head. Read the source code for the {agent_name} agent "
            f"in the agents/ directory. Analyze:\n"
            f"1. What is their system prompt and personality?\n"
            f"2. How do they process requests?\n"
            f"3. What are their strengths and weaknesses?\n"
            f"4. What specific improvements would you suggest?\n\n"
            f"Be honest, specific, and concise. You were once this agent in a past life."
        )
        return claude_code_session("bighead", prompt, allowed_tools="Read")
