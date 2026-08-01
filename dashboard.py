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

# --- PREMIUM DESIGN CSS INJECTION ---
st.markdown("""
<style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Base typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark mode background with slight gradient */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #1a1f35 100%);
        color: #ffffff;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    
    /* Premium Title styling */
    h1 {
        background: -webkit-linear-gradient(45deg, #4ade80, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }
    
    /* Card containers */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        backdrop-filter: blur(10px);
    }
    
    /* Card hover effects */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        border-color: rgba(59, 130, 246, 0.5) !important;
    }
    
    /* Primary button (Run Pipeline) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: opacity 0.2s ease, transform 0.1s ease;
    }
    
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        background: -webkit-linear-gradient(45deg, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Text input area */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
        border-radius: 8px !important;
        font-family: 'Inter', monospace;
    }
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("MeetingToMotion")
st.caption("✨ Autonomous Cross-Tool Action-Item Executor")

TOOL_ICONS = {"jira": "📋 Jira", "notion": "📓 Notion", "email": "📧 Email", "gmail": "📧 Email", "slack": "💬 Slack"}

def render_action_item_card(item: dict, status: str, link: str = None, error: str = None):
    """Renders a single action item as a nice card."""
    icon = TOOL_ICONS.get(item["tool_type"], "❓")
    
    # Status formatting
    if status == "done" or status == "success":
        status_badge = "🟢 **Done**"
    elif status == "failed":
        status_badge = "🔴 **Failed**"
    elif status == "needs clarification" or status == "pending_clarification":
        status_badge = "🟡 **Needs Clarification**"
    elif status == "in progress":
        status_badge = "🔵 **In Progress**"
    else:
        status_badge = "⚪ **Pending**"

    with st.container(border=True):
        col1, col2, col3 = st.columns([4, 2, 2])
        
        with col1:
            st.markdown(f"**{item['task']}**")
            st.caption(f"Raw Context: *\"{item['raw_context']}\"*")
            
        with col2:
            st.markdown(f"**Owner:** {item['owner']}")
            st.markdown(f"**Tool:** {icon}")
            
        with col3:
            st.markdown(status_badge)
            if link:
                st.markdown(f"[🔗 View Artifact]({link})")
            if error:
                st.markdown(f"⚠️ {error}")

# ---------------------------------------------------------------------------
# LIVE PIPELINE MODE
# ---------------------------------------------------------------------------
st.subheader("Live Pipeline")
transcript_input = st.text_area(
    "Paste a meeting transcript",
    value="Sarah, can you update the mockups before Friday's review? Ravi should send the client the recap of today's call. Let's document that we decided to use the v3 API. Can someone assign the analytics task to Alex? Which Alex, marketing or eng?",
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
    st.subheader("Pipeline Results")

    for r in results:
        render_action_item_card(
            item=r["item"], 
            status=r["result"]["status"] if r.get("result") else "failed", 
            link=r["result"].get("link") if r.get("result") else None,
            error=r["result"].get("error") if r.get("result") else None
        )

# ---------------------------------------------------------------------------
# STATIC PREVIEW MODE (TASK 3 REQUIREMENT)
# ---------------------------------------------------------------------------
st.divider()
st.subheader("UI Preview (Static Hardcoded Mock Data)")
st.info("This is the static list of 4 fake action items to prove the UI shape before real pipeline data exists.")

# We will display the 4 mock items with hardcoded varying statuses to prove the UI shape.
mock_statuses = [
    {"status": "done", "link": "https://fake.example.com/JIRA-1"},
    {"status": "in progress", "link": None},
    {"status": "done", "link": "https://fake.example.com/notion-page"},
    {"status": "needs clarification", "link": None}
]

for idx, item in enumerate(ALL_MOCK_ITEMS):
    mock_status = mock_statuses[idx % len(mock_statuses)]
    render_action_item_card(
        item=item,
        status=mock_status["status"],
        link=mock_status["link"]
    )
