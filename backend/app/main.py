import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.routers import admin, applicant, auth
from app.services.storage_service import ensure_bucket_exists

logger = logging.getLogger(__name__)

MAX_VIDEO_BYTES = 200 * 1024 * 1024


class VideoUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            request.method == "POST"
            and request.url.path.rstrip("/").endswith("/applicant/video")
        ):
            cl = request.headers.get("content-length")
            if cl is not None:
                try:
                    if int(cl) > MAX_VIDEO_BYTES:
                        return JSONResponse(
                            {"detail": "Video file exceeds maximum size of 200MB"},
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        )
                except ValueError:
                    pass
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_bucket_exists()
    yield


app = FastAPI(title="inVision U API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(VideoUploadSizeMiddleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(applicant.router, prefix="/api/v1/applicant", tags=["applicant"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/", include_in_schema=False)
async def root():
    """Avoid noisy 404s when the API base URL is opened in a browser or probed."""
    return {
        "service": "inVision U API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "api_v1": "/api/v1",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/health")
async def health():
    return {"status": "ok"}
