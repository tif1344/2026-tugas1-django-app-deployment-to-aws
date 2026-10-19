"""
Django settings for the PCM website.

Every deployment-specific value is read from environment variables (or from
an `.env` file next to manage.py). Moving between assignment levels only
requires changing `.env` — never this file:

    Level 1 (EC2)            USE_S3=false, DATABASE_URL unset  -> local files + SQLite
    Level 2 (EC2 + S3)       USE_S3=true,  DATABASE_URL unset  -> S3 files + SQLite
    Level 3 (EC2 + S3 + RDS) USE_S3=true,  DATABASE_URL=postgres://...  -> S3 + RDS
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Variables already present in the process environment win over `.env`.
load_dotenv(os.environ.get("DJANGO_ENV_FILE", BASE_DIR / ".env"))


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Core -------------------------------------------------------------------

DEBUG = env_bool("DEBUG", False)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is false.")
    SECRET_KEY = "django-insecure-local-development-only"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Nginx sets X-Forwarded-Proto, so Django knows when the original request was HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Only enable once the site is served over HTTPS (bonus task).
SESSION_COOKIE_SECURE = env_bool("SECURE_COOKIES", False)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "storages",
    "website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pcm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "website.context_processors.site_profile",
            ],
        },
    },
]

WSGI_APPLICATION = "pcm.wsgi.application"


# --- Database (Level 3 switches this to RDS PostgreSQL) ----------------------
# Example: DATABASE_URL=postgres://pcm_admin:password@pcm-db.xxxx.rds.amazonaws.com:5432/pcm?sslmode=require

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalisation ----------------------------------------------------

LANGUAGE_CODE = "id"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Jakarta")  # WIB (Kartasura, Jawa Tengah)
USE_I18N = True
USE_TZ = True


# --- Static & media files (Level 2 switches these to S3) ---------------------

STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

USE_S3 = env_bool("USE_S3", False)

if USE_S3:
    # Credentials are NOT configured here: on EC2, boto3 picks them up
    # automatically from the IAM role attached to the instance.
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "")
    if not AWS_STORAGE_BUCKET_NAME or not AWS_S3_REGION_NAME:
        raise ImproperlyConfigured(
            "USE_S3=true requires AWS_STORAGE_BUCKET_NAME and AWS_S3_REGION_NAME."
        )
    # Optional: a CloudFront domain in front of the bucket (bonus task).
    AWS_S3_CUSTOM_DOMAIN = os.environ.get(
        "AWS_S3_CUSTOM_DOMAIN",
        f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com",
    )

    s3_options = {
        "bucket_name": AWS_STORAGE_BUCKET_NAME,
        "region_name": AWS_S3_REGION_NAME,
        "custom_domain": AWS_S3_CUSTOM_DOMAIN,
        # Buckets use "Bucket owner enforced" ownership, so ACLs are disabled;
        # public read access comes from the bucket policy instead.
        "default_acl": None,
        "querystring_auth": False,
    }
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {**s3_options, "location": "media", "file_overwrite": False},
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {**s3_options, "location": "static"},
        },
    }
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    STATIC_URL = "/static/"
    MEDIA_URL = "/media/"

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


# --- Misc --------------------------------------------------------------------

# Public page showing which level is active; useful for grading.
STATUS_PAGE_ENABLED = env_bool("STATUS_PAGE_ENABLED", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
