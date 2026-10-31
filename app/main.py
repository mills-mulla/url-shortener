from fastapi import FastAPI

from app.config import settings
from app.routers import links, users, redirect

app = FastAPI(
    title="URL Shortener",
    docs_url="/docs" if settings.app_env != "prod" else None,
    redoc_url=None,
    )
app.include_router(users.router)
app.include_router(links.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

app.include_router(redirect.router)