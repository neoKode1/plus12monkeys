"""+12 Monkeys — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, auth, builds, health, mcp, templates, wizard
from app.core.config import settings
from app.core.database import close_db
from app.services.orchestrator import close_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — nothing needed yet
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


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }

