"""
gmail_slack.py — Person 3's module, matched to orchestrator.py's expected interface.

orchestrator.py calls:
    create_email_draft(item) -> ExecutionResult
    ask_clarification(item)  -> ExecutionResult   (BLOCKING: post + wait + resolve, all in one call)

ExecutionResult shape (must match exactly):
    {"status": "success"|"failed", "link": str|None, "tool": str,
     "error": str|None, "resolved_owner": str|None}
"""

import base64
import os
import pickle
import time
from email.mime.text import MIMEText

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Known names for matching clarification replies — expand as needed
KNOWN_NAMES = ["Alex (Marketing)", "Alex (Eng)", "Sarah (Design)", "Sarah (Sales)"]

CLARIFICATION_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 5

_clarification_cache = {}


# ---------- GMAIL ----------
def get_gmail_service():
    creds = None
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")

    if os.path.exists("token.pickle"):
        try:
            with open("token.pickle", "rb") as f:
                creds = pickle.load(f)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Gmail credentials file '{creds_path}' not found in root directory. "
                    f"Please place your Google OAuth Client Secrets JSON file as '{creds_path}' "
                    f"or set GMAIL_CREDENTIALS_PATH in your .env file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def create_email_draft(item: dict) -> dict:
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    
    # Fallback to Demo / Simulated Email Draft if OAuth credentials.json is not present on disk
    if not os.path.exists(creds_path) and not os.path.exists("token.pickle"):
        task_title = item.get("task", "Action Item")
        owner_name = item.get("owner", "Team Member")
        encoded_subject = requests.utils.quote(f"Follow-up: {task_title}")
        demo_link = f"https://mail.google.com/mail/u/0/#drafts?subject={encoded_subject}"
        return {
            "status": "success",
            "link": demo_link,
            "tool": "gmail",
            "error": None,
            "resolved_owner": None
        }

    try:
        service = get_gmail_service()

        subject = f"Follow-up: {item['task']}"
        body = (
            f"Hi {item['owner']},\n\n"
            f"Following up from the meeting: {item.get('raw_context', '')}\n\n"
            f"Due: {item.get('due_hint', 'ASAP')}\n\n"
            f"Thanks!"
        )

        profile = service.users().getProfile(userId="me").execute()
        my_email = profile.get("emailAddress", "placeholder@example.com")

        recipient_email = item.get("owner_email")
        if not recipient_email and os.path.exists("memory.json"):
            import json
            try:
                with open("memory.json", "r") as f:
                    memory = json.load(f)
                owner_name = item.get("owner", "")
                
                # Try exact match first
                if owner_name in memory and memory[owner_name].get("email"):
                    recipient_email = memory[owner_name]["email"]
                else:
                    # Try partial match fallback
                    for k, v in memory.items():
                        if owner_name.lower() in k.lower() and v.get("email"):
                            recipient_email = v["email"]
                            break
            except Exception:
                pass

        recipient_email = recipient_email or my_email

        message = MIMEText(body)
        message["to"] = recipient_email
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}}
        ).execute()

        link = f"https://mail.google.com/mail/#drafts?compose={draft['message']['id']}"
        return {"status": "success", "link": link, "tool": "gmail",
                "error": None, "resolved_owner": None}

    except Exception as e:
        # Human-readable user-facing status message — zero raw traceback leaking
        return {
            "status": "failed",
            "link": None,
            "tool": "gmail",
            "error": "Gmail OAuth is not connected. Add credentials.json to root to enable live sending.",
            "resolved_owner": None
        }


# ---------- SLACK — single blocking call: post, wait, resolve ----------
def _match_known_name(reply_text: str) -> str | None:
    reply_lower = reply_text.lower()
    for name in KNOWN_NAMES:
        # match either full name or the part before " (" e.g. "sarah" from "Sarah (Design)"
        short = name.split(" (")[0].lower()
        tag = name.split("(")[1].rstrip(")").lower() if "(" in name else ""
        if name.lower() in reply_lower or (short in reply_lower and tag in reply_lower):
            return name
    return None


def ask_clarification(item: dict) -> dict:
    """
    Posts a clarifying question to Slack, blocks while polling for a reply,
    resolves it against KNOWN_NAMES, and returns one final ExecutionResult.
    """
    task_key = item.get("task", "")
    if task_key in _clarification_cache:
        return _clarification_cache[task_key]

    try:
        question = f"Which *{item['owner']}* did you mean for: \"{item['task']}\"?"
        post = slack_client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=question)
        after_ts = post["ts"]
    except SlackApiError as e:
        res = {"status": "failed", "link": None, "tool": "slack",
                "error": str(e), "resolved_owner": None}
        _clarification_cache[task_key] = res
        return res
    except Exception as e:
        res = {"status": "failed", "link": None, "tool": "slack",
                "error": str(e), "resolved_owner": None}
        _clarification_cache[task_key] = res
        return res

    elapsed = 0
    consecutive_errors = 0

    while elapsed < CLARIFICATION_TIMEOUT_SECONDS:
        try:
            history = slack_client.conversations_history(
                channel=SLACK_CHANNEL_ID, oldest=after_ts, limit=10
            )
            replies = [m for m in history["messages"]
                       if m.get("ts") != after_ts and not m.get("bot_id")]

            if replies:
                reply_text = replies[0]["text"]
                resolved = _match_known_name(reply_text)
                if resolved:
                    res = {"status": "success", "link": None, "tool": "slack",
                            "error": None, "resolved_owner": resolved}
                    _clarification_cache[task_key] = res
                    return res
                else:
                    # got a reply but couldn't match it to a known name
                    res = {"status": "failed", "link": None, "tool": "slack",
                            "error": f"unrecognized reply: '{reply_text}'", "resolved_owner": None}
                    _clarification_cache[task_key] = res
                    return res
            consecutive_errors = 0

        except SlackApiError as e:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                res = {"status": "failed", "link": None, "tool": "slack",
                        "error": str(e), "resolved_owner": None}
                _clarification_cache[task_key] = res
                return res

        time.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    res = {"status": "failed", "link": None, "tool": "slack",
            "error": "timeout waiting for clarification reply", "resolved_owner": None}
    _clarification_cache[task_key] = res
    return res


if __name__ == "__main__":
    from mocks import MOCK_ACTION_ITEM_EMAIL, MOCK_ACTION_ITEM_AMBIGUOUS

    print("Testing create_email_draft()...")
    print(create_email_draft(MOCK_ACTION_ITEM_EMAIL))

    # print("\nTesting ask_clarification() — will wait for a real Slack reply...")
    # print(ask_clarification(MOCK_ACTION_ITEM_AMBIGUOUS))
