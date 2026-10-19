"""The same code must serve all three levels by changing environment variables only."""

import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

APP_DIR = Path(__file__).resolve().parents[2]

PROBE = """
import json, django
django.setup()
from django.conf import settings
print(json.dumps({
    "engine": settings.DATABASES["default"]["ENGINE"],
    "host": settings.DATABASES["default"].get("HOST", ""),
    "default_storage": settings.STORAGES["default"]["BACKEND"],
    "static_storage": settings.STORAGES["staticfiles"]["BACKEND"],
    "static_url": settings.STATIC_URL,
    "media_url": settings.MEDIA_URL,
    "debug": settings.DEBUG,
}))
"""

# DJANGO_ENV_FILE points at an empty file so a developer's own .env can't leak in.
BASE_ENV = {"SECRET_KEY": "test", "DJANGO_SETTINGS_MODULE": "pcm.settings", "DJANGO_ENV_FILE": os.devnull}
DEPLOY_KEYS = [
    "DEBUG", "SECRET_KEY", "USE_S3", "DATABASE_URL", "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_REGION_NAME", "AWS_S3_CUSTOM_DOMAIN", "ALLOWED_HOSTS",
]


def load_settings(**overrides):
    env = {k: v for k, v in os.environ.items() if k not in DEPLOY_KEYS}
    env.update(BASE_ENV, **overrides)
    result = subprocess.run(
        [sys.executable, "-c", PROBE], cwd=APP_DIR, env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout.strip().splitlines()[-1])


class LevelSettingsTests(SimpleTestCase):
    def test_level_1_local_files_and_sqlite(self):
        s = load_settings(USE_S3="false", DATABASE_URL="sqlite:///level1.sqlite3")
        self.assertEqual(s["engine"], "django.db.backends.sqlite3")
        self.assertEqual(s["default_storage"], "django.core.files.storage.FileSystemStorage")
        self.assertEqual(s["static_url"], "/static/")
        self.assertEqual(s["media_url"], "/media/")

    def test_level_2_s3_and_sqlite(self):
        s = load_settings(
            USE_S3="true",
            AWS_STORAGE_BUCKET_NAME="pcm-bucket",
            AWS_S3_REGION_NAME="us-east-1",
            DATABASE_URL="sqlite:///level2.sqlite3",
        )
        self.assertEqual(s["engine"], "django.db.backends.sqlite3")
        self.assertEqual(s["default_storage"], "storages.backends.s3.S3Storage")
        self.assertEqual(s["static_storage"], "storages.backends.s3.S3Storage")
        self.assertEqual(s["static_url"], "https://pcm-bucket.s3.us-east-1.amazonaws.com/static/")
        self.assertEqual(s["media_url"], "https://pcm-bucket.s3.us-east-1.amazonaws.com/media/")

    def test_level_3_s3_and_postgres(self):
        s = load_settings(
            USE_S3="true",
            AWS_STORAGE_BUCKET_NAME="pcm-bucket",
            AWS_S3_REGION_NAME="us-east-1",
            DATABASE_URL="postgres://u:p@pcm-db.abc123.us-east-1.rds.amazonaws.com:5432/pcm?sslmode=require",
        )
        self.assertEqual(s["engine"], "django.db.backends.postgresql")
        self.assertEqual(s["host"], "pcm-db.abc123.us-east-1.rds.amazonaws.com")

    def test_debug_defaults_to_off(self):
        self.assertFalse(load_settings()["debug"])

    def test_missing_secret_key_fails_when_debug_off(self):
        with self.assertRaises(AssertionError) as ctx:
            load_settings(SECRET_KEY="")
        self.assertIn("SECRET_KEY", str(ctx.exception))

    def test_s3_without_bucket_fails_loudly(self):
        with self.assertRaises(AssertionError) as ctx:
            load_settings(USE_S3="true")
        self.assertIn("AWS_STORAGE_BUCKET_NAME", str(ctx.exception))
