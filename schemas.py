"""
schemas.py — THE SHARED CONTRACT

Owned by: EVERYONE (agree together in Hour 0-1, then FREEZE)
If you need to change this after Hour 1, announce it in the team channel FIRST:
  "[editing] schemas.py — adding X field, back in 5 min"

This is the one file every other module in this project depends on.
"""

from typing import TypedDict, Optional, Literal


class ActionItem(TypedDict):
    task: str                                  # e.g. "Update the design mockups for the landing page"
    owner: str                                 # e.g. "Sarah"
    tool_type: Literal["jira", "email", "notion"]
    confidence: float                          # 0.0 - 1.0
    raw_context: str                           # original sentence(s) from the transcript
    due_hint: Optional[str]                    # e.g. "Friday", or None
    ambiguous: bool                            # True if owner/confidence needs human clarification


class ExecutionResult(TypedDict):
    """
    Standard return shape for every execution function
    (create_jira_ticket, update_notion_page, create_email_draft, ask_clarification).
    """
    status: Literal["success", "failed", "pending_clarification"]
    link: Optional[str]                        # URL to the created artifact, or None
    tool: Literal["jira", "notion", "gmail", "slack"]
    error: Optional[str]                       # human-readable error message, or None
    resolved_owner: Optional[str]              # only set by ask_clarification()


# Example of the exact shape (useful for quick reference without opening mocks.py):
EXAMPLE_ACTION_ITEM: ActionItem = {
    "task": "Update the design mockups for the landing page",
    "owner": "Sarah",
    "tool_type": "jira",
    "confidence": 0.92,
    "raw_context": "Sarah, can you update the mockups before Friday's review?",
    "due_hint": "Friday",
    "ambiguous": False,
}
