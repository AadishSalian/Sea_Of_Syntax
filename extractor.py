"""
extractor.py — Person 1 ("The Brain")

Owns: transcript -> structured ActionItems -> tool routing decisions
Deliverable: process_transcript(text) -> List[ActionItem]

Responsible for ingesting raw transcript text, invoking LLMs (Google Gemini / Groq),
parsing and validating JSON structure against schemas.py, resolving ambiguous owners
via memory.json conventions, and outputting validated ActionItems.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from schemas import ActionItem

# Initialize environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="[extractor] %(levelname)s: %(message)s")
logger = logging.getLogger("extractor")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Constants
MEMORY_FILE = "memory.json"
TEAM_ROSTER = ["Sarah_Design", "Sarah_Sales", "Alex_Marketing", "Alex_Eng", "Ravi"]

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI assistant that extracts action items from meeting transcripts.

Instructions:
1. Read the meeting transcript carefully.
2. Extract every actionable task, assignment, follow-up, or decision.
3. Output ONLY a valid JSON array of objects. Do NOT include markdown formatting, code fences (such as ```json), explanations, or extra commentary.

For every task, produce an object containing ONLY these 7 fields:
{
  "task": string,
  "owner": string,
  "tool_type": "jira" | "email" | "notion",
  "confidence": float between 0.0 and 1.0,
  "raw_context": string,
  "due_hint": string or null,
  "ambiguous": boolean
}

Rules:
- tool_type must ONLY be one of:
  * "jira" (for concrete assignable tasks, work items, or features)
  * "email" (for follow-up messages, recaps, client communications, or outreach)
  * "notion" (for decisions to document, meeting notes, or reference information)
- confidence must be a float between 0.0 and 1.0 reflecting how clearly the task and owner are specified.
- If confidence < 0.7 or more than one possible owner exists, set ambiguous=true. Otherwise ambiguous=false.
- Return ONLY valid JSON."""


def _clean_json_string(raw_text: str) -> str:
    """
    Cleans raw text output from LLMs by stripping markdown code blocks, backticks, and whitespace.

    Args:
        raw_text: The raw string response from the LLM.

    Returns:
        A cleaned string suitable for json.loads parsing.
    """
    if not raw_text:
        return ""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    if text.endswith("```"):
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _load_memory() -> Dict[str, Any]:
    """
    Loads organizational memory and conventions from memory.json.

    Returns:
        A dictionary containing historical mappings or convention rules, or {} if unavailable.
    """
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logger.warning(f"Failed to read memory file '{MEMORY_FILE}': {err}")
            return {}
    return {}


def _call_llm(transcript_text: str) -> str:
    """
    Directly invokes available LLM APIs (Gemini or Groq fallback).

    Args:
        transcript_text: The raw transcript text to process.

    Returns:
        Raw string output from the LLM.
    """
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nTranscript:\n{transcript_text}"
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text
    elif GROQ_API_KEY:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Transcript:\n{transcript_text}"}
            ],
            temperature=0.1,
        )
        return completion.choices[0].message.content or "[]"
    else:
        raise ValueError("Neither GEMINI_API_KEY nor GROQ_API_KEY is configured in environment.")


def extract_action_items(text: str) -> List[Dict[str, Any]]:
    """
    Calls the LLM API to extract action items as a list of raw dictionaries.
    Includes automated single-retry recovery and JSON cleaning.

    Args:
        text: Meeting transcript string.

    Returns:
        A list of un-normalized action item dictionaries.

    Raises:
        ValueError: If API keys are missing or extraction fails after retries.
    """
    max_attempts = 2
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            raw_response = _call_llm(text)
            cleaned = _clean_json_string(raw_response)
            parsed = json.loads(cleaned)

            if isinstance(parsed, dict) and "action_items" in parsed:
                parsed = parsed["action_items"]

            if isinstance(parsed, list):
                return parsed
            else:
                raise ValueError(f"LLM output is not a JSON list (got {type(parsed).__name__})")

        except Exception as err:
            last_error = err
            logger.warning(f"LLM extraction attempt {attempt}/{max_attempts} failed: {err}")
            if attempt < max_attempts:
                continue

    raise last_error or ValueError("Extraction failed after retries.")


