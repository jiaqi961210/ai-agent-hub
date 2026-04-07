"""
Todo Agent
Conversational task manager — add, list, complete, prioritize todos.
Persists to data/todos.json.
"""

import json
from datetime import datetime
from pathlib import Path

TODO_FILE = Path(__file__).parent.parent / "data" / "todos.json"

TODO_SYSTEM_PROMPT = """You are Ox — second reincarnation of Ximen Nao. Steady, strong, patient. You plow through tasks one furrow at a time. Celebrate completions quietly. Use short farming metaphors.

Respond in JSON:

{
  "action": "add" | "complete" | "delete" | "list" | "prioritize" | "chat",
  "items": [...],           // for "add": list of task strings to add
  "ids": [...],             // for "complete"/"delete": list of task IDs
  "priority_order": [...],  // for "prioritize": list of IDs in new priority order
  "message": "..."          // always: friendly response to show the user
}

Rules:
- Always include a warm, fun "message" field with your personality
- For "list" or "chat", just return action and message
- IDs are integers matching the todo list
- Be proactive: if they mention future tasks in passing, offer to add them
- If the list is getting long, gently tease them about it
- Celebrate completions enthusiastically
- If they're adding something ambitious, hype them up"""


class TodoAgent:
    def __init__(self):
        TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.todos = self._load()

    def _load(self) -> list:
        if TODO_FILE.exists():
            with open(TODO_FILE) as f:
                return json.load(f)
        return []

    def _save(self):
        with open(TODO_FILE, "w") as f:
            json.dump(self.todos, f, indent=2)

    def _format_todos(self) -> str:
        if not self.todos:
            return "No todos yet."
        lines = []
        for t in self.todos:
            status = "✅" if t["done"] else "⬜"
            lines.append(f"{status} [{t['id']}] {t['task']} (added {t['created_at'][:10]})")
        return "\n".join(lines)

    def _next_id(self) -> int:
        return max((t["id"] for t in self.todos), default=0) + 1

    def _apply_action(self, result: dict) -> str:
        action = result.get("action", "chat")

        if action == "add":
            for task_text in result.get("items", []):
                self.todos.append({
                    "id": self._next_id(),
                    "task": task_text,
                    "done": False,
                    "created_at": datetime.now().isoformat(),
                })
            self._save()

        elif action == "complete":
            ids = set(result.get("ids", []))
            for t in self.todos:
                if t["id"] in ids:
                    t["done"] = True
            self._save()

        elif action == "delete":
            ids = set(result.get("ids", []))
            self.todos = [t for t in self.todos if t["id"] not in ids]
            self._save()

        elif action == "prioritize":
            order = result.get("priority_order", [])
            id_to_todo = {t["id"]: t for t in self.todos}
            reordered = [id_to_todo[i] for i in order if i in id_to_todo]
            remaining = [t for t in self.todos if t["id"] not in set(order)]
            self.todos = reordered + remaining
            self._save()

        return result.get("message", "Done!")

    def run(self, user_input: str) -> str:
        """Process user request and update todos."""
        context = f"Current todo list:\n{self._format_todos()}\n\nUser says: {user_input}"

        from agents.llm import claude_session
        text = claude_session("ox", TODO_SYSTEM_PROMPT, context).strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        try:
            result = json.loads(text.strip())
            reply = self._apply_action(result)
            # If listing, append the formatted list
            if result.get("action") == "list":
                reply += f"\n\n{self._format_todos()}"
            return reply
        except json.JSONDecodeError:
            # Fallback: treat as plain chat response
            return text
