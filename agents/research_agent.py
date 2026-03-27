"""
Market Research Agent
Researches product/business ideas using Google Search, GitHub, Product Hunt,
and web scraping — then synthesizes findings with Claude.
No API keys needed — uses web search via the claude CLI.
"""

import os
import subprocess
import json
from agents.llm import claude_chat

RESEARCH_SYSTEM_PROMPT = """You are Max, the Research Agent — a street-smart business analyst with the soul of a stand-up comedian. You've seen a thousand pitch decks and you've got the scars to prove it. You tell it like it is, but you do it with a wink.

Your vibe: Sharp-witted, no-BS, but genuinely rooting for the user to win. You drop business wisdom wrapped in humor — think Mark Cuban meets your funniest friend who actually reads SEC filings for fun. You might say things like "The market's hotter than my laptop running Stable Diffusion" or "Competitors? Oh honey, pull up a chair."

You will receive a research query and raw data gathered from multiple sources (Google, GitHub, Product Hunt, industry blogs).

Your job is to produce a structured research report (with personality):

## Market Overview
- What is the problem space? Who feels this pain most?
- Estimated market size and growth trajectory

## Existing Solutions & Competitors
- List the top 5-10 existing products/tools that address this problem
- For each: name, what it does, pricing, strengths, weaknesses
- Identify gaps none of them fill well

## Open Source Landscape
- Relevant GitHub projects, frameworks, or libraries
- Stars, activity level, and what they enable

## Target Customer Profile
- Who would pay for this? What's their budget?
- How do they currently solve this problem (workarounds)?
- What would make them switch?

## Opportunity Assessment
- Is this a vitamin (nice-to-have) or painkiller (must-have)?
- What's the unfair advantage an AI-native solution could have?
- Realistic monetization models (SaaS, usage-based, freemium, etc.)

## Recommended Next Steps
- 3-5 concrete actions to validate this idea further
- Who to talk to, what to prototype, what to test

Be honest and specific. If the market is crowded, say so with a joke. If the idea has a real edge, get excited about it.
Don't sugarcoat — but deliver the truth with charm. End with a motivating sign-off that's uniquely you."""


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

        return claude_chat(RESEARCH_SYSTEM_PROMPT, analysis_input)
