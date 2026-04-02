import asyncio
import logging
import os
import tempfile
import uuid

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.applicant_profile import ApplicantProfile
from app.services import storage_service

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper

        _whisper_model = whisper.load_model("base")
    return _whisper_model


def _transcribe_path(path: str) -> str:
    model = _get_model()
    result = model.transcribe(path)
    return (result or {}).get("text") or ""


async def transcribe_and_save_profile(profile_id: uuid.UUID, object_key: str) -> None:
    try:
        data = await asyncio.to_thread(storage_service.get_object_bytes, object_key)
    except Exception as e:
        logger.error("Failed to download video for transcription: %s", e)
        data = None
    text = ""
    if data:
        suffix = ".mp4"
        if object_key.lower().endswith(".webm"):
            suffix = ".webm"
        elif object_key.lower().endswith(".mov"):
            suffix = ".mov"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tmp.write(data)
            tmp.flush()
            tmp.close()
            try:
                text = await asyncio.to_thread(_transcribe_path, tmp.name)
            except Exception as e:
                logger.error("Whisper transcription failed: %s", e)
                text = ""
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(ApplicantProfile).where(ApplicantProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if profile:
                profile.video_transcript = text or ""
                await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to save transcript for profile %s", profile_id)
