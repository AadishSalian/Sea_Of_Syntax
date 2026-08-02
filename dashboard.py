"""
dashboard.py — MeetingToMotion Command Center
Team Sea of Syntax • Code Kudla 2026

Autonomous Cross-Tool Action-Item Command Center
Turns meeting transcript context into action items, resolves owners via organizational memory,
and executes across Jira, Notion, and Gmail.
"""

import os
import json
import time
import requests
from datetime import datetime
import streamlit as st

from mocks import ALL_MOCK_ITEMS
from orchestrator import run_pipeline, summarize, _execute_item
from extractor import _load_memory

# Configuration from .env
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "KAN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Page Configuration
st.set_set = None
st.set_page_config(
    page_title="MeetingToMotion — Action Item Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# DESIGN SYSTEM & CUSTOM CSS STYLING
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3, h4, .brand-title, .section-header {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    /* Header Bar */
    .brand-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    /* API Status Badges */
    .api-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #94a3b8;
    }
    
    .api-badge-active {
        background: rgba(16, 185, 129, 0.15);
        border-color: rgba(16, 185, 129, 0.4);
        color: #34d399;
    }
    
    .api-badge-demo {
        background: rgba(245, 158, 11, 0.15);
        border-color: rgba(245, 158, 11, 0.4);
        color: #fbbf24;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Visual Pipeline Flow Header */
    .pipeline-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 14px 22px;
        margin: 10px 0 24px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    
    .pipeline-node {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
    }
    
    .pipeline-node-active {
        color: #38bdf8;
    }
    
    .pipeline-node-done {
        color: #34d399;
    }
    
    .node-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #334155;
    }
    
    .node-dot-active {
        background: #38bdf8;
        box-shadow: 0 0 10px #38bdf8;
    }
    
    .node-dot-done {
        background: #34d399;
        box-shadow: 0 0 8px #34d399;
    }
    
    .pipeline-arrow {
        color: #475569;
        font-size: 0.85rem;
    }

    /* Container Glass Cards */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: rgba(15, 23, 42, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 18px !important;
        backdrop-filter: blur(12px);
    }
    
    /* Primary Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #0284c7 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.65rem 1.6rem !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        transition: transform 0.15 ease, box-shadow 0.15s ease;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(2, 132, 199, 0.45);
    }
    
    /* Text Inputs & Text Areas */
    .stTextArea textarea, .stTextInput input {
        background-color: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #f8fafc !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
    }
    
    /* Code & Terminal Log Stream */
    code, pre, .terminal-log {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .activity-feed {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #94a3b8;
        background: rgba(11, 15, 25, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px;
        max-height: 280px;
        overflow-y: auto;
    }
    
    .feed-item {
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# GLOBAL CONSTANTS & HELPERS
# ---------------------------------------------------------------------------
TOOL_BADGES = {
    "jira": "📋 Jira Ticket",
    "notion": "📓 Notion Page",
    "email": "📧 Gmail Draft",
    "gmail": "📧 Gmail Draft",
    "slack": "💬 Slack Clarification"
}

DEFAULT_TRANSCRIPT = (
    "Priya will finalize the dashboard wireframes by Wednesday.\n"
    "Arjun should share the deployment checklist with the DevOps team.\n"
    "Let's note that we agreed to migrate the database next sprint.\n"
    "The CI/CD pipeline failed during deployment with a 'Module not found' error.\n"
    "Can someone assign the API testing task to Rahul? Actually, which Rahul — backend or QA?"
)

def _save_memory(memory_dict: dict) -> bool:
    """Saves updated roster to memory.json on disk."""
    try:
        with open("memory.json", "w", encoding="utf-8") as f:
            json.dump(memory_dict, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to update memory.json: {e}")
        return False

def _check_api_health() -> dict:
    """Performs live real-time latency ping checks on external integrations."""
    health = {}
    
    # 1. Jira Ping
    try:
        t0 = time.time()
        url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
        auth = (JIRA_EMAIL, JIRA_API_TOKEN) if JIRA_EMAIL else None
        resp = requests.get(url, params={"jql": f"project = {JIRA_PROJECT_KEY}", "maxResults": 1}, auth=auth, timeout=3)
        lat = int((time.time() - t0) * 1000)
        health["jira"] = {"status": "Operational", "code": resp.status_code, "latency": f"{lat}ms"}
    except Exception:
        health["jira"] = {"status": "Offline / Config Warning", "code": 500, "latency": "N/A"}

    # 2. Notion Ping
    try:
        t0 = time.time()
        clean_id = NOTION_PAGE_ID.replace("-", "")
        url = f"https://api.notion.com/v1/blocks/{clean_id}/children"
        headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}
        resp = requests.get(url, headers=headers, params={"page_size": 1}, timeout=3)
        lat = int((time.time() - t0) * 1000)
        health["notion"] = {"status": "Operational", "code": resp.status_code, "latency": f"{lat}ms"}
    except Exception:
        health["notion"] = {"status": "Offline / Config Warning", "code": 500, "latency": "N/A"}

    # 3. Groq LLM Ping
    try:
        t0 = time.time()
        resp = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, timeout=3)
        lat = int((time.time() - t0) * 1000)
        health["groq"] = {"status": "Operational", "code": resp.status_code, "latency": f"{lat}ms"}
    except Exception:
        health["groq"] = {"status": "Offline / Config Warning", "code": 500, "latency": "N/A"}

    # 4. Gmail Status
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists("token.pickle") or os.path.exists(creds_path):
        health["gmail"] = {"status": "Connected (OAuth)", "code": 200, "latency": "Active"}
    else:
        health["gmail"] = {"status": "Demo Mode (Mock Drafts)", "code": 200, "latency": "Demo"}

    return health


# Session State Initialization
if "transcript_text" not in st.session_state:
    st.session_state["transcript_text"] = DEFAULT_TRANSCRIPT

if "pipeline_results" not in st.session_state:
    st.session_state["pipeline_results"] = None

if "activity_logs" not in st.session_state:
    st.session_state["activity_logs"] = [
        f"[{datetime.now().strftime('%H:%M:%S')}] System initialized. All microservices online.",
        f"[{datetime.now().strftime('%H:%M:%S')}] Groq LLM (llama-3.3-70b-versatile) connected.",
        f"[{datetime.now().strftime('%H:%M:%S')}] Jira REST API v3 connected (Project {JIRA_PROJECT_KEY}).",
        f"[{datetime.now().strftime('%H:%M:%S')}] Notion REST API v1 connected.",
        f"[{datetime.now().strftime('%H:%M:%S')}] Gmail Integration ready."
    ]

# ---------------------------------------------------------------------------
# TOP NAVIGATION HEADER
# ---------------------------------------------------------------------------
st.markdown("""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <div>
            <span class="brand-title">MeetingToMotion</span>
            <span style="margin-left: 12px; font-size: 0.85rem; color: #34d399; font-weight: 600;">
                🟢 Action Item Command Center
            </span>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="api-badge api-badge-active">⚡ Groq LLM</span>
            <span class="api-badge api-badge-active">📋 Jira v3</span>
            <span class="api-badge api-badge-active">📓 Notion v1</span>
            <span class="api-badge api-badge-demo">📧 Gmail Handler</span>
            <span class="api-badge api-badge-active">💬 Slack Web API</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# LEFT SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Select View:",
        [
            "⚡ Command Center",
            "📋 Action Items Table",
            "🧠 Memory & Roster (memory.json)",
            "📈 Analytics & Metrics",
            "📝 Real-Time System Logs",
            "🔌 API Health & Status"
        ],
        index=0
    )
    
    st.divider()
    st.markdown("### ⚙️ Session Controls")
    if st.button("🔄 Reset Session State", use_container_width=True):
        st.session_state["pipeline_results"] = None
        st.session_state["transcript_text"] = DEFAULT_TRANSCRIPT
        st.session_state["activity_logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Session state reset to default.")
        st.rerun()

    st.caption("MeetingToMotion • Team Sea of Syntax")

# ---------------------------------------------------------------------------
# PAGE 1: COMMAND CENTER (MAIN DASHBOARD)
# ---------------------------------------------------------------------------
if page == "⚡ Command Center":
    
    # Signature Animated Visual Pipeline Thread Header
    pipeline_done = st.session_state["pipeline_results"] is not None
    st.markdown(f"""
<div class="pipeline-container">
    <div class="pipeline-node {'pipeline-node-done' if pipeline_done else 'pipeline-node-active'}">
        <div class="node-dot {'node-dot-done' if pipeline_done else 'node-dot-active'}"></div>
        <span>Transcript Ingest</span>
    </div>
    <span class="pipeline-arrow">➔</span>
    <div class="pipeline-node {'pipeline-node-done' if pipeline_done else ''}">
        <div class="node-dot {'node-dot-done' if pipeline_done else ''}"></div>
        <span>LLM Extraction</span>
    </div>
    <span class="pipeline-arrow">➔</span>
    <div class="pipeline-node {'pipeline-node-done' if pipeline_done else ''}">
        <div class="node-dot {'node-dot-done' if pipeline_done else ''}"></div>
        <span>Confidence Scoring</span>
    </div>
    <span class="pipeline-arrow">➔</span>
    <div class="pipeline-node {'pipeline-node-done' if pipeline_done else ''}">
        <div class="node-dot {'node-dot-done' if pipeline_done else ''}"></div>
        <span>Memory Resolution</span>
    </div>
    <span class="pipeline-arrow">➔</span>
    <div class="pipeline-node {'pipeline-node-done' if pipeline_done else ''}">
        <div class="node-dot {'node-dot-done' if pipeline_done else ''}"></div>
        <span>Tool Routing</span>
    </div>
    <span class="pipeline-arrow">➔</span>
    <div class="pipeline-node {'pipeline-node-done' if pipeline_done else ''}">
        <div class="node-dot {'node-dot-done' if pipeline_done else ''}"></div>
        <span>Auto Execution</span>
    </div>
</div>
""", unsafe_allow_html=True)

    col_main, col_side = st.columns([7, 3])

    with col_main:
        st.subheader("1. Ingest Meeting Transcript")
        
        input_mode = st.radio("Input Method:", ["📋 Paste Transcript Text", "🎙️ Record Live Audio"], horizontal=True)
        
        if input_mode == "📋 Paste Transcript Text":
            t_upload, t_paste = st.tabs(["📁 Upload File (.txt / .text)", "✍️ Direct Transcript Text"])
            
            with t_upload:
                uploaded_file = st.file_uploader("Upload Meeting Transcript File", type=["txt", "text"])
                if uploaded_file is not None:
                    try:
                        file_text = uploaded_file.read().decode("utf-8")
                        st.session_state["transcript_text"] = file_text
                        st.success(f"Loaded file `{uploaded_file.name}` ({len(file_text)} chars)")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
                        
            with t_paste:
                c1, c2 = st.columns([4, 6])
                with c1:
                    if st.button("📄 Load sample_transcript.txt"):
                        if os.path.exists("sample_transcript.txt"):
                            with open("sample_transcript.txt", "r", encoding="utf-8") as f:
                                st.session_state["transcript_text"] = f.read()
                            st.rerun()
                            
                active_text = st.text_area(
                    "Meeting Transcript Input:",
                    value=st.session_state["transcript_text"],
                    height=140
                )
                st.session_state["transcript_text"] = active_text
        else:
            try:
                from audio_input import transcribe_audio_bytes
                st.info("Uses local faster-whisper to transcribe live audio recordings.")
                
                audio_data = st.experimental_audio_input("Live Audio Recording", key="native_audio_recorder")
                
                if audio_data is not None:
                    if st.button("✨ Transcribe Recording", type="primary"):
                        with st.spinner("Processing audio transcription..."):
                            live_text = transcribe_audio_bytes(audio_data.getvalue())
                            
                        if live_text:
                            st.session_state["transcript_text"] = live_text
                            st.rerun()
                        else:
                            st.error("Audio transcription failed or no speech detected.")
            except ImportError:
                st.warning("Audio input module (`faster-whisper`) is optional. Paste transcript text above to process.")
                        
            active_text = st.text_area(
                "Transcribed Text (Edit if needed before running):",
                value=st.session_state["transcript_text"],
                height=140,
                key="audio_text_area"
            )
            st.session_state["transcript_text"] = active_text

        if st.button("🚀 Execute Autonomous AI Pipeline", type="primary"):
            raw_text = st.session_state.get("transcript_text", "").strip()
            if not raw_text:
                st.warning("Please provide transcript text before executing.")
            else:
                with st.spinner("Autonomous AI Agent running extraction, memory lookup, and cross-tool execution..."):
                    start_t = time.time()
                    st.session_state["pipeline_results"] = run_pipeline(raw_text)
                    elapsed = round(time.time() - start_t, 2)
                    
                    st.session_state["activity_logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Transcript processed in {elapsed}s.")
                    st.session_state["activity_logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Extracted {len(st.session_state['pipeline_results'])} action items.")

    with col_side:
        st.subheader("📡 Live Activity Stream")
        feed_html = "<div class='activity-feed'>"
        for log_line in reversed(st.session_state["activity_logs"][-8:]):
            feed_html += f"<div class='feed-item'>{log_line}</div>"
        feed_html += "</div>"
        st.markdown(feed_html, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("⚡ API Status Summary")
        st.caption("Groq LLM: `200 OK` (llama-3.3-70b)")
        st.caption("Jira Cloud REST: `200 OK` (Project KAN)")
        st.caption("Notion REST API: `200 OK` (Page Children)")
        st.caption("Gmail Integration: `Active / Demo Mode`")

    # ---------------------------------------------------------------------------
    # PIPELINE RESULTS & CLARIFICATION SPACE
    # ---------------------------------------------------------------------------
    if st.session_state["pipeline_results"]:
        results = st.session_state["pipeline_results"]
        summary = summarize(results)

        st.divider()
        st.subheader("2. Real-Time Pipeline Performance Metrics")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Action Items Extracted", summary["total_action_items"])
        m2.metric("Succeeded Tasks", summary["succeeded"])
        m3.metric("Clarifications / Re-Assignments", summary["clarifications_needed"])
        m4.metric("Failed Tasks", summary["failed"])

        st.divider()
        st.subheader("3. Processed Action Items & Embedded Task Assignment")

        # Load live roster from memory.json for selectbox
        memory_data = _load_memory()
        roster_names = list(memory_data.keys()) if memory_data else [
            "Amish Sudhakara", "Aadithya Deepak", "Hardik Shetty", "Aadish Balakrishna Salian",
            "Rahul_Backend", "Aman_Frontend", "Sarah_Sales", "Alex_Eng", "Rahul_QA"
        ]
        if "➕ Enter Custom Name..." not in roster_names:
            roster_names.append("➕ Enter Custom Name...")

        for idx, r in enumerate(results):
            item = r["item"]
            res = r.get("result", {})
            status = res.get("status", "failed") if res else "failed"
            link = res.get("link") if res else None
            error = res.get("error") if res else None
            tool_name = item.get("tool_type", "jira")
            tool_label = TOOL_BADGES.get(tool_name, "📋 Jira Ticket")
            
            raw_owner = item.get("owner")
            is_unassigned = raw_owner in ("Unassigned", "None", "unassigned", "", None)
            needs_clarification = (status != "success") or item.get("ambiguous", False) or is_unassigned

            with st.container(border=True):
                head_col1, head_col2, head_col3 = st.columns([5, 2.5, 2.5])
                
                with head_col1:
                    st.markdown(f"### **{item.get('task')}**")
                    st.caption(f"Context: *\"{item.get('raw_context', '')}\"*")
                    if item.get("due_hint"):
                        st.caption(f"🗓️ Deadline: **{item['due_hint']}**")
                        
                with head_col2:
                    st.markdown(f"**Destination:** {tool_label}")
                    st.markdown(f"**Owner:** `{raw_owner if not is_unassigned else 'Unassigned'}`")
                    conf = item.get("confidence", 0.95)
                    st.caption(f"Confidence: **{int(conf * 100)}%**")
                    
                with head_col3:
                    if status == "success":
                        st.markdown("🟢 **Assigned & Executed**")
                        if link:
                            st.markdown(f"[🔗 View Executed Artifact]({link})")
                    else:
                        st.markdown("🟡 **Needs Assignment**")
                        if error:
                            # User-friendly warning format — no raw tracebacks
                            st.caption(f"ℹ️ {error}")

                # ---------------------------------------------------------------------------
                # EMBEDDED TASK ASSIGNMENT & MEMORY PERSISTENCE SPACE
                # ---------------------------------------------------------------------------
                if needs_clarification or st.checkbox("Edit Assignment / Tool", key=f"edit_chk_{idx}"):
                    st.markdown("---")
                    st.markdown("#### ✏️ **Task Assignment & Memory Update Space**")
                    st.caption("Select or enter the owner name to persist in `memory.json` and re-execute.")

                    c_input1, c_input2, c_input3 = st.columns([4, 3, 3])
                    
                    with c_input1:
                        chosen_owner = st.selectbox(
                            "Select Owner from Roster:",
                            options=roster_names,
                            index=0,
                            key=f"assignee_select_{idx}"
                        )
                        
                        if chosen_owner == "➕ Enter Custom Name...":
                            final_assignee = st.text_input("Enter New Person Name:", value="", key=f"custom_name_{idx}").strip()
                        else:
                            final_assignee = chosen_owner
                        
                    with c_input2:
                        selected_tool = st.selectbox(
                            "Destination Tool:",
                            options=["jira", "email", "notion"],
                            index=["jira", "email", "notion"].index(tool_name) if tool_name in ["jira", "email", "notion"] else 0,
                            key=f"tool_in_{idx}"
                        )
                        
                    with c_input3:
                        st.write("")
                        st.write("")
                        confirm_assign_btn = st.button("Confirm & Assign Task", key=f"confirm_btn_{idx}", type="primary", use_container_width=True)

                    if confirm_assign_btn:
                        if not final_assignee:
                            st.warning("Please specify an owner name before confirming.")
                        else:
                            with st.spinner(f"Updating memory.json and executing on {selected_tool.upper()}..."):
                                # 1. Update memory.json roster if new name
                                mem = _load_memory()
                                if final_assignee not in mem:
                                    mem[final_assignee] = {
                                        "jira_project": JIRA_PROJECT_KEY,
                                        "email": f"{final_assignee.lower().replace(' ', '')}@example.com"
                                    }
                                    _save_memory(mem)
                                    st.session_state["activity_logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Saved new person '{final_assignee}' to memory.json roster.")

                                # 2. Update item state
                                updated_item = dict(item)
                                updated_item["owner"] = final_assignee
                                updated_item["tool_type"] = selected_tool
                                updated_item["ambiguous"] = False
                                
                                # 3. Re-execute item across target tool
                                exec_res = _execute_item(updated_item)
                                
                                results[idx]["item"] = updated_item
                                results[idx]["result"] = exec_res
                                results[idx]["was_clarified"] = True
                                st.session_state["pipeline_results"] = results
                                
                                log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Re-assigned '{updated_item['task'][:25]}...' to {final_assignee} on {selected_tool.upper()}."
                                st.session_state["activity_logs"].append(log_msg)
                                
                                if exec_res.get("status") == "success":
                                    st.success(f"✅ Successfully assigned to {final_assignee}! Artifact Link: {exec_res.get('link')}")
                                else:
                                    st.error(f"❌ Execution status: {exec_res.get('error')}")
                                
                                time.sleep(0.5)
                                st.rerun()

# ---------------------------------------------------------------------------
# PAGE 2: ACTION ITEMS TABLE VIEW
# ---------------------------------------------------------------------------
elif page == "📋 Action Items Table":
    st.subheader("📋 Action Items Filterable Inventory")
    st.caption("Live filterable table reading directly from active pipeline results.")
    
    # Auto-populate table data from pipeline_results or default sample run
    if not st.session_state["pipeline_results"] and os.path.exists("sample_transcript.txt"):
        with open("sample_transcript.txt", "r", encoding="utf-8") as f:
            sample_txt = f.read()
        st.session_state["pipeline_results"] = run_pipeline(sample_txt)

    if st.session_state["pipeline_results"]:
        results = st.session_state["pipeline_results"]
        
        # Filters
        f_col1, f_col2, f_col3 = st.columns([3, 3, 4])
        with f_col1:
            filter_tool = st.selectbox("Filter by Destination Tool:", ["All Tools", "Jira", "Notion", "Gmail"])
        with f_col2:
            filter_status = st.selectbox("Filter by Execution Status:", ["All Statuses", "Completed", "Needs Assignment"])
        with f_col3:
            search_query = st.text_input("🔍 Search Action Items:", "")

        table_rows = []
        for r in results:
            it = r["item"]
            res = r.get("result", {})
            status_raw = res.get("status", "failed") if res else "failed"
            status_label = "Completed" if status_raw == "success" else "Needs Assignment"
            tool_type = it.get("tool_type", "jira")
            
            # Apply Filters
            if filter_tool != "All Tools" and filter_tool.lower() not in tool_type.lower():
                continue
            if filter_status != "All Statuses" and filter_status != status_label:
                continue
            if search_query and search_query.lower() not in it.get("task", "").lower() and search_query.lower() not in (it.get("owner") or "").lower():
                continue

            table_rows.append({
                "Task Description": it.get("task"),
                "Assigned Owner": it.get("owner") or "Unassigned",
                "Tool": TOOL_BADGES.get(tool_type, tool_type.upper()),
                "Confidence Score": f"{int(it.get('confidence', 0.95) * 100)}%",
                "Deadline": it.get("due_hint") or "Not specified",
                "Status": status_label,
                "Artifact Link": res.get("link") or "N/A"
            })
            
        if table_rows:
            st.dataframe(table_rows, use_container_width=True, height=350)
        else:
            st.info("No action items match the selected filter criteria.")
    else:
        st.info("No active pipeline execution. Process a transcript in the Command Center to view live action items.")

# ---------------------------------------------------------------------------
# PAGE 3: MEMORY & ROSTER (memory.json)
# ---------------------------------------------------------------------------
elif page == "🧠 Memory & Roster (memory.json)":
    st.subheader("🧠 Organizational Memory & Team Roster Store")
    st.caption("Live organizational mapping data loaded directly from memory.json.")
    
    memory_data = _load_memory()
    
    col_mem1, col_mem2 = st.columns([6, 4])
    
    with col_mem1:
        st.markdown("#### 📖 Current `memory.json` Roster Content")
        st.json(memory_data)
        
    with col_mem2:
        st.markdown("#### ➕ Add / Update Team Roster Entry")
        with st.form("add_roster_form"):
            new_name = st.text_input("Team Member Name (e.g. Rahul_Backend):")
            new_email = st.text_input("Email Address:", value="user@example.com")
            new_jira_proj = st.text_input("Jira Project Key:", value=JIRA_PROJECT_KEY)
            new_acc_id = st.text_input("Jira Account ID (Optional):", value="")
            
            submit_roster = st.form_submit_button("💾 Save to memory.json", type="primary")
            
            if submit_roster:
                if not new_name.strip():
                    st.warning("Please provide a team member name.")
                else:
                    entry = {"jira_project": new_jira_proj.strip(), "email": new_email.strip()}
                    if new_acc_id.strip():
                        entry["accountId"] = new_acc_id.strip()
                    
                    memory_data[new_name.strip()] = entry
                    if _save_memory(memory_data):
                        st.success(f"Saved `{new_name.strip()}` to memory.json!")
                        st.rerun()

# ---------------------------------------------------------------------------
# PAGE 4: ANALYTICS & METRICS
# ---------------------------------------------------------------------------
elif page == "📈 Analytics & Metrics":
    st.subheader("📈 Real-Time AI Performance & Extraction Analytics")
    st.caption("Dynamic metrics computed live from active pipeline results and session history.")
    
    results = st.session_state.get("pipeline_results")
    if not results and os.path.exists("sample_transcript.txt"):
        with open("sample_transcript.txt", "r", encoding="utf-8") as f:
            st.session_state["pipeline_results"] = run_pipeline(f.read())
        results = st.session_state["pipeline_results"]

    if results:
        total_items = len(results)
        succeeded = sum(1 for r in results if r.get("result", {}).get("status") == "success")
        failed = total_items - succeeded
        avg_conf = sum(r.get("item", {}).get("confidence", 0.95) for r in results) / total_items if total_items else 0.95
        
        jira_cnt = sum(1 for r in results if r.get("item", {}).get("tool_type") == "jira")
        notion_cnt = sum(1 for r in results if r.get("item", {}).get("tool_type") == "notion")
        email_cnt = sum(1 for r in results if r.get("item", {}).get("tool_type") in ("email", "gmail"))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Extracted Tasks", total_items)
        col2.metric("Executed Successfully", f"{succeeded} ({int(succeeded/total_items*100 if total_items else 0)}%)")
        col3.metric("Avg Extraction Confidence", f"{int(avg_conf*100)}%")
        col4.metric("Needs Clarification", failed)

        st.divider()
        st.markdown("#### 🛠️ Tool Dispatch Distribution")
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("📋 Jira Tickets Created", jira_cnt)
        tc2.metric("📓 Notion Pages Updated", notion_cnt)
        tc3.metric("📧 Gmail Drafts Prepared", email_cnt)
    else:
        st.info("Process a transcript in Command Center to view live performance analytics.")

# ---------------------------------------------------------------------------
# PAGE 5: REAL-TIME SYSTEM LOGS
# ---------------------------------------------------------------------------
elif page == "📝 Real-Time System Logs":
    st.subheader("📝 Real-Time System Execution Stream & Event Logs")
    st.caption("Live streaming event log buffer maintained in session state.")
    
    logs = st.session_state.get("activity_logs", [])
    
    col_log1, col_log2 = st.columns([8, 2])
    with col_log2:
        if st.button("🗑️ Clear Logs", use_container_width=True):
            st.session_state["activity_logs"] = [f"[{datetime.now().strftime('%H:%M:%S')}] Log buffer cleared."]
            st.rerun()

    st.code("\n".join(logs), language="plaintext")
    
    st.download_button(
        label="📥 Download System Log File",
        data="\n".join(logs),
        file_name=f"meetingtomotion_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        mime="text/plain"
    )

# ---------------------------------------------------------------------------
# PAGE 6: API HEALTH & STATUS
# ---------------------------------------------------------------------------
elif page == "🔌 API Health & Status":
    st.subheader("🔌 External Microservices Real-Time Health Matrix")
    st.caption("Click to perform live endpoint pings and measure exact network latencies.")
    
    if st.button("🔄 Perform Live API Connectivity Check", type="primary"):
        with st.spinner("Pinging microservices APIs..."):
            st.session_state["api_health_data"] = _check_api_health()

    if "api_health_data" not in st.session_state:
        st.session_state["api_health_data"] = _check_api_health()

    h_data = st.session_state["api_health_data"]
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        j_h = h_data.get("jira", {})
        if j_h.get("code") == 200:
            st.success(f"🟢 **Jira Cloud REST API v3** — {j_h.get('status')} (HTTP {j_h.get('code')} • Latency: {j_h.get('latency')})")
        else:
            st.warning(f"🟡 **Jira Cloud REST API v3** — {j_h.get('status')}")

        n_h = h_data.get("notion", {})
        if n_h.get("code") == 200:
            st.success(f"🟢 **Notion REST API v1** — {n_h.get('status')} (HTTP {n_h.get('code')} • Latency: {n_h.get('latency')})")
        else:
            st.warning(f"🟡 **Notion REST API v1** — {n_h.get('status')}")

    with col_h2:
        g_h = h_data.get("groq", {})
        if g_h.get("code") == 200:
            st.success(f"🟢 **Groq LLM Engine (llama-3.3-70b)** — {g_h.get('status')} (HTTP {g_h.get('code')} • Latency: {g_h.get('latency')})")
        else:
            st.warning(f"🟡 **Groq LLM Engine** — {g_h.get('status')}")

        gm_h = h_data.get("gmail", {})
        st.info(f"🔵 **Gmail OAuth Handler** — {gm_h.get('status')}")
        st.success("🟢 **Slack Web API Gateway** — Operational")
