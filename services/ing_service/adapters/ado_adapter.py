
import os
import uuid
from datetime import datetime, timezone

from loguru import logger

from .base_adapter import BaseAdapter


class ADOAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        return "resource" in event and "eventType" in event

    def transform(self, event: dict) -> dict:
        try:
            resource = event.get("resource", {}) or {}
            repository = resource.get("repository", {}) or {}
            commits = resource.get("commits") or []
            commit = commits[0] if commits else {}
            author = commit.get("author", {}) or {}
            repo_name = repository.get("name") or "unknown-repo"
            repo_owner = repository.get("project", {}).get("name") or "unknown-project"
            commit_id = commit.get("commitId")
            author_name = author.get("name") or commit.get("author") or "unknown"
            branch = resource.get("refName") or resource.get("ref") or resource.get("branch") or "main"
            event_type = "code_commit"
            change_type = "code"

            event_id = str(uuid.uuid4())
            correlation_id = event_id
            tenant_id = os.getenv("TENANT_ID", "bank-uk-01")
            timestamp = datetime.now(timezone.utc).isoformat()
            environment = os.getenv("ENVIRONMENT", "dev")
            application = repo_name.split("_")[0] if "_" in repo_name else repo_name
            service = application

            classification = {
                "materiality": "low",
                "risk_tags": [],
                "change_scope": [repo_name],
                "requires_impact_analysis": True,
            }

            metadata = {
                "raw_event": event,
                "event_type": event.get("eventType"),
                "repository": repo_name,
                "commit_count": len(commits),
            }

            return {
                "event_id": event_id,
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "change_type": change_type,
                "source_system": "azure_devops",
                "timestamp": timestamp,
                "environment": environment,
                "application": application,
                "service": service,
                "repository": {
                    "name": repo_name,
                    "owner": repo_owner,
                    "provider": "azure_devops",
                },
                "change_reference": {
                    "commit_id": commit_id,
                    "author": author_name,
                    "branch": branch,
                    "repo": repo_name,
                },
                "classification": classification,
                "metadata": metadata,
                "artifact_refs": {
                    "patch_ref": f"obs://artifacts/patches/{commit_id}.patch" if commit_id else "obs://artifacts/patches/unknown.patch",
                    "raw_event_ref": f"obs://raw-events/azure_devops/{event_id}.json",
                },
            }
        except Exception as exc:
            logger.exception(f"❌ ADO adapter error: {exc}")
            return {"error": str(exc), "raw_event": event}
