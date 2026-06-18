from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="SaaS-сервис аналитики Wildberries: продажи, заказы, остатки, "
    "уведомления в Telegram.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.ENVIRONMENT}


@app.get("/api", tags=["meta"])
async def api_info() -> dict[str, str]:
    return {"app": settings.APP_NAME, "docs": "/docs"}


@app.get("/", include_in_schema=False)
async def landing() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
