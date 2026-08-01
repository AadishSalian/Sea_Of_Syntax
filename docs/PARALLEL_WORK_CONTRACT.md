# MeetingToMotion — Parallel Work Contract
Team: Sea of Syntax | Code Kudla 2026

This file is reference-only. It does not change the repo structure and should not be edited except to fix typos or add sync-checkpoint notes. Any change to a rule below must be announced in the team channel first.

## 1. Folder Structure (locked)
```
Sea_Of_Syntax
├── docs
│   └── team_roles.md
├── .env.example
├── .gitignore
├── dashboard.py       # Person 4
├── extractor.py       # Person 1
├── gmail_slack.py      # Person 3
├── jira_notion.py      # Person 2
├── memory.json         # Person 1
├── mocks.py            # shared, written once in Hour 1
├── orchestrator.py     # Person 4
├── py.py                # scratch/testing only — never import from this, never commit real logic here
├── README.md
├── requirements.txt
├── sample_transcript.txt
└── schemas.py           # THE CONTRACT — frozen after Hour 1
```
No new files or folders without a `[editing] structure` message first. No renames, no moves.

## 2. File Ownership
| File | Owner | Others may... |
|---|---|---|
| schemas.py | Person 1 (drafts), whole team (approves) | read only, never edit without announcing |
| extractor.py | Person 1 | not edit |
| jira_notion.py | Person 2 | not edit |
| gmail_slack.py | Person 3 | not edit |
| orchestrator.py | Person 4 | not edit without announcing |
| dashboard.py | Person 4 | not edit |
| mocks.py | shared, written together Hour 1 | edit only to add a new mock, announce first |
| memory.json | Person 1 | not edit |

## 3. Shared Data Contract (`schemas.py`)
```python
{
  "task": "Update the design mockups for the landing page",
  "owner": "Sarah",
  "tool_type": "jira",   # one of: "jira" | "email" | "notion"
  "confidence": 0.92,
  "raw_context": "Sarah, can you update the mockups before Friday's review?",
  "due_hint": "Friday",
  "ambiguous": False
}
```
Field names are case-sensitive. Do not add/remove/rename fields without a team-wide announcement.

## 4. Return-Value Contract (every execution function)
Success:
```python
{"status": "success", "link": "https://...", "tool": "jira"}
```
Failure:
```python
{"status": "failed", "error": "short reason", "tool": "jira"}
```
Every function in `jira_notion.py` and `gmail_slack.py` returns one of these two shapes. No custom keys.

## 5. Mock Objects (`mocks.py`)
```python
MOCK_ACTION_ITEM = {
  "task": "Update the design mockups for the landing page",
  "owner": "Sarah",
  "tool_type": "jira",
  "confidence": 0.92,
  "raw_context": "Sarah, can you update the mockups before Friday's review?",
  "due_hint": "Friday",
  "ambiguous": False
}

MOCK_ACTION_ITEM_AMBIGUOUS = {
  "task": "Assign the analytics task",
  "owner": "Alex",
  "tool_type": "jira",
  "confidence": 0.4,
  "raw_context": "Can someone assign the analytics task to Alex?",
  "due_hint": None,
  "ambiguous": True
}
```

## 6. Environment Variables (`.env.example`)
Every key any integration needs, name only, no real values committed:
```
GEMINI_API_KEY=
GROQ_API_KEY=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=
JIRA_ISSUE_TYPE_ID=
JIRA_BASE_URL=
NOTION_TOKEN=
NOTION_PAGE_ID=
GMAIL_OAUTH_CLIENT_ID=
GMAIL_OAUTH_CLIENT_SECRET=
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=
```

## 7. Naming Conventions
- Functions: `snake_case`, verb-first — `create_jira_ticket()`, `ask_clarification()`
- Classes: `PascalCase`
- Constants/env keys: `UPPER_SNAKE_CASE`
- No abbreviations in function names (`create_jira_ticket`, not `crt_jira_tkt`)

## 8. Python Version & Requirements
- Python 3.11.x (exact, not 3.10+) — pin locally with `python --version` before starting
- All new dependencies go into `requirements.txt` immediately, one line, no version omitted
- Install with `pip install -r requirements.txt` — nobody installs ad hoc without adding to the file

## 9. Git Workflow
- Branch naming: `person1/extractor`, `person2/jira-notion`, `person3/gmail-slack`, `person4/orchestrator`
- Solo-owned files: commit directly to `main`, no PR needed
- Shared files (`schemas.py`, `orchestrator.py`, `mocks.py`): pull first, announce `[editing] <file> for <reason>` before touching, push, then announce `[ready]`
- Commit every 30–45 min, even rough code

## 10. Communication Protocol (tagged, async, one channel)
| Tag | Format | Example |
|---|---|---|
| ready | `[ready] <function> is live in main` | `[ready] process_transcript() is live in main` |
| editing | `[editing] <file> for <reason>` | `[editing] schemas.py — adding due_hint field` |
| blocked | `[blocked] on <what>` | `[blocked] on Gmail OAuth consent screen` |
| broken | `[broken] <what> — don't pull yet` | `[broken] orchestrator.py — fixing, 10 min` |

Live sync only at Hour 6 / 12 / 18 checkpoints. Everything else async.

## 11. Sample Input
`sample_transcript.txt` — exactly 4 action items, 1 deliberately ambiguous owner (two people named Sarah). Locked after Hour 1, do not edit without team agreement.

## 12. Scratch File
`py.py` is scratch space only. Never import it. Never put real pipeline logic in it. Delete its contents before final commit if unused.