
import requests
import json

URL = "http://localhost:8000/webhook/github"

# ✅ Test GitHub
github_payload = {
    
    "repository": {
        "name": "bank-of-anthos_Test_Ayush",
        "owner": {
            "login": "singhayush1421"
        }
    },
    "pusher": {
        "name": "singhayush1421"
    },

    "head_commit": {
        "id": "7b58b0b2045f05d882484bf99f7ccc27610e41f8",
        "timestamp": "2026-06-21T10:00:00Z"
    }
}

# ✅ Test Jenkins
jenkins_payload = {
    "job": {"name": "ci-pipeline"},
    "build": {
        "number": 45,
        "status": "SUCCESS",
        "branch": "main"
    }
}

# ✅ Test ADO
ado_payload = {
    "eventType": "git.push",
    "resource": {
        "repository": {"name": "ado-repo"},
        "commits": [
            {
                "commitId": "ado456",
                "author": {"name": "Ayush"}
            }
        ]
    }
}


def test(payload, name):
    print(f"\n--- Testing {name} ---")
    response = requests.post(URL, json=payload)
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    test(github_payload, "GitHub")
    test(jenkins_payload, "Jenkins")
    test(ado_payload, "ADO")
