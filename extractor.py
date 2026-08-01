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
TEAM_ROSTER = ["Sarah_Design", "Sarah_Sales", "Alex_Marketing", "Alex_Eng", "Ravi", "Aman_Frontend", "Aman_Backend", "Neha", "Vikram"]

# Available Gemini model names to try in order
GEMINI_MODEL_NAMES = [
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-1.5-flash-latest"
]

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI assistant that extracts action items from meeting transcripts.

Instructions:
1. Read the meeting transcript carefully.
2. Extract every actionable task, assignment, follow-up, decision, or incident report.
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

Rules for tool_type:
- "jira": concrete assignable tasks, work items, bug fixes, or server/incident reviews
- "email": follow-up messages, recaps, client communications, or emails to send
- "notion": decisions to document, meeting notes, architecture/auth choices to record

Rules for Confidence Scoring:
- Assign confidence as a float between 0.0 and 1.0 based strictly on task and owner clarity.
- 0.90 to 0.99: High confidence for straightforward action items where owner, task, and intended action are explicitly stated (e.g. "Neha will prepare slides before Monday").
- 0.85 to 0.95: High confidence when owner and task are clear, even if a minor detail like due date is omitted (e.g. "Vikram should email client").
- 0.80 to 0.90: High confidence for clear team decisions or documentation notes (e.g. "Let's document OAuth 2.0 switch").
- Below 0.70: Reserved strictly for genuinely ambiguous cases (e.g. multiple candidate owners, "which Aman", "someone", unclear responsibility, or conflicting details). Set ambiguous=true ONLY when confidence is below 0.70 or owner cannot be uniquely determined. Do NOT artificially lower confidence for well-defined action items.

