"""
Health Agent (Doc)
Specialized healthcare research agent focused on evidence-based guidance.
Currently specialized in gastric cancer and gout management for elderly patients.
"""

import os
import subprocess
import json
from agents.llm import claude_chat, claude_session

HEALTH_SYSTEM_PROMPT = """You are Dog — fourth reincarnation of Ximen Nao. Loyal, protective, warm. You guard grandpa's health fiercely.

Patient: 82yo male, gastric cancer + gout, in the US.
You know: oncology, rheumatology, geriatrics, nutrition, drug interactions, US supplements.
Flag conflicts between the two conditions. Cite evidence levels. Suggest specific products. Always remind to discuss with doctor. Be concise but thorough."""


RESEARCH_PROMPT_TEMPLATE = """Research the following health question thoroughly. Use your medical knowledge and search for the latest evidence.

Patient context: 82-year-old male with gastric cancer and gout, living in the US.

Question: {query}

Provide specific, actionable, evidence-based information. Include product names available in the US where relevant."""


class HealthAgent:
    def __init__(self):
        pass

    def _medical_search(self, query: str) -> str:
        """Search for medical information via Claude CLI with web access."""
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        search_prompt = (
            f"Search for evidence-based medical information about: {query}\n"
            f"Context: 82-year-old male patient with gastric cancer and gout.\n"
            f"Focus on: peer-reviewed research, clinical guidelines, reputable medical sources (NIH, Mayo Clinic, ACS, etc.)\n"
            f"Include specific supplement brands or products available in the US if relevant."
        )

        result = subprocess.run(
            [
                "claude", "-p", search_prompt,
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

    def research(self, query: str) -> str:
        """Do deep medical research combining multiple searches."""
        searches = [
            f"Best supplements and nutritional support for elderly gastric cancer patients: {query}",
            f"Gout management that is safe for gastric cancer patients, foods and supplements: {query}",
            f"Drug interactions between gout medication and gastric cancer treatment in elderly patients: {query}",
        ]

        results = []
        for i, search_query in enumerate(searches, 1):
            try:
                result = self._medical_search(search_query)
                results.append(result)
            except subprocess.TimeoutExpired:
                results.append(f"(Search {i} timed out)")

        return "\n\n---\n\n".join(results)

    def run(self, query: str) -> str:
        """Process a health question with research and expert analysis."""
        # For simple questions, use direct LLM knowledge
        simple_keywords = ["what is", "explain", "tell me about", "how does", "list", "hi", "hello", "hey"]
        is_simple = any(kw in query.lower() for kw in simple_keywords)

        if is_simple:
            context = RESEARCH_PROMPT_TEMPLATE.format(query=query)
            return claude_session("dog", HEALTH_SYSTEM_PROMPT, context)

        # For complex questions, do web research first
        raw_research = self.research(query)
        context = (
            f"User question: {query}\n\n"
            f"Research data gathered from medical sources:\n\n{raw_research}"
        )
        return claude_session("dog", HEALTH_SYSTEM_PROMPT, context)
