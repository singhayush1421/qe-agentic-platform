import importlib
import os
import unittest


class IngestEventDbConfigTests(unittest.TestCase):
    def test_db_config_uses_environment_variables(self):
        os.environ["POSTGRES_HOST"] = "db.internal"
        os.environ["POSTGRES_DB"] = "events_test"
        os.environ["POSTGRES_USER"] = "app_user"
        os.environ["POSTGRES_PASSWORD"] = "super-secret"

        import services.ing_service.ingest_event as ingest_event_module

        module = importlib.reload(ingest_event_module)

        self.assertEqual(
            module.get_db_config(),
            {
                "host": "db.internal",
                "database": "events_test",
                "user": "app_user",
                "password": "super-secret",
                "port": 5432,
            },
        )

    def test_db_config_loads_values_from_env_file(self):
        for key in ["POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT"]:
            os.environ.pop(key, None)

        import services.ing_service.config as config_module

        module = importlib.reload(config_module)

        db_config = module.get_db_config()

        self.assertEqual(db_config["host"], "localhost")
        self.assertEqual(db_config["database"], "events_db")
        self.assertEqual(db_config["user"], "postgres")
        self.assertEqual(db_config["password"], "Alohomora@1421")
        self.assertEqual(db_config["port"], 5432)


if __name__ == "__main__":
    unittest.main()