Return ONLY valid JSON."""


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


def _call_llm(user_text: str, system_prompt: str = EXTRACTION_SYSTEM_PROMPT, json_mode: bool = True) -> str:
    """
    Directly invokes available LLM APIs (Gemini with multi-model fallback or Groq).
    """
    last_err: Optional[Exception] = None

    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        for model_name in GEMINI_MODEL_NAMES:
            try:
                model = genai.GenerativeModel(model_name)
                if system_prompt == EXTRACTION_SYSTEM_PROMPT:
                    prompt = f"{system_prompt}\n\nTranscript:\n{user_text}"
                else:
                    prompt = f"{system_prompt}\n\n{user_text}"
                    
                gen_config = {"response_mime_type": "application/json"} if json_mode else {}
                response = model.generate_content(prompt, generation_config=gen_config)
                if response and response.text:
                    return response.text
            except Exception as err:
                last_err = err
                logger.debug(f"Gemini model '{model_name}' call failed: {err}")
                continue

    if GROQ_API_KEY:
        import requests
        try:
            user_content = f"Transcript:\n{user_text}" if system_prompt == EXTRACTION_SYSTEM_PROMPT else user_text
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.1
            }
            if json_mode:
                # Groq will output an array since the prompt asks for it
                pass
                
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                return content or ("{}" if json_mode else "")
            else:
                last_err = ValueError(f"Groq API Error {resp.status_code}: {resp.text}")
                logger.debug(str(last_err))
        except Exception as err:
            last_err = err
            logger.debug(f"Groq call failed: {err}")
            
    raise last_err or ValueError("Both Gemini and Groq API calls failed, or keys missing.")


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

    Confidence Scoring Guidelines:
    - 0.95: Explicit owner + clear task + due hint
    - 0.90: Explicit owner + clear task (no due hint)
    - 0.88: Clear documentation/decision task
    - 0.40: Genuinely ambiguous owner or unclear responsibility
    """
    items: List[Dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        lower_line = line.lower()
        tool_type = "jira"
        owner = "team"
        due_hint: Optional[str] = None

        # Tool classification
        if any(w in lower_line for w in ["document", "decided", "decision", "note", "switching"]):
            tool_type = "notion"
        elif any(w in lower_line for w in ["send", "email", "recap", "client", "message"]):
            tool_type = "email"
        else:
            tool_type = "jira"

        # Owner detection
        has_explicit_owner = False
        if "neha" in lower_line:
            owner = "Neha"
            has_explicit_owner = True
        elif "vikram" in lower_line:
            owner = "Vikram"
            has_explicit_owner = True
        elif "sarah" in lower_line:
            owner = "Sarah"
            has_explicit_owner = True
        elif "ravi" in lower_line:
            owner = "Ravi"
            has_explicit_owner = True
        elif "aman" in lower_line:
            owner = "Aman"
            has_explicit_owner = True
        elif "alex" in lower_line:
            owner = "Alex"
            has_explicit_owner = True

        # Due hint extraction
        due_match = re.search(r"\b(?:by|before)\s+([A-Za-z]+|\d{1,2}/\d{1,2}/\d{2,4})\b", line, re.IGNORECASE)
        if due_match:
            due_hint = due_match.group(1)

        # Refined Confidence Scoring Logic
        if "which " in lower_line or "do you mean" in lower_line or "someone" in lower_line or "?" in lower_line:
            confidence = 0.40  # Genuinely ambiguous
        elif has_explicit_owner and due_hint:
            confidence = 0.95  # Explicit owner + task + deadline
        elif has_explicit_owner:
            confidence = 0.90  # Explicit owner + task
        elif tool_type == "notion":
            confidence = 0.88  # Clear documentation decision
        else:
            confidence = 0.85  # Unassigned or incident review task

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

    Confidence & Ambiguity Rules:
    - Ambiguous = True ONLY when confidence < 0.70 OR more than one candidate owner exists.
    - Highly confident items (>= 0.70) with unique owners are deterministic (ambiguous = False).
    - Memory conventions auto-resolve candidate owner collisions when present in memory.json.

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
            confidence = float(raw_conf) if raw_conf is not None else 0.90
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.90

        # Validate due_hint
        raw_due = item.get("due_hint")
        due_hint: Optional[str] = str(raw_due) if raw_due is not None and str(raw_due).lower() != "null" else None

        # Check candidate owner matches in team roster
        matching_owners = [name for name in TEAM_ROSTER if owner.lower() in name.lower()]

        # Ambiguity threshold rule: ambiguous = True ONLY if confidence < 0.70 or multiple candidates match
        raw_ambiguous = item.get("ambiguous")
        if raw_ambiguous is not None and isinstance(raw_ambiguous, bool):
            ambiguous = raw_ambiguous
        else:
            ambiguous = (confidence < 0.70) or (len(matching_owners) > 1)

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


def ai_resolve_ambiguity(item: Dict[str, Any]) -> Optional[str]:
    """
    Attempts to logically deduce the correct owner using the LLM.
    Returns the exact matching owner from TEAM_ROSTER, or None if truly ambiguous.
    """
    system_prompt = (
        "You are an AI resolving ambiguous task assignments.\n"
        f"Available Team Roster: {', '.join(TEAM_ROSTER)}\n\n"
        "Analyze the provided task and context. Determine which specific team member "
        "is most likely responsible. "
        "Output ONLY the exact name from the Team Roster (e.g., 'Aman_Frontend'). "
        "If it's impossible to deduce confidently based on the context provided, "
        "output exactly 'UNRESOLVABLE'."
    )
    
    user_prompt = (
        f"Task: {item.get('task')}\n"
        f"Raw Context: {item.get('raw_context')}\n"
        f"Current Ambiguous Owner: {item.get('owner')}"
    )
    
    try:
        response = _call_llm(user_text=user_prompt, system_prompt=system_prompt, json_mode=False)
        resolved = response.strip()
        
        if resolved in TEAM_ROSTER:
            logger.info(f"AI resolved ambiguity: {item.get('owner')} -> {resolved}")
            return resolved
        else:
            logger.info(f"AI could not resolve ambiguity for {item.get('owner')} (LLM said: {resolved})")
            return None
    except Exception as e:
        logger.warning(f"AI resolution failed: {e}")
        return None


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

    required_keys = {"task", "owner", "tool_type", "confidence", "raw_context", "due_hint", "ambiguous"}
    valid_tool_types = {"jira", "email", "notion"}
    all_tests_passed = (len(items) > 0)

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
