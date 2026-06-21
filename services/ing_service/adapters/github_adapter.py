
from .base_adapter import BaseAdapter
from datetime import datetime
import uuid


class GitHubAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        return "repository" in event

    def transform(self, event: dict) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "code_commit",
            "source": "github",
            "timestamp": event.get("head_commit", {}).get(
                "timestamp", str(datetime.utcnow())
            ),
            "service": event.get("repository", {}).get("name"),
            "change_reference": {
                "commit_id": event.get("head_commit", {}).get("id"),
                "author": event.get("pusher", {}).get("name"),
                "repo": event.get("repository", {}).get("name"),
            },
            "metadata": event
        }
