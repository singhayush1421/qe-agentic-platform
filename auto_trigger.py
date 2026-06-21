
import subprocess
import time
import requests

API_URL = "http://127.0.0.1:8000/webhook/github"


def get_latest_commit():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd="C:/Users/ASING442/bank-of-anthos_Test_Ayush"
    ).decode().strip()


last_commit = None

print("🚀 Auto trigger started...")

while True:
    try:
        current_commit = get_latest_commit()

        # ✅ Only trigger when commit changes
        if current_commit != last_commit:

            print(f"\n✅ New commit detected: {current_commit}")

            # ✅ WAIT for repo + git consistency
            time.sleep(5)

            # ✅ Re-check stability
            new_commit = get_latest_commit()

            if new_commit != current_commit:
                print("⚠️ Commit unstable, skipping...")
                continue

            # ✅ Payload
            payload = {
                "ref": "refs/heads/main",
                "repository": {
                    "name": "bank-of-anthos_Test_Ayush",
                    "owner": {"login": "singhayush1421"}
                },
                "pusher": {"name": "singhayush1421"},
                "head_commit": {
                    "id": current_commit
                }
            }

            # ✅ Call API
            response = requests.post(API_URL, json=payload)

            print("📡 API Status:", response.status_code)

            last_commit = current_commit

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(5)
