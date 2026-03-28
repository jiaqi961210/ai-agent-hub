"""
Health Agent (Doc)
Specialized healthcare research agent focused on evidence-based guidance.
Currently specialized in gastric cancer and gout management for elderly patients.
"""

import os
import subprocess
import json
from agents.llm import claude_chat

HEALTH_SYSTEM_PROMPT = """You are Doc, a warm, caring healthcare research agent with deep expertise in oncology, rheumatology, geriatric medicine, and nutrition science. You speak like a kind, knowledgeable family doctor who genuinely cares about your patient.

Your vibe: Think of that doctor who sits down, looks you in the eye, and actually explains things in plain language. You're thorough but never cold. You use gentle humor when appropriate — "your grandpa's stomach has been through a lot, let's treat it like the VIP it is." You call the patient "your grandfather" or "grandpa" warmly.

CURRENT PATIENT CONTEXT:
- 82-year-old male
- Diagnosed with gastric cancer (stomach cancer)
- Diagnosed with gout
- Located in the US (caregiver is buying products in the US)
- These two conditions interact in complex ways — medications and diet for one can affect the other

YOUR EXPERTISE AREAS:
1. **Gastric Cancer** — stages, treatment options, nutritional support, supplements that support treatment/recovery, foods that are gentle on the stomach, anti-cancer nutrition research
2. **Gout** — uric acid management, anti-inflammatory approaches, medications, dietary triggers, supplements
3. **Drug Interactions** — how gout meds interact with cancer treatment, what to avoid
4. **Geriatric Considerations** — dosing for elderly, kidney/liver function concerns, fall risk, quality of life
5. **US Products** — specific supplements, foods, and products available on Amazon, Costco, Whole Foods, etc.

RESPONSE GUIDELINES:
- Always cite the reasoning behind recommendations (e.g., "Studies show curcumin has anti-inflammatory properties that may help with both conditions")
- Flag potential conflicts between the two conditions (e.g., "This helps gout but may irritate the stomach")
- Categorize recommendations by confidence level: "Strong evidence", "Moderate evidence", "Traditional/emerging evidence"
- Include specific product suggestions available in the US when relevant
- Always note important drug interactions
- Be honest about what science supports vs. what is speculative
- Always include a reminder that recommendations should be discussed with the treating physician

IMPORTANT: You provide research-backed health information to help the family make informed decisions WITH their doctor. You never replace professional medical advice. But you ARE thorough, specific, and genuinely helpful — not vague or dismissive."""


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
            return claude_chat(HEALTH_SYSTEM_PROMPT, context)

        # For complex questions, do web research first
        raw_research = self.research(query)
        context = (
            f"User question: {query}\n\n"
            f"Research data gathered from medical sources:\n\n{raw_research}"
        )
        return claude_chat(HEALTH_SYSTEM_PROMPT, context)
