import unittest

from services.ing_service.adapters.ado_adapter import ADOAdapter
from services.ing_service.adapters.jenkins_adapter import JenkinsAdapter


class AdapterCanonicalModelTests(unittest.TestCase):
    def test_ado_adapter_emits_canonical_event_shape(self):
        adapter = ADOAdapter()
        payload = {
            "eventType": "git.push",
            "resource": {
                "repository": {"name": "ado-repo"},
                "commits": [
                    {"commitId": "ado456", "author": {"name": "Ayush"}}
                ],
            },
        }

        event = adapter.transform(payload)

        self.assertEqual(event["source_system"], "azure_devops")
        self.assertEqual(event["event_type"], "code_commit")
        self.assertEqual(event["change_type"], "code")
        self.assertEqual(event["repository"]["name"], "ado-repo")
        self.assertEqual(event["change_reference"]["commit_id"], "ado456")
        self.assertEqual(event["change_reference"]["author"], "Ayush")
        self.assertIn("raw_event", event["metadata"])

    def test_jenkins_adapter_emits_canonical_event_shape(self):
        adapter = JenkinsAdapter()
        payload = {
            "job": {"name": "ci-pipeline"},
            "build": {
                "number": 45,
                "status": "SUCCESS",
                "branch": "main",
            },
        }

        event = adapter.transform(payload)

        self.assertEqual(event["source_system"], "jenkins")
        self.assertEqual(event["event_type"], "ci_build")
        self.assertEqual(event["change_type"], "ci")
        self.assertEqual(event["service"], "ci-pipeline")
        self.assertEqual(event["change_reference"]["build_id"], 45)
        self.assertEqual(event["change_reference"]["status"], "SUCCESS")
        self.assertIn("raw_event", event["metadata"])


if __name__ == "__main__":
    unittest.main()
