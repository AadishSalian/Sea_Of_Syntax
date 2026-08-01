"""
gmail_slack.py — Person 3 ("Executor: Comms & Clarification")

Owns: Gmail draft creation + Slack clarification loop (pause/resume logic)
Deliverable: create_email_draft(item) -> ExecutionResult
             ask_clarification(item) -> ExecutionResult

Do not edit: extractor.py, jira_notion.py, orchestrator.py, dashboard.py
"""

import os
import time
import base64
import pickle
from email.mime.text import MIMEText

from dotenv import load_dotenv

from schemas import ActionItem, ExecutionResult
from mocks import MOCK_ACTION_ITEM_EMAIL, MOCK_ACTION_ITEM_AMBIGUOUS

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from slack_sdk import WebClient

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
slack_client = WebClient(token=SLACK_BOT_TOKEN)

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

# Known roster for parsing clarification replies — expand as needed
KNOWN_NAMES = ["Alex (Marketing)", "Alex (Eng)", "Sarah (Design)", "Sarah (Sales)", "Sarah"]

CLARIFICATION_TIMEOUT_SECONDS = 60
CLARIFICATION_POLL_INTERVAL = 5


def get_gmail_service():
    from google.auth.transport.requests import Request
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build("gmail", "v1", credentials=creds)


def create_email_draft(item: ActionItem) -> ExecutionResult:
    """
    Creates a Gmail DRAFT (never auto-sends) via the Gmail API.
    Assumes a one-time OAuth flow has already produced token.pickle locally.
    """
    try:
        service = get_gmail_service()

        subject = f"Follow-up: {item['task']}"
        body = (
            f"Hi {item['owner']},\n\n"
            f"Following up from the meeting: {item['raw_context']}\n\n"
            f"Due: {item.get('due_hint') or 'ASAP'}\n\n"
            f"Thanks!"
        )

        message = MIMEText(body)
        message["to"] = "aadithyadeepak2006@gmail.com"
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()

        draft_id = draft["id"]
        link = f"https://mail.google.com/mail/#drafts?compose={draft_id}"

        return {
            "status": "success",
            "link": link,
            "tool": "gmail",
            "error": None,
            "resolved_owner": None,
        }
    except Exception as e:
        return {
            "status": "failed",
            "link": None,
            "tool": "gmail",
            "error": str(e),
            "resolved_owner": None,
        }


def ask_clarification(item: ActionItem) -> ExecutionResult:
    """
    THE MOST IMPORTANT FUNCTION IN THE PROJECT.

    Posts a clarifying question to Slack, polls for a human reply, and returns the
    resolved owner — or a timeout failure if nobody answers in time.
    """
    try:
        question = f"Which *{item['owner']}* did you mean for: \"{item['task']}\"?"
        response = slack_client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=question)
        ts = response["ts"]

        elapsed = 0
        while elapsed < CLARIFICATION_TIMEOUT_SECONDS:
            history = slack_client.conversations_history(
                channel=SLACK_CHANNEL_ID,
                oldest=ts,
                limit=10
            )
            messages = history.get("messages", [])
            replies = [m for m in messages if m.get("ts") != ts and not m.get("bot_id")]
            
            if replies:
                reply_text = replies[0]["text"]
                resolved = next(
                    (name for name in KNOWN_NAMES if name.lower() in reply_text.lower()),
                    reply_text.strip(),
                )
                return {
                    "status": "success",
                    "link": None,
                    "tool": "slack",
                    "error": None,
                    "resolved_owner": resolved,
                }

            time.sleep(CLARIFICATION_POLL_INTERVAL)
            elapsed += CLARIFICATION_POLL_INTERVAL

        return {
            "status": "failed",
            "link": None,
            "tool": "slack",
            "error": "clarification timeout",
            "resolved_owner": None,
        }
    except Exception as e:
        return {
            "status": "failed",
            "link": None,
            "tool": "slack",
            "error": str(e),
            "resolved_owner": None,
        }


if __name__ == "__main__":
    print("Testing create_email_draft()...")
    print(create_email_draft(MOCK_ACTION_ITEM_EMAIL))

    print("\nTesting ask_clarification() — will wait for a real Slack reply...")
    print(ask_clarification(MOCK_ACTION_ITEM_AMBIGUOUS))
