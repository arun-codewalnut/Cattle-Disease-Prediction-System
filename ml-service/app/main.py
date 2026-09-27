import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

load_dotenv()  # must run before any app.* import reads an env var at module load time

from app.api.diagnose import router as diagnose_router  # noqa: E402
from app.api.diagnoses import router as public_api_router  # noqa: E402
from app.errors import (  # noqa: E402
    ApiError,
    api_error_handler,
    http_error_handler,
    unexpected_error_handler,
)
from app.middleware import correlation_id_middleware  # noqa: E402

# Every log line carries the correlation ID in its message (see app/api/diagnoses.py), so one
# request can be traced from the frontend's console through these logs.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(name)s - %(message)s")

app = FastAPI(title="ml-service", version="0.1.0")

app.middleware("http")(correlation_id_middleware)
# Browser calls come straight from the frontend now that there's no separate backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)
app.include_router(diagnose_router)
app.include_router(public_api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
