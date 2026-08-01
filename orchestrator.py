"""
orchestrator.py — Person 4 ("Glue & Demo Face")

Owns: the end-to-end pipeline wiring everyone else's functions together
Deliverable: run_pipeline(transcript_text) -> List[dict]  (final per-item results)

Do not edit: extractor.py, jira_notion.py, gmail_slack.py

HOUR 1-6: build against placeholder/mock functions below (already wired).
HOUR 6+ : swap each placeholder import for the real teammate function as they announce
          readiness. Only the import lines and mock-call lines need to change.
"""

from typing import List, TypedDict

from schemas import ActionItem, ExecutionResult
from mocks import ALL_MOCK_ITEMS

# ---------------------------------------------------------------------------
# SWAP THESE IMPORTS FOR REAL TEAMMATE FUNCTIONS AS THEY BECOME AVAILABLE
# ---------------------------------------------------------------------------
# from extractor import process_transcript
# from jira_notion import create_jira_ticket, update_notion_page
# from gmail_slack import create_email_draft, ask_clarification

def process_transcript(text: str) -> List[ActionItem]:
    """PLACEHOLDER — replace with: from extractor import process_transcript"""
    print("[orchestrator] using MOCK extractor")
    return ALL_MOCK_ITEMS


def create_jira_ticket(item: ActionItem) -> ExecutionResult:
    """PLACEHOLDER — replace with: from jira_notion import create_jira_ticket"""
    return {"status": "success", "link": "https://fake.example.com/JIRA-1",
            "tool": "jira", "error": None, "resolved_owner": None}


def update_notion_page(item: ActionItem) -> ExecutionResult:
    """PLACEHOLDER — replace with: from jira_notion import update_notion_page"""
    return {"status": "success", "link": "https://fake.example.com/notion-page",
            "tool": "notion", "error": None, "resolved_owner": None}


def create_email_draft(item: ActionItem) -> ExecutionResult:
    """PLACEHOLDER — replace with: from gmail_slack import create_email_draft"""
    return {"status": "success", "link": "https://fake.example.com/gmail-draft",
            "tool": "gmail", "error": None, "resolved_owner": None}


def ask_clarification(item: ActionItem) -> ExecutionResult:
    """PLACEHOLDER — replace with: from gmail_slack import ask_clarification"""
    return {"status": "success", "link": None, "tool": "slack",
            "error": None, "resolved_owner": "Alex (Marketing)"}

# ---------------------------------------------------------------------------


class PipelineResult(TypedDict):
    item: ActionItem
    result: ExecutionResult
    was_clarified: bool


def _execute_item(item: ActionItem) -> ExecutionResult:
    """Routes a single (already-resolved) ActionItem to the correct tool."""
    if item["tool_type"] == "jira":
        return create_jira_ticket(item)
    elif item["tool_type"] == "notion":
        return update_notion_page(item)
    elif item["tool_type"] == "email":
        return create_email_draft(item)
    else:
        return {"status": "failed", "link": None, "tool": "jira",
                "error": f"unknown tool_type: {item['tool_type']}", "resolved_owner": None}


def run_pipeline(transcript_text: str) -> List[PipelineResult]:
    """
    THE MAIN LOOP: ingest -> extract -> classify(already done in extractor) ->
    route -> execute -> clarify (conditional) -> report
    """
    items = process_transcript(transcript_text)
    results: List[PipelineResult] = []

    for item in items:
        was_clarified = bool(item.get("ambiguous"))

        if was_clarified:
            clarification = ask_clarification(item)
            if clarification["status"] == "success" and clarification["resolved_owner"]:
                item = dict(item)  # copy
                item["owner"] = clarification["resolved_owner"]
                item["ambiguous"] = False
                exec_result = _execute_item(item)  # type: ignore
            else:
                exec_result = clarification  # propagate the failure/timeout
        else:
            exec_result = _execute_item(item)

        results.append({"item": item, "result": exec_result, "was_clarified": was_clarified})

    return results


def summarize(results: List[PipelineResult]) -> dict:
    """Builds the completion summary shown at the end of the demo."""
    total = len(results)
    tools_touched = {r["result"]["tool"] for r in results}
    clarifications = sum(1 for r in results if r["was_clarified"])
    succeeded = sum(1 for r in results if r["result"]["status"] == "success")

    return {
        "total_action_items": total,
        "tools_touched": sorted(tools_touched),
        "clarifications_needed": clarifications,
        "succeeded": succeeded,
        "failed": total - succeeded,
    }


if __name__ == "__main__":
    with open("sample_transcript.txt", "r") as f:
        transcript = f.read()

    pipeline_results = run_pipeline(transcript)

    print("\n--- RESULTS ---")
    for r in pipeline_results:
        print(f"{r['item']['task'][:50]:50} -> {r['result']['status']} ({r['result']['link']})")

    print("\n--- SUMMARY ---")
    print(summarize(pipeline_results))
