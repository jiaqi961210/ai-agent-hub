"""
Market Research Agent
Researches product/business ideas using Google Search, GitHub, Product Hunt,
and web scraping — then synthesizes findings with Claude.
No API keys needed — uses web search via the claude CLI.
"""

import os
import subprocess
import json
from agents.llm import claude_chat, claude_session

RESEARCH_SYSTEM_PROMPT = """You are Pig — third reincarnation of Ximen Nao. Cunning, sharp, sees through hype. Produce a structured market research report: Market Overview, Competitors, Open Source, Target Customer, Opportunity Assessment, Next Steps. Be honest and concise."""


class ResearchAgent:
    def __init__(self):
        pass

    def _search(self, query: str) -> str:
        """Run a single focused web search via the claude CLI."""
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        result = subprocess.run(
            [
                "claude", "-p", query,
                "--output-format", "json",
                "--model", "sonnet",
                "--no-session-persistence",
                "--allowedTools", "WebSearch", "WebFetch",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd="/tmp",
        )

        if result.returncode != 0:
            return f"Search error: {result.stderr.strip()[:200]}"

        try:
            data = json.loads(result.stdout)
            return data.get("result", "")
        except json.JSONDecodeError:
            return result.stdout[:3000]

    def search_web(self, query: str) -> str:
        """Run multiple focused searches in parallel-ish to gather broad data."""
        searches = [
            f"Search the web for: top competitors and existing products for '{query}'. List product names, what they do, and pricing.",
            f"Search the web for: market size, growth data, and industry reports about '{query}'.",
            f"Search GitHub for: open source projects related to '{query}'. List repo names, stars, and descriptions.",
        ]

        results = []
        for i, search_query in enumerate(searches, 1):
            print(f"    Search {i}/{len(searches)}...")
            try:
                result = self._search(search_query)
                results.append(result)
            except subprocess.TimeoutExpired:
                print(f"    Search {i} timed out, skipping...")
                results.append(f"(Search {i} timed out)")

        return "\n\n---\n\n".join(results)

    def run(self, query: str) -> str:
        """Research a product/business idea and return a structured report."""
        print("  Gathering market intelligence...")
        raw_data = self.search_web(query)

        print("  Analyzing findings...")
        analysis_input = (
            f"Research query: {query}\n\n"
            f"Raw research data gathered from web sources:\n\n{raw_data}"
        )

        return claude_session("pig", RESEARCH_SYSTEM_PROMPT, analysis_input)
