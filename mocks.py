"""
mocks.py — SHARED FAKE DATA

Owned by: EVERYONE (append-only — add new mocks freely, don't delete existing ones
without checking if a teammate depends on them)

Use these to build and test your piece BEFORE anyone else's real code exists.
This is what makes true parallel work possible.
"""

from schemas import ActionItem

# --- Standard, unambiguous item (tool_type: jira) ---
MOCK_ACTION_ITEM: ActionItem = {
    "task": "Update the design mockups for the landing page",
    "owner": "Sarah",
    "tool_type": "jira",
    "confidence": 0.92,
    "raw_context": "Sarah, can you update the mockups before Friday's review?",
    "due_hint": "Friday",
    "ambiguous": False,
}

# --- Email-routed item ---
MOCK_ACTION_ITEM_EMAIL: ActionItem = {
    "task": "Send the client the recap of today's call",
    "owner": "Ravi",
    "tool_type": "email",
    "confidence": 0.88,
    "raw_context": "Ravi should send the client the recap of today's call.",
    "due_hint": None,
    "ambiguous": False,
}

# --- Notion-routed item (a decision to document, not a task) ---
MOCK_ACTION_ITEM_NOTION: ActionItem = {
    "task": "Document that we decided to use the v3 API",
    "owner": "team",
    "tool_type": "notion",
    "confidence": 0.85,
    "raw_context": "Let's document that we decided to use the v3 API.",
    "due_hint": None,
    "ambiguous": False,
}

# --- Ambiguous item — triggers the clarification loop ---
MOCK_ACTION_ITEM_AMBIGUOUS: ActionItem = {
    "task": "Assign the analytics task",
    "owner": "Alex",
    "tool_type": "jira",
    "confidence": 0.4,
    "raw_context": "Can someone assign the analytics task to Alex? Which Alex, marketing or eng?",
    "due_hint": None,
    "ambiguous": True,
}

# Convenience list — the full "4 action items" MVP scope in one place
ALL_MOCK_ITEMS = [
    MOCK_ACTION_ITEM,
    MOCK_ACTION_ITEM_EMAIL,
    MOCK_ACTION_ITEM_NOTION,
    MOCK_ACTION_ITEM_AMBIGUOUS,
]
