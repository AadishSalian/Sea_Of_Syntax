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
from typing import List, Dict, Any, Optional, Tuple

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
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-8b",
]

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI assistant that extracts action items from meeting transcripts.

Instructions:
1. Read the meeting transcript carefully.
2. Extract ONLY genuine, actionable tasks, assignments, follow-ups, or decisions directed at someone.
3. Do NOT extract conversational filler, meeting greetings, introductory remarks, or adjournment announcements (e.g. "Good morning everyone", "Let's go through today's action items", "Meeting adjourned"). Skip filler lines completely.
4. Output ONLY a valid JSON array of objects. Do NOT include markdown formatting, code fences (such as ```json), explanations, or extra commentary.

For every task, produce an object containing ONLY these 7 fields:
{
  "task": string,
  "owner": string or null,
  "tool_type": "jira" | "email" | "notion",
  "confidence": float between 0.0 and 1.0,
  "raw_context": string,
  "due_hint": string or null,
  "ambiguous": boolean
}

Rules for owner:
- Set owner to the specific person's name if explicitly named (e.g. "Hardik", "Sarah", "Aadish").
- Set owner to null (not "team") when ambiguous=true or no specific person is named (e.g. "Someone should review...").
- Only set owner="team" for non-ambiguous team-wide commitments.

Rules for due_hint:
- due_hint must be the exact time phrase indicating deadline (e.g. "tomorrow", "Friday", "this evening", "end of day", "before Friday").
- Do NOT include tool names, arbitrary prepositions, or single words like "the" or "email".

Rules for tool_type:
- "jira": concrete assignable tasks, work items, bug fixes, or server/incident reviews
- "email": follow-up messages, recaps, client communications, or emails to send
- "notion": decisions to document, meeting notes, architecture/auth choices to record

Rules for Confidence & Ambiguity:
- Set ambiguous=true and confidence < 0.70 ONLY when the owner is unassigned ("Someone"), ambiguous, or unclear.
- High confidence (0.85-0.95) with ambiguous=false for explicit assignments.

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


def _call_llm(transcript_text: str) -> Tuple[str, str]:
    """
    Directly invokes available LLM APIs (Groq primary with llama-3.3-70b-versatile, Gemini secondary).

    Args:
        transcript_text: The raw transcript text to process.

    Returns:
        Tuple of (raw_json_string_response, extraction_method_name)
    """
    # Primary: Groq API with llama-3.3-70b-versatile
    if GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Transcript:\n{transcript_text}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = completion.choices[0].message.content or "[]"
            if content and content.strip():
                return content, "Groq (llama-3.3-70b-versatile)"
        except Exception as groq_err:
            logger.warning(f"Groq API call failed: {groq_err}. Trying Gemini fallback...")

    # Secondary: Gemini API fallback
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        last_err: Optional[Exception] = None
        for model_name in GEMINI_MODEL_NAMES:
            try:
                model = genai.GenerativeModel(model_name)
                prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nTranscript:\n{transcript_text}"
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                if response and response.text:
                    return response.text, f"Gemini ({model_name})"
            except Exception as err:
                last_err = err
                logger.debug(f"Gemini model '{model_name}' call failed: {err}")
                continue
                
        if last_err:
            logger.warning(f"Gemini API attempts failed: {last_err}")

    raise ValueError("Neither Groq nor Gemini LLM API calls succeeded.")


def extract_action_items(text: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Calls the LLM API to extract action items as a list of raw dictionaries.
    Includes automated single-retry recovery and JSON cleaning.

    Args:
        text: Meeting transcript string.

    Returns:
        Tuple of (list_of_unnormalized_action_item_dicts, extraction_method_name).

    Raises:
        ValueError: If API keys are missing or extraction fails after retries.
    """
    max_attempts = 2
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            raw_response, method_name = _call_llm(text)
            cleaned = _clean_json_string(raw_response)
            parsed = json.loads(cleaned)

            if isinstance(parsed, dict) and "action_items" in parsed:
                parsed = parsed["action_items"]

            if isinstance(parsed, list):
                return parsed, method_name
            elif isinstance(parsed, dict):
                for k, v in parsed.items():
                    if isinstance(v, list):
                        return v, method_name
                return [parsed], method_name
            else:
                raise ValueError(f"LLM output is not a JSON list/dict (got {type(parsed).__name__})")

        except Exception as err:
            last_error = err
            logger.warning(f"LLM extraction attempt {attempt}/{max_attempts} failed: {err}")
            if attempt < max_attempts:
                continue

    raise last_error or ValueError("Extraction failed after retries.")


def _is_filler_line(line: str) -> bool:
    """Detects conversational filler, greetings, and adjournment lines."""
    lower = line.lower().strip()
    if not lower:
        return True
    
    # Filler phrases to skip
    if any(p in lower for p in ["good morning", "good afternoon", "meeting adjourned", "action items"]):
        # Verify line does not contain an actual actionable task verb
        action_verbs = ["fix", "create", "document", "send", "review", "investigate", "update", "continue"]
        if not any(v in lower for v in action_verbs):
            return True
            
    return False


def _extract_time_phrase(line: str) -> Optional[str]:
    """Extracts clean time phrases for due_hint, avoiding tool names and arbitrary single words."""
    lower = line.lower()
    
    # Check multi-word time phrases first
    if "end of the day" in lower or "end of day" in lower:
        return "end of the day"
    if "this evening" in lower:
        return "this evening"
    if "before tomorrow" in lower or "tomorrow" in lower:
        return "tomorrow"
        
    # Check days of the week with prepositions
    day_prep_match = re.search(r"\b(?:by|before|on)\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", line, re.IGNORECASE)
    if day_prep_match:
        return day_prep_match.group(1)
        
    day_match = re.search(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", line, re.IGNORECASE)
    if day_match:
        return day_match.group(1)

    # Check date formats
    date_match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", line)
    if date_match:
        return date_match.group(1)

    return None


def _fallback_extract(text: str) -> List[Dict[str, Any]]:
    """
    Rule-based extractor fallback used when LLM API keys are missing or network calls fail.
    Implements fixes for Bug 1 (skipping filler), Bug 2 (accurate due_hint), and Bug 3 (owner=None for ambiguous).
    """
    items: List[Dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        # Bug 1 Fix: Skip conversational filler lines
        if _is_filler_line(line):
            continue

        lower_line = line.lower()
        tool_type = "jira"
        owner: Optional[str] = None

        # Tool classification
        if any(w in lower_line for w in ["document", "decided", "decision", "note", "switching"]):
            tool_type = "notion"
        elif any(w in lower_line for w in ["send", "email", "recap", "client", "message"]):
            tool_type = "email"
        else:
            tool_type = "jira"

        # Owner detection
        has_explicit_owner = False
        if "hardik" in lower_line:
            owner = "Hardik"
            has_explicit_owner = True
        elif "aadish" in lower_line:
            owner = "Aadish"
            has_explicit_owner = True
        elif "aadithya" in lower_line:
            owner = "Aadithya"
            has_explicit_owner = True
        elif "john" in lower_line:
            owner = "John"
            has_explicit_owner = True
        elif "neha" in lower_line:
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

        # Bug 2 Fix: Accurate due_hint time phrase extraction
        due_hint = _extract_time_phrase(line)

        # Ambiguity detection & Bug 3 Fix
        is_ambiguous = ("which " in lower_line or "do you mean" in lower_line or "someone" in lower_line or "?" in lower_line or not has_explicit_owner)

        if is_ambiguous:
            confidence = 0.40  # Genuinely ambiguous
            # Bug 3 Fix: When ambiguous=True and no specific person is named, owner MUST be null/None
            owner = None
        elif has_explicit_owner and due_hint:
            confidence = 0.95  # Explicit owner + task + deadline
        elif has_explicit_owner:
            confidence = 0.90  # Explicit owner + task
        elif tool_type == "notion":
            confidence = 0.88  # Clear documentation decision
        else:
            confidence = 0.85

        task = line.split(":", 1)[1].strip() if ":" in line else line

        items.append({
            "task": task,
            "owner": owner,
            "tool_type": tool_type,
            "confidence": confidence,
            "raw_context": line,
            "due_hint": due_hint,
            "ambiguous": is_ambiguous
        })

    return items


def _apply_ambiguity_rules(items: List[Dict[str, Any]]) -> List[ActionItem]:
    """
    Normalizes items and applies ambiguity detection & memory resolution rules.

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

        task = str(item.get("task", "")).strip()
        raw_context = str(item.get("raw_context", "")).strip()

        # Bug 1 Fix: Filter out filler tasks that slipped through
        if _is_filler_line(task) or _is_filler_line(raw_context):
            continue

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

        # Bug 2 Fix: Validate due_hint cleaning
        raw_due = item.get("due_hint")
        if raw_due is not None and str(raw_due).lower() not in ["null", "none"]:
            cleaned_due = str(raw_due).strip()
            # Clean single arbitrary words like "the" or "email"
            if cleaned_due.lower() in ["the", "email", "a", "an", "this", "by", "before"]:
                due_hint = _extract_time_phrase(raw_context)
            else:
                due_hint = cleaned_due
        else:
            due_hint = None

        # Owner resolution
        raw_owner = item.get("owner")
        if raw_owner is not None and str(raw_owner).lower() not in ["null", "none", "someone", "unassigned"]:
            owner: Optional[str] = str(raw_owner).strip()
        else:
            owner = None

        # Determine ambiguity
        raw_ambiguous = item.get("ambiguous")
        if raw_ambiguous is not None and isinstance(raw_ambiguous, bool):
            ambiguous = raw_ambiguous
        else:
            ambiguous = (confidence < 0.70) or (owner is None)

        # Bug 3 Fix: If ambiguous=True and owner is generic or not a specific person, set owner=None
        if ambiguous:
            if owner is None or owner.lower() in ["someone", "anyone", "team", "unassigned", "somebody"]:
                owner = None

        # Memory convention resolution
        if ambiguous and memory and owner:
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

        # Construct ActionItem matching schemas.py contract
        action_item: ActionItem = {
            "task": task,
            "owner": owner,  # type: ignore (null/None when ambiguous=True with no specific person)
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
    extraction_method = "rule-based fallback"

    try:
        items, extraction_method = extract_action_items(text)
        print(f"[extractor] Extraction Method Used: {extraction_method}")
        logger.info(f"Extraction Method Used: {extraction_method}")
    except Exception as err:
        extraction_method = "rule-based fallback"
        print(f"[extractor] Extraction Method Used: {extraction_method}")
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
