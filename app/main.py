from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, ensure_sqlite_schema
from app.core.exceptions import DomainError, domain_exception_handler
from app.core.logging import configure_logging, get_logger
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.tenant_middleware import TenantMiddleware

logger = get_logger("skyfall.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    ensure_sqlite_schema()
    logger.info("Skyfall Lounge API startup")
    yield
    logger.info("Skyfall Lounge API shutdown")


app = FastAPI(
    title="Skyfall Lounge API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

app.add_exception_handler(DomainError, domain_exception_handler)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    db_status = "connected"
    try:
        with engine.connect():
            db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status, "version": "1.0.0"}


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }
