import importlib
import os
import unittest


class GitHubAdapterDynamicConfigTests(unittest.TestCase):
    def test_repo_base_path_uses_environment_override(self):
        os.environ["REPO_BASE_PATH"] = "/tmp/repos"

        import services.ing_service.adapters.github_adapter as github_adapter_module

        module = importlib.reload(github_adapter_module)

        self.assertEqual(module.get_repo_base_path(), "/tmp/repos")

    def test_service_details_are_derived_from_repository_event(self):
        os.environ.pop("GITHUB_SERVICE_MAPPING", None)

        import services.ing_service.adapters.github_adapter as github_adapter_module

        module = importlib.reload(github_adapter_module)

        config = module.get_service_config("my-app_repo", "octocat")

        self.assertEqual(config["application"], "my-app")
        self.assertEqual(config["service"], "my-app")

    def test_repo_path_uses_direct_repo_root_when_configured(self):
        os.environ.pop("REPO_BASE_PATH", None)
        os.environ["AUTO_TRIGGER_REPO_PATH"] = "/tmp/my-repo"

        import services.ing_service.adapters.github_adapter as github_adapter_module

        module = importlib.reload(github_adapter_module)

        self.assertEqual(module.get_repo_path("my-repo", "octocat"), "/tmp/my-repo")


if __name__ == "__main__":
    unittest.main()
