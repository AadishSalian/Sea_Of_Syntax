"""
dashboard.py — Person 4 ("Glue & Demo Face")

Owns: the live Streamlit dashboard shown during the demo
Run with: streamlit run dashboard.py

HOUR 1-6: static fake data (already wired below).
HOUR 6+ : swap STATIC_ITEMS for a live call to orchestrator.run_pipeline().
"""

import streamlit as st

from orchestrator import stream_pipeline, summarize
import gmail_slack

st.set_page_config(page_title="MeetingToMotion", page_icon="🧭", layout="wide")

# --- PREMIUM DESIGN CSS INJECTION ---
st.markdown("""
<style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');
    
    /* Base typography */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Dynamic Animated Mesh Background */
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e1b4b, #020617, #312e81);
        background-size: 400% 400%;
        animation: gradientMesh 15s ease infinite;
        color: #ffffff;
    }
    
    @keyframes gradientMesh {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    
    /* Premium Animated Title styling */
    h1 {
        background: -webkit-linear-gradient(45deg, #10b981, #3b82f6, #8b5cf6, #ec4899);
        background-size: 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textGradient 6s linear infinite;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 2rem !important;
    }
    
    @keyframes textGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* True Glassmorphic Card containers */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: rgba(17, 24, 39, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(20px) saturate(150%);
        -webkit-backdrop-filter: blur(20px) saturate(150%);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    /* Card hover effects with ambient glow */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Primary button (Run Pipeline) with pulsing glow */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #d946ef 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(217, 70, 239, 0.3);
        width: 100%;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(217, 70, 239, 0.5), 0 0 15px rgba(79, 70, 229, 0.4);
        filter: brightness(1.1);
    }
    
    .stButton > button[kind="primary"]:active {
        transform: translateY(1px);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 3rem !important;
        font-weight: 700 !important;
        background: -webkit-linear-gradient(45deg, #a78bfa, #f472b6, #fb923c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textGradient 8s linear infinite;
        background-size: 300%;
    }
    
    /* Text input area - Glassmorphic */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #f8fafc !important;
        border-radius: 12px !important;
        font-family: 'Fira Code', monospace;
        font-size: 0.95rem;
        padding: 1rem;
        transition: all 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3), 0 0 20px rgba(139, 92, 246, 0.1) !important;
        background-color: rgba(15, 23, 42, 0.6) !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(255, 255, 255, 0.05) !important;
        margin: 2rem 0 !important;
    }
    
    /* Text rendering tweaks for crispness */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
</style>
""", unsafe_allow_html=True)

st.title("MeetingToMotion")
st.caption("✨ Autonomous Cross-Tool Action-Item Executor")

TOOL_ICONS = {"jira": "📋 Jira", "notion": "📓 Notion", "email": "📧 Email", "gmail": "📧 Email", "slack": "💬 Slack"}

def render_action_item_card_to_container(container, item: dict, status: str, link: str = None, error: str = None):
    """Renders a single action item as a nice card inside a specific st.empty container."""
    icon = TOOL_ICONS.get(item["tool_type"], "❓")
    
    # Status formatting
    if status == "done" or status == "success":
        status_badge = "✅ **Done**"
    elif status == "failed":
        status_badge = "❌ **Failed**"
    elif status == "needs clarification" or status == "pending_clarification":
        status_badge = "⚠️ **Needs Clarification**"
    elif status == "in progress":
        status_badge = "🔄 **In Progress**"
    else:
        status_badge = "⏳ **Pending**"

    with container.container(border=True):
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
                st.markdown(f"🚨 {error}")

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
    # Reset states for a genuinely new run
    st.session_state["pipeline_running"] = True
    st.session_state["final_results_cache"] = None
    gmail_slack._clarification_cache.clear()

if st.session_state.get("pipeline_running"):
    st.divider()
    
    # Create placeholders for metrics and cards
    metrics_placeholder = st.empty()
    cards_header = st.empty()
    card_placeholders = []
    
    # If we already finished, just use the cached results instead of re-streaming
    if st.session_state.get("final_results_cache") is not None:
        final_results = st.session_state["final_results_cache"]
        
        cards_header.subheader("Pipeline Results")
        
        # We need enough placeholders for the cached results
        for item in final_results:
            placeholder = st.empty()
            card_placeholders.append(placeholder)
            
            result = item.get("result")
            if result:
                status = result.get("status", "failed")
            else:
                status = "in progress"
                
            render_action_item_card_to_container(
                container=placeholder,
                item=item["item"],
                status=status,
                link=result.get("link") if result else None,
                error=result.get("error") if result else None
            )
            
    else:
        with st.spinner("Extracting, routing, and executing action items..."):
            cards_header.subheader("Pipeline Results")
            
            # Track final results for the summary
            final_results = []
            
            for event in stream_pipeline(transcript_input):
                if event["type"] == "extracted":
                    items = event["items"]
                    # Initialize placeholders and results tracking for each extracted item
                    for item in items:
                        placeholder = st.empty()
                        card_placeholders.append(placeholder)
                        
                        # Initial render as Pending
                        render_action_item_card_to_container(
                            container=placeholder,
                            item=item,
                            status="Pending"
                        )
                        
                        # Setup default final result struct
                        final_results.append({
                            "item": item,
                            "result": None,
                            "was_clarified": False
                        })
                        
                elif event["type"] == "update":
                    idx = event["index"]
                    state = event["state"]
                    item = state["item"]
                    result = state.get("result")
                    
                    # Update final result tracking
                    final_results[idx]["item"] = item
                    final_results[idx]["result"] = result
                    final_results[idx]["was_clarified"] = state.get("was_clarified", False)
                    
                    # Determine current status based on state
                    if result:
                        status = result.get("status", "failed")
                    else:
                        status = "in progress"
                    
                    render_action_item_card_to_container(
                        container=card_placeholders[idx],
                        item=item,
                        status=status,
                        link=result.get("link") if result else None,
                        error=result.get("error") if result else None
                    )

            # Save to cache so rerenders don't re-trigger the stream
            st.session_state["final_results_cache"] = final_results

    # Once done (either live or cached), update the summary metrics
    summary = summarize(final_results)
    
    with metrics_placeholder.container():
        cols = st.columns(4)
        cols[0].metric("Action items processed", summary["total_action_items"])
        cols[1].metric("Tools touched", len(summary["tools_touched"]))
        cols[2].metric("Clarifications needed", summary["clarifications_needed"])
        cols[3].metric("Succeeded", summary["succeeded"])
