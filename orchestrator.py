"""
orchestrator.py — Person 4 ("Glue & Demo Face")

Owns: the end-to-end pipeline wiring everyone else's functions together
Deliverable: run_pipeline(transcript_text) -> List[dict]  (final per-item results)

Do not edit: extractor.py, jira_notion.py, gmail_slack.py

HOUR 1-6: build against placeholder/mock functions below (already wired).
HOUR 6+ : swap each placeholder import for the real teammate function as they announce
          readiness. Only the import lines and mock-call lines need to change.
"""

from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, START, END

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


# --- LANGGRAPH IMPLEMENTATION ---

class ItemState(TypedDict):
    item: ActionItem
    result: Optional[ExecutionResult]
    was_clarified: bool

def classify_node(state: ItemState):
    """Classify the item to determine if it is ambiguous (already done in extraction for now)."""
    return {"item": state["item"]}  # Return existing state instead of {}

def route_after_classify(state: ItemState):
    """Routing logic: if ambiguous, route to clarify, else execute."""
    if state["item"].get("ambiguous"):
        return "clarify"
    return "execute"

def clarify_node(state: ItemState):
    """Ask a human for clarification."""
    item = dict(state["item"])  # copy to avoid mutating original reference directly
    clarification = ask_clarification(item)
    
    if clarification["status"] == "success" and clarification["resolved_owner"]:
        item["owner"] = clarification["resolved_owner"]
        item["ambiguous"] = False
        return {"item": item, "was_clarified": True}
    else:
        # If clarification failed, record the error result
        return {"result": clarification, "was_clarified": True}

def execute_node(state: ItemState):
    """Execute the task by creating the appropriate ticket, draft, or page."""
    if state.get("result"): 
        # If we already have a result (e.g. clarification failed), skip execution
        return {"result": state["result"]}
    
    exec_result = _execute_item(state["item"])
    return {"result": exec_result}

# Build the Item Processing Graph
builder = StateGraph(ItemState)
builder.add_node("classify", classify_node)
builder.add_node("clarify", clarify_node)
builder.add_node("execute", execute_node)

builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify",
    route_after_classify,
    {"clarify": "clarify", "execute": "execute"}
)
# Route back into execute after clarification completes
builder.add_edge("clarify", "execute")
builder.add_edge("execute", END)

item_graph = builder.compile()

def run_pipeline(transcript_text: str) -> List[PipelineResult]:
    """
    THE MAIN LOOP: ingest -> extract -> classify -> route -> execute -> clarify -> report
    """
    # INGEST & EXTRACT
    items = process_transcript(transcript_text)
    
    results: List[PipelineResult] = []

    for item in items:
        # Process each item through the StateGraph
        initial_state = {"item": item, "result": None, "was_clarified": False}
        final_state = item_graph.invoke(initial_state)
        
        results.append({
            "item": final_state["item"],
            "result": final_state["result"],
            "was_clarified": final_state["was_clarified"]
        })

    # REPORT is handled by returning results for downstream summary
    return results


def summarize(results: List[PipelineResult]) -> dict:
    """Builds the completion summary shown at the end of the demo."""
    total = len(results)
    tools_touched = {r["result"]["tool"] for r in results if r.get("result")}
    clarifications = sum(1 for r in results if r["was_clarified"])
    succeeded = sum(1 for r in results if r.get("result") and r["result"]["status"] == "success")

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
        task_preview = r['item']['task'][:50]
        status = r['result']['status'] if r.get('result') else 'unknown'
        link = r['result']['link'] if r.get('result') else 'None'
        print(f"{task_preview:50} -> {status} ({link})")

    print("\n--- SUMMARY ---")
    print(summarize(pipeline_results))
