"""
chatbot.py — Autonomous Query & Status Chatbot Engine

Provides natural language querying capabilities over Jira tickets, Notion pages,
and action items using Groq LLM with multi-turn conversation history and pagination-aware API integrations.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Initialize environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="[chatbot] %(levelname)s: %(message)s")
logger = logging.getLogger("chatbot")

# Configuration from .env
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "KAN")

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# In-memory session history storage for module-level persistence
_session_history: List[Dict[str, str]] = []


def clear_session_history() -> None:
    """Clears the module-level in-memory session history."""
    global _session_history
    _session_history.clear()
    logger.info("Session history cleared.")


def fetch_all_notion_blocks(page_id: str = NOTION_PAGE_ID, token: str = NOTION_TOKEN) -> List[Dict[str, Any]]:
    """
    Fetches ALL blocks for a given Notion page ID using cursor pagination.

    Args:
        page_id: Notion Page ID string.
        token: Notion Bearer API Token.

    Returns:
        List of block dictionaries.
    """
    if not page_id or not token:
        logger.warning("Missing NOTION_PAGE_ID or NOTION_TOKEN for Notion read.")
        return []

    clean_id = page_id.replace("-", "")
    url = f"https://api.notion.com/v1/blocks/{clean_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    all_blocks: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        params: Dict[str, Any] = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Notion API error HTTP {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            results = data.get("results", [])
            all_blocks.extend(results)

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        except Exception as e:
            logger.error(f"Failed to fetch Notion blocks: {e}")
            break

    logger.info(f"Fetched {len(all_blocks)} total blocks from Notion page {clean_id[:8]}...")
    return all_blocks


def fetch_jira_tickets() -> List[Dict[str, Any]]:
    """
    Fetches Jira tickets for JIRA_PROJECT_KEY ordered by creation date descending.
    Supports pagination using startAt/maxResults.

    Returns:
        List of cleaned dicts: {"key": str, "summary": str, "status": str, "assignee_name": str}
    """
    if not JIRA_BASE_URL or not JIRA_API_TOKEN:
        logger.warning("Missing JIRA credentials in .env.")
        return []

    auth = (JIRA_EMAIL, JIRA_API_TOKEN) if JIRA_EMAIL else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    if not auth:
        headers["Authorization"] = f"Bearer {JIRA_API_TOKEN}"

    search_url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    cleaned_tickets: List[Dict[str, Any]] = []
    start_at = 0
    max_results = 50

    while True:
        get_params = {
            "jql": f"project = {JIRA_PROJECT_KEY} ORDER BY created DESC",
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,status,assignee"
        }

        try:
            if auth:
                resp = requests.get(search_url, params=get_params, auth=auth, headers=headers, timeout=10)
            else:
                resp = requests.get(search_url, params=get_params, headers=headers, timeout=10)

            # Fallback if GET fails
            if resp.status_code != 200:
                payload = {
                    "jql": f"project = {JIRA_PROJECT_KEY} ORDER BY created DESC",
                    "maxResults": max_results,
                    "fields": ["summary", "status", "assignee"]
                }
                if auth:
                    resp = requests.post(search_url, json=payload, auth=auth, headers=headers, timeout=10)
                else:
                    resp = requests.post(search_url, json=payload, headers=headers, timeout=10)

            if resp.status_code != 200:
                logger.error(f"Jira API search failed HTTP {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            issues = data.get("issues", [])
            total = data.get("total", len(issues))

            for issue in issues:
                key = issue.get("key", "UNKNOWN")
                fields = issue.get("fields", {})
                summary = fields.get("summary", "No Summary")
                status = fields.get("status", {}).get("name", "Unknown Status")
                assignee_obj = fields.get("assignee")
                assignee_name = assignee_obj.get("displayName") if assignee_obj else "Unassigned"

                cleaned_tickets.append({
                    "key": key,
                    "summary": summary,
                    "status": status,
                    "assignee_name": assignee_name
                })

            start_at += len(issues)
            if start_at >= total or len(issues) == 0:
                break

        except Exception as e:
            logger.error(f"Failed to fetch Jira tickets: {e}")
            break

    logger.info(f"Fetched {len(cleaned_tickets)} total Jira tickets for project {JIRA_PROJECT_KEY}.")
    return cleaned_tickets


def format_notion_blocks(blocks: List[Dict[str, Any]]) -> str:
    """
    Turns raw Notion blocks into clean, readable text.
    De-duplicates identical consecutive lines to avoid cluttering LLM context.

    Args:
        blocks: List of raw Notion block dicts.

    Returns:
        Formatted newline-separated string.
    """
    lines: List[str] = []
    
    for block in blocks:
        b_type = block.get("type", "")
        text = ""

        if b_type in block and isinstance(block[b_type], dict):
            rich_text = block[b_type].get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text if isinstance(t, dict)]).strip()
        elif b_type == "child_page":
            title = block.get("child_page", {}).get("title", "").strip()
            if title:
                text = f"[Child Page: {title}]"

        if text:
            # Avoid duplicate consecutive lines
            if not lines or lines[-1] != text:
                lines.append(text)

    return "\n".join(lines)


def answer_question(
    user_query: str,
    history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Answers natural language questions about the team's Jira tickets and Notion tasks
    using Groq LLM (llama-3.3-70b-versatile) with multi-turn conversation memory.

    Args:
        user_query: The natural language question string.
        history: Optional conversation history list of {"role": "user"/"assistant", "content": "..."}.
                 If None, uses module-level in-memory session history.

    Returns:
        Tuple of (answer_string, updated_history_list).
    """
    global _session_history
    if history is None:
        active_history = _session_history
    else:
        active_history = history

    if not GROQ_API_KEY:
        error_msg = "Error: GROQ_API_KEY is not set in environment."
        active_history.append({"role": "user", "content": user_query})
        active_history.append({"role": "assistant", "content": error_msg})
        return error_msg, active_history

    # 1. Fetch fresh live context from Jira and Notion (re-fetches on every call)
    jira_tickets = fetch_jira_tickets()
    notion_blocks = fetch_all_notion_blocks()
    notion_text = format_notion_blocks(notion_blocks)

    # 2. Format Jira tickets
    jira_lines = []
    for t in jira_tickets:
        jira_lines.append(f"- {t['key']} | Status: {t['status']} | Assignee: {t['assignee_name']} | Summary: {t['summary']}")
    jira_text = "\n".join(jira_lines) if jira_lines else "No Jira tickets found."

    # 3. Construct fresh context text for system prompt
    context_str = (
        "=== JIRA TICKETS ===\n"
        f"{jira_text}\n\n"
        "=== NOTION TASKS & NOTES ===\n"
        f"{notion_text if notion_text else 'No Notion tasks found.'}"
    )

    system_prompt_content = (
        "You are a helpful assistant answering questions about the team's Jira tickets and Notion tasks.\n"
        "Use ONLY the provided data below. If the answer isn't in the data, say you don't have that information — do not guess.\n\n"
        f"Context:\n{context_str}"
    )

    # 4. Construct message payload: System prompt + Prior conversation history + New user message
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt_content}
    ]

    for entry in active_history:
        messages.append({"role": entry["role"], "content": entry["content"]})

    messages.append({"role": "user", "content": user_query})

    # 5. Call Groq API
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.1
    }

    try:
        resp = requests.post(groq_url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            answer = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        else:
            logger.error(f"Groq API call failed HTTP {resp.status_code}: {resp.text}")
            answer = f"Error: Groq API call failed with status code {resp.status_code}."
    except Exception as e:
        logger.error(f"Groq API call exception: {e}")
        answer = f"Error connecting to Groq API: {e}"

    # 6. Update growing history
    active_history.append({"role": "user", "content": user_query})
    active_history.append({"role": "assistant", "content": answer})

    return answer, active_history


if __name__ == "__main__":
    print("=" * 70)
    print("        CHATBOT.PY — MULTI-TURN CONVERSATION HISTORY VERIFICATION   ")
    print("=" * 70)

    # Clear previous history
    clear_session_history()

    # Turn 1
    t1_query = "What tasks does Hardik have?"
    print(f"\n--- TURN 1 (User): '{t1_query}' ---")
    t1_answer, current_history = answer_question(t1_query)
    print(f"ASSISTANT:\n{t1_answer}\n")
    print(f"[History Length: {len(current_history)} messages]")

    # Turn 2 (Follow-up relying on history context)
    t2_query = "Is any of those overdue or pending?"
    print(f"\n--- TURN 2 (User): '{t2_query}' ---")
    t2_answer, current_history = answer_question(t2_query, history=current_history)
    print(f"ASSISTANT:\n{t2_answer}\n")
    print(f"[History Length: {len(current_history)} messages]")

    print("=" * 70)
