from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings


@dataclass
class StoredObject:
    storage: str  # local|s3
    object_key: str  # local path or s3 key


def _local_write_bytes(base_dir: Path, key: str, data: bytes) -> StoredObject:
    p = base_dir / key
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return StoredObject(storage="local", object_key=str(p))


def _s3_client():
    import boto3

    s = get_settings()
    return boto3.client(
        "s3",
        region_name=s.s3_region,
        aws_access_key_id=s.s3_access_key_id,
        aws_secret_access_key=s.s3_secret_access_key,
        endpoint_url=s.s3_endpoint_url,
    )


def put_bytes(*, kind: str, filename: str, data: bytes) -> StoredObject:
    """
    Store bytes either in local filesystem or S3 depending on config.
    Returns an object key that can later be used to fetch/download.
    """
    s = get_settings()
    safe_name = os.path.basename(filename) or "blob"
    key = f"{kind}/{safe_name}"

    if s.storage_backend == "s3":
        if not s.s3_bucket:
            raise RuntimeError("S3 storage enabled but S3_BUCKET not set")
        content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        cli = _s3_client()
        cli.put_object(Bucket=s.s3_bucket, Key=key, Body=data, ContentType=content_type)
        return StoredObject(storage="s3", object_key=key)

    base = Path(s.media_dir if kind == "media" else s.artifacts_dir)
    return _local_write_bytes(base, safe_name if kind in ("media", "artifacts") else key, data)


def get_local_path(obj: StoredObject) -> Optional[Path]:
    if obj.storage != "local":
        return None
    return Path(obj.object_key)


def get_bytes(*, storage: str, object_key: str) -> bytes:
    s = get_settings()
    if storage == "s3":
        if not s.s3_bucket:
            raise RuntimeError("S3 bucket not set")
        cli = _s3_client()
        resp = cli.get_object(Bucket=s.s3_bucket, Key=object_key)
        return resp["Body"].read()
    return Path(object_key).read_bytes()

