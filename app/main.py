from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="Url Shortener",
    docs_url="/docs" if settings.app_env != "prod" else None,
    redoc_url=None,
    )

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}