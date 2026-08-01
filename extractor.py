"""
extractor.py — Person 1 ("The Brain")

Owns: transcript -> structured ActionItems -> tool routing decisions
Deliverable: process_transcript(text) -> List[ActionItem]

Do not edit: jira_notion.py, gmail_slack.py, orchestrator.py, dashboard.py
"""

import os
import json
from typing import List

from dotenv import load_dotenv
from schemas import ActionItem

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Known team roster for ambiguity detection — expand this as needed
TEAM_ROSTER = ["Sarah_Design", "Sarah_Sales", "Alex_Marketing", "Alex_Eng", "Ravi"]

MEMORY_FILE = "memory.json"

EXTRACTION_SYSTEM_PROMPT = """
You are an assistant that extracts action items from a meeting transcript.

Return ONLY a JSON array of objects, no markdown fences, no commentary. Each object
must have exactly these fields:

{
  "task": string,
  "owner": string,
  "tool_type": "jira" | "email" | "notion",
  "confidence": float between 0 and 1,
  "raw_context": string (the original sentence(s)),
  "due_hint": string or null
}

Rules:
- tool_type = "jira" for concrete assignable tasks
- tool_type = "email" for follow-ups, recaps, or messages to send to someone
- tool_type = "notion" for decisions or reference info that should be documented
- confidence should reflect how clearly the task and owner are specified
- If the owner name is ambiguous or unclear from context, still extract it as written
  and lower the confidence score accordingly
"""


def _call_gemini(transcript: str) -> str:
    """Calls the Gemini API and returns the raw text response."""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"{EXTRACTION_SYSTEM_PROMPT}\n\nTranscript:\n{transcript}"
    )
    return response.text


def _load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}


def _apply_ambiguity_rules(items: List[dict]) -> List[ActionItem]:
    """Sets ambiguous=True when confidence is low or owner name is not uniquely
    resolvable against the team roster, unless memory resolves it."""
    memory = _load_memory()
    resolved: List[ActionItem] = []

    for item in items:
        owner = item.get("owner", "")
        matches = [name for name in TEAM_ROSTER if owner.lower() in name.lower()]

        ambiguous = item.get("confidence", 1.0) < 0.7 or len(matches) > 1

        # Memory can auto-resolve what would otherwise be ambiguous
        if ambiguous and owner in memory:
            ambiguous = False

        item["ambiguous"] = ambiguous
        resolved.append(item)  # type: ignore

    return resolved


def process_transcript(text: str) -> List[ActionItem]:
    """
    MAIN DELIVERABLE — everyone else on the team imports and calls this function.

    Takes raw transcript text, returns a list of ActionItem dicts matching schemas.py.
    """
    try:
        raw_response = _call_gemini(text)
        items = json.loads(raw_response)
    except Exception as e:
        print(f"[extractor] WARNING: extraction failed ({e}), returning empty list")
        return []

    return _apply_ambiguity_rules(items)


if __name__ == "__main__":
    with open("sample_transcript.txt", "r") as f:
        sample = f.read()

    result = process_transcript(sample)
    print(json.dumps(result, indent=2))
