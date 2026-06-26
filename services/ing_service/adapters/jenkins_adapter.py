
import os
import uuid
from datetime import datetime, timezone

from loguru import logger

from .base_adapter import BaseAdapter


class JenkinsAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        return "build" in event or "job" in event

    def transform(self, event: dict) -> dict:
        try:
            job = event.get("job", {}) or {}
            build = event.get("build", {}) or {}
            repository = event.get("repository", {}) or {}
            job_name = job.get("name") or "unknown-job"
            repo_name = repository.get("name") or job_name
            build_number = build.get("number")
            status = build.get("status") or "UNKNOWN"
            branch = build.get("branch") or build.get("ref") or "main"

            event_id = str(uuid.uuid4())
            correlation_id = event_id
            tenant_id = os.getenv("TENANT_ID", "bank-uk-01")
            timestamp = datetime.now(timezone.utc).isoformat()
            environment = os.getenv("ENVIRONMENT", "dev")
            application = repo_name.split("_")[0] if "_" in repo_name else repo_name
            service = job_name

            classification = {
                "materiality": "medium" if status == "SUCCESS" else "low",
                "risk_tags": [],
                "change_scope": [job_name],
                "requires_impact_analysis": True,
            }

            metadata = {
                "raw_event": event,
                "job_name": job_name,
                "build_status": status,
            }

            return {
                "event_id": event_id,
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
                "event_type": "ci_build",
                "change_type": "ci",
                "source_system": "jenkins",
                "timestamp": timestamp,
                "environment": environment,
                "application": application,
                "service": service,
                "repository": {
                    "name": repo_name,
                    "owner": repository.get("owner", {}).get("name") or "unknown-owner",
                    "provider": "jenkins",
                },
                "change_reference": {
                    "build_id": build_number,
                    "status": status,
                    "branch": branch,
                },
                "classification": classification,
                "metadata": metadata,
                "artifact_refs": {
                    "patch_ref": f"obs://artifacts/builds/{build_number}" if build_number is not None else "obs://artifacts/builds/unknown",
                    "raw_event_ref": f"obs://raw-events/jenkins/{event_id}.json",
                },
            }
        except Exception as exc:
            logger.exception(f"❌ Jenkins adapter error: {exc}")
            return {"error": str(exc), "raw_event": event}
