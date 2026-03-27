"""
Supervisor Agent
Routes user input to the appropriate sub-agent, supports inter-agent
communication and multi-step handoffs.
"""

import json
from agents.llm import claude_chat
from agents.intelligence_agent import IntelligenceAgent
from agents.todo_agent import TodoAgent
from agents.research_agent import ResearchAgent
from agents.kk_agent import KKAgent
from agents.message_bus import bus

SUPERVISOR_SYSTEM_PROMPT = """You are the silent router. You do NOT respond to the user directly. Your only job is to read the user's message and decide which agent(s) should handle it.

The agents:
1. **intelligence** (Nova) — AI news, tech updates, what's happening in AI, latest papers/releases
2. **todo** (Chip) — task management, to-do lists, adding/completing/listing tasks, reminders
3. **research** (Max) — business ideas, market analysis, competitor research, product validation
4. **kk** (KK) — system questions, agent reviews, "how does this work", health checks, general conversation, greetings, or anything that doesn't clearly fit the other three

Routing rules:
- Usually ONE agent handles the message
- But if the request naturally spans multiple agents, you can chain them with "handoff"
  Examples of chaining:
  - "get AI news and add the top story to my todo" → intelligence first, then handoff to todo
  - "research X and tell me what KK thinks" → research first, then handoff to kk
  - "what's new in AI and is there a business opportunity" → intelligence first, then handoff to research
- Greetings like "hi", "hello", "hey" go to "kk"
- When in doubt, route to "kk"

Respond ONLY in JSON:
{
  "route": "intelligence" | "todo" | "research" | "kk",
  "handoff_to": null | "intelligence" | "todo" | "research" | "kk",
  "handoff_instruction": null | "what to do with the first agent's output",
  "reasoning": "brief explanation",
  "transformed_query": "cleaned up version of user's request for the agent"
}
"""


class SupervisorAgent:
    def __init__(self):
        self.intelligence_agent = IntelligenceAgent()
        self.todo_agent = TodoAgent()
        self.research_agent = ResearchAgent()
        self.kk_agent = KKAgent()
        self.agents = {
            "intelligence": (self.intelligence_agent, "Nova"),
            "todo": (self.todo_agent, "Chip"),
            "research": (self.research_agent, "Max"),
            "kk": (self.kk_agent, "KK"),
        }

    def route(self, user_input: str) -> dict:
        """Ask Claude to decide which agent handles this request."""
        text = claude_chat(SUPERVISOR_SYSTEM_PROMPT, user_input)
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    def _run_agent(self, route: str, query: str) -> str:
        """Run a single agent and return its result."""
        agent, name = self.agents.get(route, (self.kk_agent, "KK"))
        result = agent.run(query)
        self.kk_agent.log_agent_activity(name, query, result)
        return result

    def run(self, user_input: str) -> str:
        """Main entry point — routes, runs, and handles handoffs."""
        try:
            routing = self.route(user_input)
        except Exception:
            routing = {"route": "kk", "transformed_query": user_input}

        route = routing.get("route", "kk")
        query = routing.get("transformed_query", user_input)
        handoff_to = routing.get("handoff_to")
        handoff_instruction = routing.get("handoff_instruction")

        # Step 1: Run the primary agent
        first_result = self._run_agent(route, query)
        first_name = self.agents.get(route, (None, "KK"))[1]

        # Step 2: If there's a handoff, pass the result to the next agent
        if handoff_to and handoff_to in self.agents:
            second_name = self.agents[handoff_to][1]

            # Log the handoff on the message bus
            bus.send(first_name, second_name, first_result, msg_type="handoff")

            # Build context for the second agent
            handoff_query = (
                f"{handoff_instruction or 'Continue based on this'}\n\n"
                f"--- Output from {first_name} ---\n{first_result}"
            )
            second_result = self._run_agent(handoff_to, handoff_query)

            # Combine both responses
            return (
                f"[{first_name}]\n{first_result}\n\n"
                f"---\n\n"
                f"[{second_name}]\n{second_result}"
            )

        return first_result
