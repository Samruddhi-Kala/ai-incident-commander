from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import register_exception_handlers
from app.api.routes import health
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events lifecycle.
    """
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="A production-inspired AI incident investigation and response platform backend API.",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

# Register central application exception handlers
register_exception_handlers(app)

# Configure CORS for local frontend origins and dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Health routes
app.include_router(health.router, tags=["Health"])

# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint returning service status and documentation link.
    """
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_v1_prefix": "/api/v1",
    }
