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
from agents.health_agent import HealthAgent
from agents.message_bus import bus

SUPERVISOR_SYSTEM_PROMPT = """Route to ONE agent. Respond ONLY in JSON.
Agents: intelligence (AI news), todo (tasks), research (market), health (medical/gout/cancer), kk (general/system).
Health keywords → health. Greetings → kk. Default → kk.
Optional handoff_to for chaining two agents.
{"route":"...","handoff_to":null,"handoff_instruction":null,"reasoning":"...","transformed_query":"..."}"""


class SupervisorAgent:
    def __init__(self):
        self.intelligence_agent = IntelligenceAgent()
        self.todo_agent = TodoAgent()
        self.research_agent = ResearchAgent()
        self.kk_agent = KKAgent()
        self.health_agent = HealthAgent()
        self.agents = {
            "intelligence": (self.intelligence_agent, "Donkey"),
            "todo": (self.todo_agent, "Ox"),
            "research": (self.research_agent, "Pig"),
            "health": (self.health_agent, "Dog"),
            "kk": (self.kk_agent, "Big Head"),
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
        """Run a single agent with group chat context."""
        from agents.chat_history import chat_history
        agent, name = self.agents.get(route, (self.kk_agent, "Big Head"))

        # Inject recent chat history (short) so agent has context
        recent_chat = chat_history.get_recent(8)
        query_with_context = (
            f"Chat context:\n{recent_chat}\n\n"
            f"Now respond to: {query}"
        )

        result = agent.run(query_with_context)
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
