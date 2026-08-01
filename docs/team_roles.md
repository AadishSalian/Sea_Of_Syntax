# Team Roles

| Person | Role | Owns | Files |
|---|---|---|---|
| Person 1 | The Brain | Transcript → structured action items → tool routing decisions | `extractor.py`, `memory.json` |
| Person 2 | Executor: Docs & Tickets | Jira ticket creation + Notion page updates | `jira_notion.py` |
| Person 3 | Executor: Comms & Clarification | Gmail draft creation + Slack clarification loop | `gmail_slack.py` |
| Person 4 | Glue & Demo Face | Orchestrator + live dashboard + integration testing + demo | `orchestrator.py`, `dashboard.py` |

## Sync Checkpoints

- **Hour 6** — Person 1 shares real `process_transcript()`; others swap mocks for the real function
- **Hour 12** — first full end-to-end pass on real data, all real code involved
- **Hour 18** — MVP locked, no new features after this point

## Golden Rule

Nobody writes logic against a guess of what another person's output looks like. Everyone
builds against `mocks.py` (matching `schemas.py`) until the real function is ready, then
does a one-line swap.
