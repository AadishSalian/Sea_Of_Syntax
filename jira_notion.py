"""
jira_notion.py — Person 2 ("Executor: Docs & Tickets")

Owns: Jira ticket creation + Notion page updates
Deliverable: create_jira_ticket(item) -> ExecutionResult
             update_notion_page(item) -> ExecutionResult

Scaffold stub implementation following docs/PARALLEL_WORK_CONTRACT.md.
"""

import os
from dotenv import load_dotenv

from schemas import ActionItem, ExecutionResult
from mocks import MOCK_ACTION_ITEM, MOCK_ACTION_ITEM_NOTION

load_dotenv()

# Environment variables as defined in PARALLEL_WORK_CONTRACT.md
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_ISSUE_TYPE_ID = os.getenv("JIRA_ISSUE_TYPE_ID")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")


def create_jira_ticket(item: ActionItem) -> ExecutionResult:
    """
    Creates a Jira ticket for the given action item.

    Args:
        item (ActionItem): Action item dictionary containing task, owner, raw_context, etc.

    Returns:
        ExecutionResult: Dict containing status, link, tool, error, and resolved_owner.
    """
    # TODO: Implement real Jira REST API v3 endpoint integration using JIRA_BASE_URL and JIRA_API_TOKEN
    # TODO: Construct issue fields (project key, summary, description, issuetype) and handle assignee mapping
    return {
        "status": "success",
        "link": f"{JIRA_BASE_URL or 'https://jira.example.com'}/browse/MOCK-1",
        "tool": "jira",
        "error": None,
        "resolved_owner": None,
    }


def update_notion_page(item: ActionItem) -> ExecutionResult:
    """
    Appends a new action item entry to a Notion page.

    Args:
        item (ActionItem): Action item dictionary containing task, owner, due_hint, etc.

    Returns:
        ExecutionResult: Dict containing status, link, tool, error, and resolved_owner.
    """
    # TODO: Implement real Notion API block creation using NOTION_TOKEN and NOTION_PAGE_ID
    # TODO: Format task details as Notion to_do block and send append request
    return {
        "status": "success",
        "link": f"https://notion.so/{NOTION_PAGE_ID or 'mockpageid'}",
        "tool": "notion",
        "error": None,
        "resolved_owner": None,
    }


if __name__ == "__main__":
    print("Testing create_jira_ticket stub...")
    print(create_jira_ticket(MOCK_ACTION_ITEM))

    print("\nTesting update_notion_page stub...")
    print(update_notion_page(MOCK_ACTION_ITEM_NOTION))
