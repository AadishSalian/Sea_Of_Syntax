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
from email.mime.text import MIMEText

from dotenv import load_dotenv

from schemas import ActionItem, ExecutionResult
from mocks import MOCK_ACTION_ITEM_EMAIL, MOCK_ACTION_ITEM_AMBIGUOUS

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# Known roster for parsing clarification replies — expand as needed
KNOWN_NAMES = ["Alex (Marketing)", "Alex (Eng)", "Sarah (Design)", "Sarah (Sales)"]

CLARIFICATION_TIMEOUT_SECONDS = 60
CLARIFICATION_POLL_INTERVAL = 3


def create_email_draft(item: ActionItem) -> ExecutionResult:
    """
    Creates a Gmail DRAFT (never auto-sends) via the Gmail API.
    Assumes a one-time OAuth flow has already produced token.json locally.
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        subject = f"Follow-up: {item['task']}"
        body = f"{item['raw_context']}\n\n— Drafted by MeetingToMotion"

        message = MIMEText(body)
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )

        return {
            "status": "success",
            "link": f"https://mail.google.com/mail/u/0/#drafts/{draft['id']}",
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


def _post_slack_message(text: str):
    from slack_sdk import WebClient

    client = WebClient(token=SLACK_BOT_TOKEN)
    resp = client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=text)
    return resp["ts"]  # timestamp, used to find replies after this point


def _poll_for_reply(after_ts: str, timeout: int, interval: int):
    from slack_sdk import WebClient

    client = WebClient(token=SLACK_BOT_TOKEN)
    elapsed = 0

    while elapsed < timeout:
        history = client.conversations_history(
            channel=SLACK_CHANNEL_ID, oldest=after_ts, inclusive=False
        )
        messages = history.get("messages", [])
        if messages:
            return messages[-1]["text"]  # oldest new message after our post
        time.sleep(interval)
        elapsed += interval

    return None


def ask_clarification(item: ActionItem) -> ExecutionResult:
    """
    THE MOST IMPORTANT FUNCTION IN THE PROJECT.

    Posts a clarifying question to Slack, polls for a human reply, and returns the
    resolved owner — or a timeout failure if nobody answers in time.
    """
    try:
        question = (
            f"Clarification needed: \"{item['task']}\" — "
            f"context: \"{item['raw_context']}\". Who should this go to?"
        )
        ts = _post_slack_message(question)

        reply_text = _poll_for_reply(
            after_ts=ts,
            timeout=CLARIFICATION_TIMEOUT_SECONDS,
            interval=CLARIFICATION_POLL_INTERVAL,
        )

        if reply_text is None:
            return {
                "status": "failed",
                "link": None,
                "tool": "slack",
                "error": "clarification timeout",
                "resolved_owner": None,
            }

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
