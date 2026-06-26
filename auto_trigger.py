
import os
import subprocess
import time
import requests

from services.ing_service.config import get_repo_config


API_URL = os.getenv(
    "AUTO_TRIGGER_API_URL",
    "http://127.0.0.1:8000/webhook/github"
)


def get_repo_details():
    repo_config = get_repo_config()
    return (
        repo_config["repo_path"],
        repo_config["repo_name"],
        repo_config["repo_owner"],
    )


def get_latest_commit(repo_path: str):
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
    ).decode().strip()


last_commit = None
repo_path, repo_name, repo_owner = get_repo_details()

print(f"🚀 Auto trigger started for {repo_name} at {repo_path}...")


while True:
    try:
        current_commit = get_latest_commit(repo_path)

        if current_commit != last_commit:
            print(f"\n✅ New commit detected: {current_commit}")

            # ✅ wait to ensure commit is stable
            time.sleep(5)

            new_commit = get_latest_commit(repo_path)

            if new_commit != current_commit:
                print("⚠️ Commit unstable (HEAD moved), skipping...")
                continue

            # ✅ FINAL COMMIT TO USE
            stable_commit = new_commit

            print(f"➡️ Sending stable commit: {stable_commit}")

            # ✅ Build payload
            payload = {
                "ref": os.getenv("AUTO_TRIGGER_REF", "refs/heads/main"),
                "repository": {
                    "name": repo_name,
                    "owner": {
                        "login": repo_owner or os.getenv("GITHUB_USERNAME", "")
                    },
                },
                "pusher": {
                    "name": repo_owner or os.getenv("GITHUB_USERNAME", "")
                },
                "head_commit": {
                    "id": stable_commit   # ✅ FIXED HERE
                },
            }

            # ✅ Send to API
            response = requests.post(API_URL, json=payload)

            print(f"📡 API Status: {response.status_code}")

            last_commit = stable_commit

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(5)
