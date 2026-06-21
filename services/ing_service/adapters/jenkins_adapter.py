
from .base_adapter import BaseAdapter
from datetime import datetime
import uuid


class JenkinsAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        # Jenkins events often contain "build" or "job"
        return "build" in event or "job" in event

    def transform(self, event: dict) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "ci_build",
            "source": "jenkins",
            "timestamp": str(datetime.utcnow()),
            "service": event.get("job", {}).get("name"),
            "change_reference": {
                "build_id": event.get("build", {}).get("number"),
                "status": event.get("build", {}).get("status"),
                "branch": event.get("build", {}).get("branch"),
            },
            "metadata": event
        }
