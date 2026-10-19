"""Inspect the running deployment so the /status/ page can show which level is active."""

import functools
import socket
import urllib.request

from django.conf import settings
from django.db import connection

IMDS = "http://169.254.169.254/latest"


@functools.lru_cache(maxsize=1)
def ec2_metadata():
    """Return instance details via IMDSv2, or None when not running on EC2."""
    try:
        token_request = urllib.request.Request(
            f"{IMDS}/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = urllib.request.urlopen(token_request, timeout=0.5).read().decode()

        def get(path):
            request = urllib.request.Request(
                f"{IMDS}/meta-data/{path}", headers={"X-aws-ec2-metadata-token": token}
            )
            return urllib.request.urlopen(request, timeout=0.5).read().decode()

        return {
            "instance_id": get("instance-id"),
            "instance_type": get("instance-type"),
            "availability_zone": get("placement/availability-zone"),
        }
    except OSError:
        return None


def deployment_info():
    db = connection.settings_dict
    is_postgres = connection.vendor == "postgresql"
    db_host = db.get("HOST") or ""
    uses_rds = is_postgres and db_host.endswith(".rds.amazonaws.com")

    if settings.USE_S3 and uses_rds:
        level = "3"
    elif settings.USE_S3 and not is_postgres:
        level = "2"
    elif not settings.USE_S3 and not is_postgres:
        level = "1"
    else:
        level = None  # e.g. PostgreSQL without S3 — not one of the assignment levels

    return {
        "level": level,
        "hostname": socket.gethostname(),
        "ec2": ec2_metadata(),
        "database_vendor": connection.vendor,
        "database_host": db_host if is_postgres else "",
        "database_name": str(db.get("NAME")) if is_postgres else "db.sqlite3 (file di server)",
        "uses_rds": uses_rds,
        "use_s3": settings.USE_S3,
        "bucket": getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""),
        "storage_backend": settings.STORAGES["default"]["BACKEND"].rsplit(".", 1)[-1],
        "static_url": settings.STATIC_URL,
        "media_url": settings.MEDIA_URL,
        "debug": settings.DEBUG,
    }