def _fallback_extract(text: str) -> List[Dict[str, Any]]:
    """
    Rule-based extractor fallback used when LLM API keys are missing or network calls fail.

    Args:
        text: Meeting transcript text.

    Returns:
        A list of extracted item dictionaries.
    """
    items: List[Dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        lower_line = line.lower()
        tool_type = "jira"
        owner = "team"
        due_hint: Optional[str] = None
        confidence = 0.9

        # Tool classification
        if any(w in lower_line for w in ["document", "decided", "decision", "note"]):
            tool_type = "notion"
        elif any(w in lower_line for w in ["send", "email", "recap", "client", "message"]):
            tool_type = "email"

        # Owner detection
        if "sarah" in lower_line:
            owner = "Sarah"
        elif "ravi" in lower_line:
            owner = "Ravi"
        elif "alex" in lower_line:
            owner = "Alex"

        # Ambiguity indicator
        if "which " in lower_line or "someone" in lower_line or "?" in lower_line:
            confidence = 0.4

        # Due hint extraction
        due_match = re.search(r"\bby\s+([A-Za-z]+|\d{1,2}/\d{1,2}/\d{2,4})\b", line, re.IGNORECASE)
        if due_match:
            due_hint = due_match.group(1)

        task = line.split(":", 1)[1].strip() if ":" in line else line

        items.append({
            "task": task,
            "owner": owner,
            "tool_type": tool_type,
            "confidence": confidence,
            "raw_context": line,
            "due_hint": due_hint,
        })

    return items


def _apply_ambiguity_rules(items: List[Dict[str, Any]]) -> List[ActionItem]:
    """
    Normalizes items and applies ambiguity detection & memory resolution rules.

    Guarantees that each returned dict adheres strictly to schemas.py (containing ONLY
    the 7 exact fields: task, owner, tool_type, confidence, raw_context, due_hint, ambiguous).

    Args:
        items: List of raw extracted action item dictionaries.

    Returns:
        List of typed ActionItem dictionaries matching schemas.py contract.
    """
    memory = _load_memory()
    resolved: List[ActionItem] = []
    valid_tool_types = {"jira", "email", "notion"}

    for item in items:
        if not isinstance(item, dict):
            continue

        # Safely extract and default required fields
        task = str(item.get("task", "")).strip()
        owner = str(item.get("owner", "unassigned")).strip()
        raw_context = str(item.get("raw_context", "")).strip()

        # Validate tool_type
        tool_type = item.get("tool_type", "jira")
        if tool_type not in valid_tool_types:
            tool_type = "jira"

        # Validate confidence score
        raw_conf = item.get("confidence")
        try:
            confidence = float(raw_conf) if raw_conf is not None else 1.0
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 1.0

        # Validate due_hint
        raw_due = item.get("due_hint")
        due_hint: Optional[str] = str(raw_due) if raw_due is not None and str(raw_due).lower() != "null" else None

        # Check candidate owner matches in team roster
        matching_owners = [name for name in TEAM_ROSTER if owner.lower() in name.lower()]

        # Determine ambiguity state (confidence < 0.7 or multiple candidates)
        raw_ambiguous = item.get("ambiguous")
        if raw_ambiguous is not None:
            ambiguous = bool(raw_ambiguous)
        else:
            ambiguous = (confidence < 0.7) or (len(matching_owners) > 1)

        # Memory convention resolution
        if ambiguous and memory:
            if owner in memory:
                ambiguous = False
            else:
                for convention_key, convention_val in memory.items():
                    if owner.lower() in convention_key.lower():
                        if isinstance(convention_val, dict):
                            jira_proj = convention_val.get("jira_project", "").lower()
                            if jira_proj and jira_proj in raw_context.lower():
                                ambiguous = False
                                break

        # Construct ActionItem matching schemas.py contract (no extra or missing fields)
        action_item: ActionItem = {
            "task": task,
            "owner": owner,
            "tool_type": tool_type,  # type: ignore
            "confidence": confidence,
            "raw_context": raw_context,
            "due_hint": due_hint,
            "ambiguous": ambiguous,
        }
        resolved.append(action_item)

    return resolved


def process_transcript(text: str) -> List[ActionItem]:
    """
    MAIN DELIVERABLE — Ingests transcript text, extracts action items, applies ambiguity
    rules, and returns a list of validated ActionItem dictionaries matching schemas.py.

    Args:
        text: Raw meeting transcript text.

    Returns:
        List of ActionItem dictionaries. Returns [] on complete processing failure.
    """
    if not text or not text.strip():
        logger.warning("Empty transcript text provided to process_transcript")
        return []

    items: List[Dict[str, Any]] = []

    try:
        items = extract_action_items(text)
    except Exception as err:
        logger.info(f"LLM extraction unavailable ({err}); using rule-based fallback")
        try:
            items = _fallback_extract(text)
        except Exception as fallback_err:
            logger.error(f"Fallback extraction failed: {fallback_err}")
            return []

    try:
        return _apply_ambiguity_rules(items)
    except Exception as rule_err:
        logger.error(f"Failed to apply ambiguity rules: {rule_err}")
        return []


def run_extractor_tests() -> bool:
    """
    Runs automated verification tests on extractor.py deliverables using sample_transcript.txt.

    Returns:
        True if all verification assertions pass, False otherwise.
    """
    print("=" * 65)
    print("           EXTRACTOR.PY VERIFICATION & TEST SUITE            ")
    print("=" * 65)

    sample_file = "sample_transcript.txt"
    if not os.path.exists(sample_file):
        print(f"[FAIL] Test transcript '{sample_file}' not found.")
        return False

    with open(sample_file, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    items = process_transcript(transcript_text)
    print(f"Extracted {len(items)} Action Items from {sample_file}:\n")

    # 1. Verify item count
    item_count_pass = (len(items) == 4)
    print(f"[{'PASS' if item_count_pass else 'FAIL'}] Action Item Count: {len(items)} (Expected: 4)")

    required_keys = {"task", "owner", "tool_type", "confidence", "raw_context", "due_hint", "ambiguous"}
    valid_tool_types = {"jira", "email", "notion"}
    all_tests_passed = item_count_pass

    for i, item in enumerate(items, 1):
        print(f"\n--- Action Item {i} ---")
        print(f"  task:        {item.get('task')!r}")
        print(f"  owner:       {item.get('owner')!r}")
        print(f"  tool_type:   {item.get('tool_type')!r}")
        print(f"  confidence:  {item.get('confidence')}")
        print(f"  due_hint:    {item.get('due_hint')!r}")
        print(f"  ambiguous:   {item.get('ambiguous')}")
        print(f"  raw_context: {item.get('raw_context')!r}")

        keys_set = set(item.keys())
        keys_valid = (keys_set == required_keys)
        tool_type_valid = item.get("tool_type") in valid_tool_types
        conf_val = item.get("confidence")
        conf_valid = isinstance(conf_val, (int, float)) and 0.0 <= float(conf_val) <= 1.0
        ambig_valid = isinstance(item.get("ambiguous"), bool)

        item_passed = keys_valid and tool_type_valid and conf_valid and ambig_valid
        if not item_passed:
            all_tests_passed = False

        print(f"  [Status]: {'PASS' if item_passed else 'FAIL'}")
        print(f"    - Schema Match (Exact 7 Keys): {'PASS' if keys_valid else 'FAIL'}")
        print(f"    - Valid Tool Type:              {'PASS' if tool_type_valid else 'FAIL'}")
        print(f"    - Valid Confidence Exists:      {'PASS' if conf_valid else 'FAIL'}")
        print(f"    - Valid Ambiguous Exists:       {'PASS' if ambig_valid else 'FAIL'}")

    print("\n" + "=" * 65)
    if all_tests_passed:
        print("RESULT: ALL EXTRACTOR VERIFICATION TESTS PASSED SUCCESSFULLY! [PASS]")
    else:
        print("RESULT: EXTRACTOR VERIFICATION TESTS FAILED! [FAIL]")
    print("=" * 65 + "\n")

    return all_tests_passed


if __name__ == "__main__":
    run_extractor_tests()
