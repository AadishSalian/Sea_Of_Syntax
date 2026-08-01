# MeetingToMotion

Autonomous Cross-Tool Action-Item Executor — 24-Hour Hackathon Build

> "Extraction is commoditized. Execution is the moat."

## What This Is

An agent that extracts action items from a meeting transcript and autonomously executes
them across Jira, Gmail, and Notion — asking a human for clarification via Slack only
when genuinely ambiguous.

## File Ownership (Read This First)

| File | Owner | Status |
|---|---|---|
| `schemas.py` | Shared — lock in Hour 0-1, then freeze | 🔒 |
| `mocks.py` | Shared — append-only | 🔓 |
| `sample_transcript.txt` | Shared — agree together in Hour 0-1 | 🔒 |
| `memory.json` | Person 1 | — |
| `extractor.py` | **Person 1** — The Brain | — |
| `jira_notion.py` | **Person 2** — Docs & Tickets | — |
| `gmail_slack.py` | **Person 3** — Comms & Clarification | — |
| `orchestrator.py` | **Person 4** — Glue & Demo Face | — |
| `dashboard.py` | **Person 4** — Glue & Demo Face | — |

**Golden rule:** only edit files you own. If you must touch a shared/locked file,
announce it in the team channel first (`[editing] schemas.py — adding X, back in 5 min`).

## Setup (Everyone, Hour 0)

```bash
git clone <this-repo-url>
cd meetingtomotion
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then fill in your own keys/tokens
```

## Running Your Piece Independently

Every owned file has a `if __name__ == "__main__":` block at the bottom so you can run
and test it standalone, without anyone else's code needing to exist yet:

```bash
python extractor.py        # Person 1
python jira_notion.py       # Person 2
python gmail_slack.py       # Person 3
python orchestrator.py      # Person 4
streamlit run dashboard.py  # Person 4
```

## The Shared Contract

Every function in this project passes data around using the `ActionItem` shape defined
in `schemas.py`. See `mocks.py` for ready-to-use fake objects so you never have to wait
on anyone else's real code to start building.

## Docs

- `docs/build_plan.md` — full 24-hour phase-by-phase plan
- `docs/team_roles.md` — who owns what, in detail

## Sync Checkpoints

- **Hour 6** — Person 1 shares real `process_transcript()`
- **Hour 12** — first full end-to-end pass on real data
- **Hour 18** — MVP locked, no new features after this point
