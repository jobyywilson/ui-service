import unittest

from app.config import (
    ConfigurationError,
    get_database_settings,
    get_server_settings,
    get_storage_settings,
)


class ConfigurationTests(unittest.TestCase):
    def test_database_url_takes_precedence(self):
        settings = get_database_settings({"DATABASE_URL": "postgresql://example"})

        self.assertEqual(settings.database_url, "postgresql://example")

    def test_requires_separate_connection_credentials(self):
        with self.assertRaisesRegex(ConfigurationError, "DB_HOST"):
            get_database_settings({})

    def test_rejects_invalid_server_port(self):
        with self.assertRaisesRegex(ConfigurationError, "PORT must be an integer"):
            get_server_settings({"PORT": "invalid"})

    def test_loads_storage_settings(self):
        settings = get_storage_settings(
            {
                "SUPABASE_URL": "https://project.supabase.co/",
                "SUPABASE_SECRET_KEY": "sb_secret_example",
                "SUPABASE_STORAGE_BUCKET": "case-files",
            }
        )

        self.assertEqual(settings.supabase_url, "https://project.supabase.co")
        self.assertEqual(settings.api_key, "sb_secret_example")
        self.assertEqual(settings.bucket, "case-files")

    def test_requires_storage_credentials(self):
        with self.assertRaisesRegex(ConfigurationError, "SUPABASE_URL"):
            get_storage_settings({})
