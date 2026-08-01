"""
jira_notion.py — Person 2 ("Executor: Docs & Tickets")

Owns: Jira ticket creation + Notion page updates
Deliverable: create_jira_ticket(item) -> ExecutionResult
             update_notion_page(item) -> ExecutionResult

Do not edit: extractor.py, gmail_slack.py, orchestrator.py, dashboard.py
"""

import os
import json
from typing import Optional, Tuple
import requests
from dotenv import load_dotenv

from schemas import ActionItem, ExecutionResult
from mocks import MOCK_ACTION_ITEM, MOCK_ACTION_ITEM_NOTION

load_dotenv()

# Environment Variables loaded from .env via load_dotenv()
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_ISSUE_TYPE_ID = os.getenv("JIRA_ISSUE_TYPE_ID")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

# Admin / Default Jira accountId fallback for ticket assignment
DEFAULT_JIRA_ACCOUNT_ID = os.getenv(
    "JIRA_ASSIGNEE_ACCOUNT_ID", "712020:979062c8-9986-4407-8a5b-b82877e16918"
)


def _resolve_assignee(
    owner: str, project_key: str, base_url: str, auth: Optional[Tuple[str, str]], headers: dict
) -> Tuple[Optional[str], str]:
    """
    Dynamically resolves Jira accountId for the given owner.
    1. Queries Jira assignable users endpoint.
    2. Fallbacks to memory.json if 0 or multiple users matched.
    Returns tuple of (resolved_accountId_or_None, target_project_key).
    """
    resolved_account_id: Optional[str] = None
    target_project_key = project_key

    # 1. Search Jira assignable users endpoint
    if base_url and owner and target_project_key:
        try:
            search_url = f"{base_url}/rest/api/3/user/assignable/search"
            params = {"project": target_project_key, "query": owner}
            if auth:
                resp = requests.get(search_url, params=params, auth=auth, headers=headers, timeout=10)
            else:
                resp = requests.get(search_url, params=params, headers=headers, timeout=10)

            if resp.status_code == 200:
                users = resp.json()
                if isinstance(users, list) and len(users) > 0:
                    # 1. Exact or partial displayName match
                    for u in users:
                        disp_name = (u.get("displayName") or "").lower()
                        email_addr = (u.get("emailAddress") or "").lower()
                        if owner.lower() in disp_name or owner.lower() in email_addr:
                            resolved_account_id = u.get("accountId")
                            break
                    # 2. Fallback to first returned assignable project user if no explicit name match
                    if not resolved_account_id and len(users) == 1:
                        resolved_account_id = users[0].get("accountId")
        except Exception as e:
            print(f"[jira_notion] Warning: Jira assignable user search failed: {e}")

    # 2. If 0 or >1 matches (ambiguous), fall back to memory.json
    if not resolved_account_id and os.path.exists("memory.json"):
        try:
            with open("memory.json", "r") as f:
                memory = json.load(f)

            mem_data = memory.get(owner)
            if not mem_data:
                # Case-insensitive / substring search fallback for memory keys (e.g. Sarah -> Sarah_Design)
                for k, v in memory.items():
                    if owner.lower() in k.lower():
                        mem_data = v
                        break

            if isinstance(mem_data, dict):
                resolved_account_id = (
                    mem_data.get("accountId")
                    or mem_data.get("jira_account_id")
                    or mem_data.get("account_id")
                )
                # Only use memory project override if default project key is not set in .env
                if mem_data.get("jira_project") and not project_key:
                    target_project_key = mem_data["jira_project"]
        except Exception as e:
            print(f"[jira_notion] Warning: memory.json lookup failed: {e}")

    return resolved_account_id, target_project_key


def _fetch_project_issue_types(
    project_key: str, base_url: str, auth: Optional[Tuple[str, str]], headers: dict
) -> list:
    """Fetches list of valid issue types for a project from Jira."""
    try:
        url = f"{base_url}/rest/api/3/project/{project_key}"
        if auth:
            resp = requests.get(url, auth=auth, headers=headers, timeout=10)
        else:
            resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            return resp.json().get("issueTypes", [])
    except Exception:
        pass
    return []


