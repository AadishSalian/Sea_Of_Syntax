"""
dashboard.py — Person 4 ("Glue & Demo Face")

Owns: the live Streamlit dashboard shown during the demo
Run with: streamlit run dashboard.py

HOUR 1-6: static fake data (already wired below).
HOUR 6+ : swap STATIC_ITEMS for a live call to orchestrator.run_pipeline().
"""

import streamlit as st

from mocks import ALL_MOCK_ITEMS
from orchestrator import run_pipeline, summarize

st.set_page_config(page_title="MeetingToMotion", page_icon="🧭", layout="wide")

st.title("🧭 MeetingToMotion")
st.caption("Autonomous Cross-Tool Action-Item Executor")

TOOL_ICONS = {"jira": "📋", "notion": "📓", "email": "📧", "gmail": "📧", "slack": "💬"}
STATUS_COLORS = {"success": "🟢", "failed": "🔴", "pending_clarification": "🟡"}

transcript_input = st.text_area(
    "Paste a meeting transcript",
    value=open("sample_transcript.txt").read(),
    height=120,
)

if st.button("Run MeetingToMotion", type="primary"):
    with st.spinner("Extracting, routing, and executing action items..."):
        results = run_pipeline(transcript_input)
        summary = summarize(results)

    st.divider()
    cols = st.columns(4)
    cols[0].metric("Action items processed", summary["total_action_items"])
    cols[1].metric("Tools touched", len(summary["tools_touched"]))
    cols[2].metric("Clarifications needed", summary["clarifications_needed"])
    cols[3].metric("Succeeded", summary["succeeded"])

    st.divider()
    st.subheader("Action Items")

    for r in results:
        item, result = r["item"], r["result"]
        icon = TOOL_ICONS.get(item["tool_type"], "❓")
        status_icon = STATUS_COLORS.get(result["status"], "⚪")

        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 2])
            c1.markdown(f"**{icon} {item['task']}**\n\nOwner: {item['owner']}")
            c2.markdown(f"{status_icon} `{result['status']}`")
            if result["link"]:
                c3.markdown(f"[View result]({result['link']})")
            elif result["error"]:
                c3.markdown(f"⚠️ {result['error']}")
else:
    st.info("Paste a transcript above and click **Run MeetingToMotion** to see it in action.")
    st.subheader("Preview (static mock data)")
    for item in ALL_MOCK_ITEMS:
        icon = TOOL_ICONS.get(item["tool_type"], "❓")
        with st.container(border=True):
            st.markdown(f"**{icon} {item['task']}** — Owner: {item['owner']} · "
                        f"{'🟡 needs clarification' if item['ambiguous'] else '⚪ pending'}")
