
import os
import subprocess
import uuid
from datetime import datetime, timezone

from loguru import logger

from .base_adapter import BaseAdapter
from ..config import get_repo_config, get_service_mapping


def get_repo_base_path() -> str:
    return get_repo_config()["repo_path"]


def get_service_config(repo_name: str, owner: str | None = None) -> dict:
    configured_mapping = get_service_mapping()
    repo_key = f"{owner}/{repo_name}" if owner else repo_name

    if repo_key in configured_mapping:
        return configured_mapping[repo_key]

    if repo_name in configured_mapping:
        return configured_mapping[repo_name]

    application = repo_name.split("_")[0] if "_" in repo_name else repo_name

    return {
        "application": application,
        "service": application,
    }


def get_repo_path(repo_name: str, owner: str | None = None) -> str:
    repo_root = get_repo_base_path() or os.getcwd()

    if os.path.exists(os.path.join(repo_root, ".git")) or os.path.basename(repo_root) == repo_name:
        return repo_root

    candidates = []
    if repo_root:
        candidates.append(os.path.join(repo_root, repo_name))
    if owner and repo_root:
        candidates.append(os.path.join(repo_root, owner, repo_name))

    for candidate in candidates:
        if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, ".git")):
            return candidate

    return candidates[0] if candidates else os.path.join(repo_root, repo_name)


class GitHubAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        return "repository" in event

    def transform(self, event: dict) -> dict:
        try:
            # -----------------------------------
            # ✅ BASIC INPUT
            # -----------------------------------
            repo_name = event.get("repository", {}).get("name")

            owner = (
                event.get("repository", {}).get("owner", {}).get("login")
                or event.get("pusher", {}).get("name")
            )

            commit_id = event.get("head_commit", {}).get("id")

            if not repo_name or not commit_id:
                raise ValueError("Missing repo_name or commit_id")

            # -----------------------------------
            # ✅ IDENTIFIERS
            # -----------------------------------
            event_id = str(uuid.uuid4())
            correlation_id = event_id
            tenant_id = os.getenv("TENANT_ID", "bank-uk-01")

            # -----------------------------------
            # ✅ TIMESTAMP
            # -----------------------------------
            timestamp = datetime.now(timezone.utc).isoformat()

            # -----------------------------------
            # ✅ BRANCH + ENVIRONMENT
            # -----------------------------------
            ref = event.get("ref", "refs/heads/main")
            branch = ref.split("/")[-1]

            if branch in ["main", "develop"]:
                environment = "dev"
            elif branch in ["test", "qa"]:
                environment = "test"
            elif branch in ["staging", "preprod"]:
                environment = "preprod"
            elif branch in ["prod", "release"]:
                environment = "prod"
            else:
                environment = "dev"

            # ✅ override support
            environment = os.getenv("ENVIRONMENT", environment)

            # -----------------------------------
            # ✅ COMMIT URL
            # -----------------------------------
            commit_url = f"https://github.com/{owner}/{repo_name}/commit/{commit_id}"

            # -----------------------------------
            # ✅ APP + SERVICE
            # -----------------------------------
            mapping = get_service_config(repo_name, owner)
            application = mapping.get("application") or repo_name.split("_")[0]
            service = mapping.get("service", application)

            # -----------------------------------
            # ✅ INIT VALUES
            # -----------------------------------
            commit_message = None
            files_changed = []
            total_additions = 0
            total_deletions = 0
            contains_binary = False

            # -----------------------------------
            # ✅ LOCAL GIT ENRICHMENT
            # -----------------------------------
            try:
                repo_path = get_repo_path(repo_name, owner)

                logger.info(f"✅ Using local repo: {repo_path}")

                # ✅ commit message
                commit_message = subprocess.check_output(
                    ["git", "log", "-1", "--pretty=%B", commit_id],
                    cwd=repo_path,
                    timeout=5
                ).decode().strip()

                # ✅ diff stats
                diff_output = subprocess.check_output(
                    ["git", "show", "--numstat", "--format=", commit_id],
                    cwd=repo_path,
                    timeout=5
                ).decode().splitlines()

                for line in diff_output:
                    parts = line.split("\t")
                    if len(parts) == 3:
                        additions, deletions, filename = parts

                        is_binary = not additions.isdigit()

                        add_val = int(additions) if additions.isdigit() else 0
                        del_val = int(deletions) if deletions.isdigit() else 0

                        if is_binary:
                            contains_binary = True

                        total_additions += add_val
                        total_deletions += del_val

                        ext = os.path.splitext(filename)[1]

                        # ✅ smarter impact hint
                        if is_binary:
                            impact_hint = "binary_change"
                        elif "test" in filename.lower():
                            impact_hint = "test_change"
                        elif filename.endswith((".yaml", ".yml", ".json")):
                            impact_hint = "config_change"
                        else:
                            impact_hint = "code_change"

                        if add_val > 0 and del_val > 0:
                            change_status = "modified"
                        elif add_val > 0:
                            change_status = "added"
                        elif del_val > 0:
                            change_status = "deleted"
                        else:
                            change_status = "modified"

                        files_changed.append({
                            "path": filename,
                            "extension": ext,
                            "change_status": change_status,
                            "additions": add_val,
                            "deletions": del_val,
                            "changes": add_val + del_val,
                            "is_binary": is_binary,
                            "is_test_file": "test" in filename.lower(),
                            "impact_hint": impact_hint
                        })

                # ✅ Service detection
                for f in files_changed:
                    path = f["path"].lower()

                    if "payment" in path:
                        service = "payment-service"
                        break
                    elif "auth" in path:
                        service = "auth-service"
                        break

                logger.info(f"✅ Files processed: {len(files_changed)}")

            except Exception as e:
                logger.warning(f"⚠️ Git enrichment failed: {e}")

            # -----------------------------------
            # ✅ HANDLE EMPTY FILE CASE
            # -----------------------------------
            if not files_changed:
                logger.warning("⚠️ No file changes detected")

            # -----------------------------------
            # ✅ SMART MATERIALITY
            # -----------------------------------
            total_changes = total_additions + total_deletions

            if total_changes > 50:
                materiality = "high"
            elif total_changes > 10:
                materiality = "medium"
            else:
                materiality = "low"

            # -----------------------------------
            # ✅ CLASSIFICATION
            # -----------------------------------
            classification = {
                "materiality": materiality,
                "risk_tags": ["binary_change"] if contains_binary else [],
                "change_scope": [f["path"] for f in files_changed],
                "requires_impact_analysis": total_changes > 0
            }

            # -----------------------------------
            # ✅ METADATA SUMMARY
            # -----------------------------------
            metadata_summary = {
                "files_changed_count": len(files_changed),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "contains_binary_change": contains_binary
            }

            # -----------------------------------
            # ✅ FINAL EVENT
            # -----------------------------------
            transformed_event = {
                "event_id": event_id,
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
                "event_type": "code_commit",
                "change_type": "code",
                "source_system": "github",
                "timestamp": timestamp,
                "environment": environment,

                "application": application,
                "service": service,

                "repository": {
                    "name": repo_name,
                    "owner": owner,
                    "provider": "github"
                },

                "change_reference": {
                    "commit_id": commit_id,
                    "author": owner,
                    "branch": branch,
                    "commit_url": commit_url
                },

                "classification": classification,

                "metadata": {
                    "message": commit_message,
                    **metadata_summary,
                    "files_changed": files_changed
                },

                "artifact_refs": {
                    "patch_ref": f"obs://artifacts/patches/{commit_id}.patch",
                    "raw_event_ref": f"obs://raw-events/github/{event_id}.json"
                }
            }

            logger.info(f"✅ Event transformed: {commit_id}")

            return transformed_event

        except Exception as e:
            logger.exception(f"❌ Fatal adapter error: {e}")

            return {
                "error": str(e),
                "raw_event": event
            }
