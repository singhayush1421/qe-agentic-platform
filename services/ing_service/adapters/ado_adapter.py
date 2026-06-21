
from .base_adapter import BaseAdapter
from datetime import datetime
import uuid


class ADOAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        # ADO events often have "resource" and "eventType"
        return "resource" in event and "eventType" in event

    def transform(self, event: dict) -> dict:
        resource = event.get("resource", {})

        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "code_commit",
            "source": "azure_devops",
            "timestamp": str(datetime.utcnow()),
            "service": resource.get("repository", {}).get("name"),
            "change_reference": {
                "commit_id": resource.get("commits", [{}])[0].get("commitId"),
                "author": resource.get("commits", [{}])[0].get("author", {}).get("name"),
                "repo": resource.get("repository", {}).get("name"),
            },
            "metadata": event
        }
