
import requests
from loguru import logger
from .base_adapter import BaseAdapter
from datetime import datetime
import uuid
import subprocess


class GitHubAdapter(BaseAdapter):

    def can_handle(self, event: dict) -> bool:
        return "repository" in event

    def transform(self, event: dict) -> dict:
        try:
            # ✅ Extract basic fields
            repo_name = event.get("repository", {}).get("name")

            owner = (
                event.get("repository", {}).get("owner", {}).get("login")
                or event.get("pusher", {}).get("name")
            )

            commit_id = event.get("head_commit", {}).get("id")

            if not repo_name or not owner or not commit_id:
                logger.error("❌ Missing required GitHub fields")
                return self._safe_response(repo_name, reason="missing_fields")

            # ✅ GitHub API URL (optional use only)
            url = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{commit_id}"
            logger.info(f"🔗 GitHub API URL → {url}")

            commit_message = None
            files_changed = []
            patch_preview = None

            # ✅ ✅ PRIMARY: LOCAL GIT (DETAILED EXTRACTION ✅)
            try:
                logger.info("✅ Using local git for commit details")

                # ✅ Commit message
                commit_message = subprocess.check_output(
                    ["git", "log", "-1", "--pretty=%B", commit_id],
                    cwd="C:/Users/ASING442/bank-of-anthos_Test_Ayush"
                ).decode().strip()

                # ✅ Detailed file changes (additions/deletions)
                diff_output = subprocess.check_output(
                    ["git", "show", "--numstat", "--format=", commit_id],
                    cwd="C:/Users/ASING442/bank-of-anthos_Test_Ayush"
                ).decode().splitlines()

                for line in diff_output:
                    parts = line.split("\t")
                    if len(parts) == 3:
                        additions = parts[0]
                        deletions = parts[1]
                        filename = parts[2]

                        files_changed.append({
                            "filename": filename,
                            "additions": int(additions) if additions.isdigit() else 0,
                            "deletions": int(deletions) if deletions.isdigit() else 0,
                            "changes": (
                                int(additions) + int(deletions)
                                if additions.isdigit() and deletions.isdigit()
                                else 0
                            )
                        })

                logger.info(f"✅ Files detected with stats: {files_changed}")

                # ✅ OPTIONAL: Full patch (diff content)
                try:
                    patch_output = subprocess.check_output(
                        ["git", "show", commit_id],
                        cwd="C:/Users/ASING442/bank-of-anthos_Test_Ayush"
                    ).decode()

                    # Limit size for safety
                    patch_preview = patch_output[:1000]

                    logger.info("✅ Patch extracted (truncated)")

                except Exception as patch_error:
                    logger.warning(f"⚠️ Patch extraction failed: {patch_error}")

            except Exception as local_error:
                logger.error(f"❌ Local git failed: {local_error}")

            # ✅ OPTIONAL: GitHub API enrichment (non-blocking)
            try:
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    logger.info("✅ GitHub API enrichment successful")
                else:
                    logger.warning(
                        f"⚠️ GitHub API unavailable (status {response.status_code})"
                    )

            except Exception as api_error:
                logger.warning(f"⚠️ GitHub API skipped: {api_error}")

            # ✅ FINAL EVENT
            return {
                "event_id": str(uuid.uuid4()),
                "event_type": "code_commit",
                "source": "github",
                "timestamp": event.get(
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
                    "patch": patch_preview,   # ✅ Optional diff preview
                    "raw_event": event
                }
            }

        except Exception as e:
            logger.exception(f"❌ Fatal error in GitHubAdapter: {str(e)}")

            return self._safe_response("unknown", reason=str(e))

    # ✅ Safe fallback
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
