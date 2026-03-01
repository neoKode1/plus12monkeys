"""+12 Monkeys — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import agents, auth, billing, builds, health, mcp, templates, webhook, wizard
from app.core.config import settings
from app.core.database import close_db, ensure_indexes
from app.services.orchestrator import close_client

# Rate limiter — shared instance, keyed by client IP
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — create MongoDB indexes
    await ensure_indexes()
    yield
    # Shutdown — close shared clients
    await close_client()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agent-as-a-Service platform with MCP integration",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — set CORS_ORIGINS env var to restrict in production
_origins = (
    ["*"]
    if settings.cors_origins.strip() == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(mcp.router, prefix="/api/v1")
app.include_router(wizard.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(builds.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }

