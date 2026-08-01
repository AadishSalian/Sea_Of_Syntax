"""
jira_notion.py — Person 2 ("Executor: Docs & Tickets")

Owns: Jira ticket creation + Notion page updates
Deliverable: create_jira_ticket(item) -> ExecutionResult
             update_notion_page(item) -> ExecutionResult

Do not edit: extractor.py, gmail_slack.py, orchestrator.py, dashboard.py
"""

import os
import requests
from dotenv import load_dotenv

from schemas import ActionItem, ExecutionResult
from mocks import MOCK_ACTION_ITEM

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_ISSUE_TYPE_ID = os.getenv("JIRA_ISSUE_TYPE_ID")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

# Fill in real Jira accountIds as you get them during setup
OWNER_TO_JIRA_ACCOUNT_ID = {
    "Sarah": "REPLACE_WITH_REAL_ACCOUNT_ID",
}


def create_jira_ticket(item: ActionItem) -> ExecutionResult:
    """Creates a real Jira ticket via REST API v3."""
    try:
        url = f"{JIRA_BASE_URL}/rest/api/3/issue"
        auth = (JIRA_EMAIL, JIRA_API_TOKEN)
        headers = {"Content-Type": "application/json"}

        payload = {
            "fields": {
                "project": {"key": JIRA_PROJECT_KEY},
                "summary": item["task"],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": item["raw_context"]}],
                        }
                    ],
                },
                "issuetype": {"id": JIRA_ISSUE_TYPE_ID},
            }
        }

        account_id = OWNER_TO_JIRA_ACCOUNT_ID.get(item["owner"])
        if account_id:
            payload["fields"]["assignee"] = {"id": account_id}

        resp = requests.post(url, json=payload, auth=auth, headers=headers, timeout=10)
        resp.raise_for_status()
        issue_key = resp.json()["key"]

        return {
            "status": "success",
            "link": f"{JIRA_BASE_URL}/browse/{issue_key}",
            "tool": "jira",
            "error": None,
            "resolved_owner": None,
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
    """Appends a new block to a Notion page via the Notion API."""
    try:
        from notion_client import Client

        notion = Client(auth=NOTION_TOKEN)

        text = f"{item['task']} — Owner: {item['owner']}"
        if item.get("due_hint"):
            text += f" (Due: {item['due_hint']})"

        notion.blocks.children.append(
            block_id=NOTION_PAGE_ID,
            children=[
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "checked": False,
                    },
                }
            ],
        )

        return {
            "status": "success",
            "link": f"https://notion.so/{NOTION_PAGE_ID.replace('-', '')}",
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
    print(update_notion_page(MOCK_ACTION_ITEM))
