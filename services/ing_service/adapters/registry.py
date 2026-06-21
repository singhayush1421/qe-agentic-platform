
from .github_adapter import GitHubAdapter
from .jenkins_adapter import JenkinsAdapter
from .ado_adapter import ADOAdapter
from loguru import logger
ADAPTERS = [
    GitHubAdapter(),
    JenkinsAdapter(),
    ADOAdapter()
]



def get_adapter(event: dict):
    for adapter in ADAPTERS:
        if adapter.can_handle(event):
            logger.info(f"✅ Adapter selected: {adapter.__class__.__name__}")
            return adapter

    logger.warning("❌ No adapter matched")
    return None