def _assign_issue_via_put(
    issue_key: str, account_id: str, base_url: str, auth: Optional[Tuple[str, str]], headers: dict
) -> bool:
    """
    Performs a follow-up PUT request to set the assignee of an issue if creation assignment failed or was omitted.
    Endpoint: PUT /rest/api/3/issue/{issueIdOrKey}/assignee
    """
    try:
        url = f"{base_url}/rest/api/3/issue/{issue_key}/assignee"
        payload = {"accountId": account_id}
        if auth:
            resp = requests.put(url, json=payload, auth=auth, headers=headers, timeout=10)
        else:
            resp = requests.put(url, json=payload, headers=headers, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[jira_notion] Warning: Follow-up PUT assignment failed for {issue_key}: {e}")
        return False


def create_jira_ticket(item: ActionItem) -> ExecutionResult:
    """
    Creates a Jira ticket via REST API v3 and automatically assigns it to the designated Jira account.
    Assigns via initial POST payload, with automatic PUT fallback if necessary.
    """
    try:
        if not JIRA_BASE_URL:
            return {
                "status": "failed",
                "link": None,
                "tool": "jira",
                "error": "JIRA_BASE_URL is missing in environment variables",
                "resolved_owner": None,
            }

        base_url_clean = JIRA_BASE_URL.rstrip("/")

        # Jira Cloud REST API v3 Auth setup
        if JIRA_EMAIL:
            auth: Optional[Tuple[str, str]] = (JIRA_EMAIL, JIRA_API_TOKEN or "")
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        else:
            auth = None
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {JIRA_API_TOKEN}",
            }

        owner_name = item.get("owner", "")
        default_project = JIRA_PROJECT_KEY or ""

        # Step 1: Assignee resolution (dynamic lookup -> fallback to DEFAULT_JIRA_ACCOUNT_ID)
        resolved_account_id, project_key = _resolve_assignee(
            owner=owner_name,
            project_key=default_project,
            base_url=base_url_clean,
            auth=auth,
            headers=headers,
        )

        # Guarantee assignment: if dynamic lookup didn't yield an accountId, use DEFAULT_JIRA_ACCOUNT_ID
        target_assignee_account_id = resolved_account_id or DEFAULT_JIRA_ACCOUNT_ID

        # Step 2: Build description (raw_context + due_hint if present)
        description_text = item.get("raw_context", "")
        if item.get("due_hint"):
            description_text += f"\nDue: {item['due_hint']}"

        # Jira REST API v3 expects Atlassian Document Format (ADF) for issue description
        description_adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description_text}],
                }
            ],
        }

        # Issue type resolution
        configured_type = (JIRA_ISSUE_TYPE_ID or "").strip()
        if configured_type:
            if configured_type.isdigit():
                issue_type_dict = {"id": configured_type}
            else:
                issue_type_dict = {"name": configured_type}
        else:
            issue_type_dict = {"name": "Task"}

        # Build issue payload including assignee during creation
        fields = {
            "project": {"key": project_key},
            "summary": item.get("task", "Untitled Task"),
            "description": description_adf,
            "issuetype": issue_type_dict,
            "assignee": {"accountId": target_assignee_account_id},
        }

        payload = {"fields": fields}

        # Step 3: POST to {JIRA_BASE_URL}/rest/api/3/issue
        issue_url = f"{base_url_clean}/rest/api/3/issue"
        if auth:
            resp = requests.post(issue_url, json=payload, auth=auth, headers=headers, timeout=10)
        else:
            resp = requests.post(issue_url, json=payload, headers=headers, timeout=10)

        # Retry logic if issue type was invalid for this project
        if resp.status_code == 400 and "issuetype" in resp.text:
            valid_types = _fetch_project_issue_types(project_key, base_url_clean, auth, headers)
            non_subtask = [it for it in valid_types if not it.get("subtask")]
            if non_subtask:
                payload["fields"]["issuetype"] = {"id": non_subtask[0]["id"]}
                if auth:
                    resp = requests.post(issue_url, json=payload, auth=auth, headers=headers, timeout=10)
                else:
                    resp = requests.post(issue_url, json=payload, headers=headers, timeout=10)

        # If initial POST fails because assignee field is restricted on create screen, retry without assignee in POST
        if resp.status_code == 400 and "assignee" in resp.text:
            del payload["fields"]["assignee"]
            if auth:
                resp = requests.post(issue_url, json=payload, auth=auth, headers=headers, timeout=10)
            else:
                resp = requests.post(issue_url, json=payload, headers=headers, timeout=10)

        if resp.status_code not in (200, 201):
            return {
                "status": "failed",
                "link": None,
                "tool": "jira",
                "error": f"Jira API HTTP {resp.status_code}: {resp.text[:200]}",
                "resolved_owner": None,
            }

        resp_data = resp.json()
        issue_key = resp_data.get("key")
        ticket_link = f"{base_url_clean}/browse/{issue_key}"

        # Step 4: Guarantee assignment via follow-up PUT if assignee wasn't included in POST response
        # or if initial creation didn't set assignee
        if issue_key:
            _assign_issue_via_put(issue_key, target_assignee_account_id, base_url_clean, auth, headers)

        return {
            "status": "success",
            "link": ticket_link,
            "tool": "jira",
            "error": None,
            "resolved_owner": target_assignee_account_id,
        }
    except Exception as e:
        return {
            "status": "failed",
            "link": None,
            "tool": "jira",
            "error": str(e),
            "resolved_owner": None,
        }


def update_notion_page(item: ActionItem) -> ExecutionResult:
    """
    Appends a to_do block to a Notion page at NOTION_PAGE_ID via Notion API.
    Handles exceptions gracefully without crashing the pipeline.
    """
    try:
        if not NOTION_TOKEN or not NOTION_PAGE_ID:
            return {
                "status": "failed",
                "link": None,
                "tool": "notion",
                "error": "NOTION_TOKEN or NOTION_PAGE_ID missing from environment",
                "resolved_owner": None,
            }

        # Construct block text: task + owner + due_hint if present
        text_content = f"{item.get('task', '')} — Owner: {item.get('owner', '')}"
        if item.get("due_hint"):
            text_content += f" (Due: {item['due_hint']})"

        clean_page_id = NOTION_PAGE_ID.replace("-", "")
        notion_url = f"https://notion.so/{clean_page_id}"

        # Option A: Try using official notion-client library
        try:
            from notion_client import Client

            notion = Client(auth=NOTION_TOKEN)
            notion.blocks.children.append(
                block_id=NOTION_PAGE_ID,
                children=[
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [
                                {"type": "text", "text": {"content": text_content}}
                            ],
                            "checked": False,
                        },
                    }
                ],
            )
        except Exception:
            # Option B: Fallback to Notion REST API v1 PATCH endpoint directly via requests
            endpoint_url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children"
            headers = {
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }
            payload = {
                "children": [
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [
                                {"type": "text", "text": {"content": text_content}}
                            ],
                            "checked": False,
                        },
                    }
                ]
            }
            resp = requests.patch(endpoint_url, json=payload, headers=headers, timeout=10)
            if resp.status_code not in (200, 201):
                return {
                    "status": "failed",
                    "link": None,
                    "tool": "notion",
                    "error": f"Notion API HTTP {resp.status_code}: {resp.text[:200]}",
                    "resolved_owner": None,
                }

        return {
            "status": "success",
            "link": notion_url,
            "tool": "notion",
            "error": None,
            "resolved_owner": None,
        }
    except Exception as e:
        return {
            "status": "failed",
            "link": None,
            "tool": "notion",
            "error": str(e),
            "resolved_owner": None,
        }


if __name__ == "__main__":
    print("Testing create_jira_ticket()...")
    print(create_jira_ticket(MOCK_ACTION_ITEM))

    print("\nTesting update_notion_page()...")
    print(update_notion_page(MOCK_ACTION_ITEM_NOTION))
