from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # must run before any app.* import reads an env var at module load time

from app.api.diagnose import router as diagnose_router  # noqa: E402
from app.errors import ApiError, api_error_handler  # noqa: E402
from app.middleware import correlation_id_middleware  # noqa: E402

app = FastAPI(title="ml-service", version="0.1.0")

app.middleware("http")(correlation_id_middleware)
app.add_exception_handler(ApiError, api_error_handler)
app.include_router(diagnose_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
