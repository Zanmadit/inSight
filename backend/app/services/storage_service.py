import logging
import re
import uuid
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


def _internal_client() -> Minio:
    ep = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "").rstrip("/")
    secure = settings.MINIO_ENDPOINT.startswith("https://")
    return Minio(
        ep,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=secure,
    )


def _presign_client() -> Minio:
    ep, secure = settings.minio_public_endpoint_secure
    return Minio(
        ep,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=secure,
        # MinIO defaults to us-east-1. Setting region explicitly prevents SDK
        # from trying to discover region via network (which fails for localhost
        # from inside Docker backend container).
        region="us-east-1",
    )


async def ensure_bucket_exists() -> None:
    client = _internal_client()
    try:
        found = client.bucket_exists(settings.MINIO_BUCKET)
        if not found:
            client.make_bucket(settings.MINIO_BUCKET)
    except S3Error as e:
        logger.error("MinIO bucket setup failed: %s", e)
        raise


def sanitize_filename(name: str) -> str:
    base = name.split("/")[-1]
    stem, dot, ext = base.rpartition(".")
    if dot:
        safe_stem = re.sub(r"[^a-zA-Z0-9._-]", "_", stem) or "file"
        safe_ext = re.sub(r"[^a-zA-Z0-9]", "", ext)[:10]
        return f"{safe_stem}.{safe_ext.lower()}" if safe_ext else safe_stem
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base) or "video"


def build_object_key(user_id: uuid.UUID, original_filename: str) -> str:
    safe = sanitize_filename(original_filename)
    return f"{user_id}/{uuid.uuid4()}_{safe}"


def put_object_from_bytes(object_key: str, data: bytes, content_type: str) -> None:
    client = _internal_client()
    client.put_object(
        settings.MINIO_BUCKET,
        object_key,
        BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def get_object_bytes(object_key: str) -> bytes:
    client = _internal_client()
    response = client.get_object(settings.MINIO_BUCKET, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def presigned_get_url(object_key: str | None, expiry_seconds: int = 3600) -> str | None:
    if not object_key:
        return None
    client = _presign_client()
    return client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_key,
        expires=timedelta(seconds=expiry_seconds),
    )
