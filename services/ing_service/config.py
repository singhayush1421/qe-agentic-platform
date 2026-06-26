import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


def _load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    if load_dotenv is not None:
        load_dotenv(dotenv_path=str(ENV_FILE), override=False)
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


def get_setting(name: str, default=None, cast=None):
    value = os.getenv(name, default)
    if cast is None:
        return value
    if cast is bool:
        return str(value).lower() in {"1", "true", "yes", "on"}
    if cast is int:
        return int(value)
    return cast(value)


def get_repo_config() -> dict:
    repo_path = os.getenv("REPO_BASE_PATH") or os.getenv("AUTO_TRIGGER_REPO_PATH") or str(BASE_DIR)
    return {
        "repo_path": repo_path,
        "repo_name": get_setting("AUTO_TRIGGER_REPO_NAME") or os.path.basename(os.path.abspath(repo_path)),
        "repo_owner": get_setting("AUTO_TRIGGER_REPO_OWNER") or get_setting("GITHUB_REPO_OWNER") or get_setting("GITHUB_USERNAME", ""),
        "tenant_id": get_setting("TENANT_ID", ""),
        "environment": get_setting("ENVIRONMENT", ""),
        "api_url": get_setting("AUTO_TRIGGER_API_URL", ""),
        "ref": get_setting("AUTO_TRIGGER_REF", ""),
    }


def get_db_config() -> dict:
    return {
        "host": get_setting("POSTGRES_HOST", "localhost"),
        "database": get_setting("POSTGRES_DB", "events_db"),
        "user": get_setting("POSTGRES_USER", "postgres"),
        "password": get_setting("POSTGRES_PASSWORD", "postgres"),
        "port": get_setting("POSTGRES_PORT", 5432, int),
    }


def get_service_mapping() -> dict:
    raw_mapping = get_setting("GITHUB_SERVICE_MAPPING", "")
    if not raw_mapping:
        return {}

    try:
        parsed = json.loads(raw_mapping)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
