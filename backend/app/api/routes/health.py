from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.db.session import check_db_connection
from app.db.redis import check_redis_connection

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic application health check.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@router.get("/health/db")
async def db_health_check():
    """
    Verifies PostgreSQL database connectivity and pgvector extension availability.
    """
    try:
        db_status = check_db_connection()
        return {
            "status": "ok",
            "database": "connected" if db_status["connected"] else "disconnected",
            "pgvector_extension": db_status["pgvector_extension"],
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "unavailable",
                "detail": str(e),
            },
        )


@router.get("/health/redis")
async def redis_health_check():
    """
    Verifies Redis connectivity.
    """
    try:
        redis_status = check_redis_connection()
        return {
            "status": "ok",
            "redis": "connected" if redis_status["connected"] else "disconnected",
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "redis": "unavailable",
                "detail": str(e),
            },
        )
