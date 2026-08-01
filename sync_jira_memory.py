"""
sync_jira_memory.py — Utility to sync assignable Jira users to memory.json
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
MEMORY_FILE = "memory.json"


def fetch_all_assignable_users(base_url: str, project_key: str, auth, headers) -> list:
    """Fetches all assignable users for a project with pagination."""
    users = []
    start_at = 0
    max_results = 50

    while True:
        url = f"{base_url.rstrip('/')}/rest/api/3/user/assignable/search"
        params = {
            "project": project_key,
            "startAt": start_at,
            "maxResults": max_results,
        }
        if auth:
            resp = requests.get(url, params=params, auth=auth, headers=headers, timeout=10)
        else:
            resp = requests.get(url, params=params, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"[sync_jira_memory] Failed to fetch users: HTTP {resp.status_code} - {resp.text[:200]}")
            break

        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            break

        users.extend(batch)
        if len(batch) < max_results:
            break
        start_at += max_results

    return users


def sync_memory_from_jira():
    if not JIRA_BASE_URL or not JIRA_PROJECT_KEY:
        print("[FAIL] JIRA_BASE_URL and JIRA_PROJECT_KEY must be set in .env")
        return

    base_url = JIRA_BASE_URL.rstrip("/")
    if JIRA_EMAIL:
        auth = (JIRA_EMAIL, JIRA_API_TOKEN or "")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
    else:
        auth = None
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {JIRA_API_TOKEN}",
        }

    # Fetch assignable users
    assignable_users = fetch_all_assignable_users(base_url, JIRA_PROJECT_KEY, auth, headers)

    # Load existing memory.json
    memory_data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory_data = json.load(f)
        except Exception as e:
            print(f"[sync_jira_memory] Warning loading existing {MEMORY_FILE}: {e}")

    updated_count = 0
    added_count = 0

    # Sync assignable users
    for u in assignable_users:
        display_name = u.get("displayName", "").strip()
        account_id = u.get("accountId")
        if not display_name or not account_id:
            continue

        # Check exact key or case-insensitive match in existing memory
        matched_key = None
        if display_name in memory_data:
            matched_key = display_name
        else:
            for k in memory_data.keys():
                if display_name.lower() == k.lower():
                    matched_key = k
                    break

        if matched_key:
            # Update existing entry preserving existing fields
            if not isinstance(memory_data[matched_key], dict):
                memory_data[matched_key] = {}
            if memory_data[matched_key].get("accountId") != account_id:
                memory_data[matched_key]["accountId"] = account_id
                updated_count += 1
        else:
            # Add new entry
            memory_data[display_name] = {"accountId": account_id}
            added_count += 1

    # Save updated memory.json
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=2)

    print("=========================================================")
    print("           JIRA ASSIGNABLE USERS MEMORY SYNC             ")
    print("=========================================================")
    print(f"Total Assignable Users Found:  {len(assignable_users)}")
    print(f"Existing Users Updated:        {updated_count}")
    print(f"New Users Added:              {added_count}")
    print("\nSample Memory Entries:")
    sample = {k: memory_data[k] for k in list(memory_data.keys())[:10]}
    print(json.dumps(sample, indent=2))
    print("=========================================================\n")


if __name__ == "__main__":
    sync_memory_from_jira()
