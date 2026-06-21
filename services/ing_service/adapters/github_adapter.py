
import requests
from loguru import logger
from .base_adapter import BaseAdapter
from datetime import datetime
import uuid


class GitHubAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        return "repository" in event

    def transform(self, event: dict) -> dict:
        try:
            # ✅ Extract fields safely
            repo_name = event.get("repository", {}).get("name")

            owner = (
                event.get("repository", {}).get("owner", {}).get("login")
                or event.get("pusher", {}).get("name")
            )

            commit_id = event.get("head_commit", {}).get("id")

            # ✅ Validate inputs
            if not repo_name or not owner or not commit_id:
                logger.error("❌ Missing required GitHub fields")

                return self._safe_response(repo_name, reason="missing_fields")

            # ✅ Construct API URL
            url = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{commit_id}"

            logger.info(f"🔗 Calling GitHub API → {url}")

            commit_details = {}

            try:
                response = requests.get(url, timeout=10)

                logger.info(f"📡 GitHub API Status: {response.status_code}")
                logger.info(f"📡 Response Preview: {response.text[:200]}")

                if response.status_code == 200:
                    commit_details = response.json()
                else:
                    logger.warning(
                        f"⚠️ GitHub API returned {response.status_code}"
                    )

            except Exception as api_error:
                logger.error(f"❌ GitHub API call failed: {str(api_error)}")

            # ✅ Safe extraction (NO CRASHES)
            commit_message = None
            files_changed = []

            if isinstance(commit_details, dict):

                # ✅ Commit message
                commit_obj = commit_details.get("commit")
                if isinstance(commit_obj, dict):
                    commit_message = commit_obj.get("message")

                # ✅ File changes
                files = commit_details.get("files") or []

                if isinstance(files, list):
                    for file in files:
                        if isinstance(file, dict):
                            files_changed.append({
                                "filename": file.get("filename"),
                                "additions": file.get("additions"),
                                "deletions": file.get("deletions"),
                                "changes": file.get("changes"),
                                "patch": file.get("patch")
                            })

            # ✅ Final safe response (ALWAYS RETURNS)
            return {
                "event_id": str(uuid.uuid4()),
                "event_type": "code_commit",
                "source": "github",
                "timestamp": event.get("head_commit", {}).get(
                    "timestamp", str(datetime.utcnow())
                ),
                "service": repo_name,
                "change_reference": {
                    "commit_id": commit_id,
                    "author": owner,
                    "repo": repo_name
                },
                "metadata": {
                    "message": commit_message,
                    "files_changed": files_changed,
                    "raw_event": event
                }
            }

        except Exception as e:
            logger.exception(f"❌ Fatal error in GitHubAdapter: {str(e)}")

            return self._safe_response("unknown", reason=str(e))

    # ✅ Fallback safe response (never break API)
    def _safe_response(self, repo_name, reason="unknown"):
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "code_commit",
            "source": "github",
            "timestamp": str(datetime.utcnow()),
            "service": repo_name,
            "change_reference": {},
            "metadata": {
                "error": reason
            }
        }
