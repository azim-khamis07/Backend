"""FastAPI application factory and main entry point."""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseAPIException,
    ConflictError,
    NotFoundError,
    ValidationError,
    base_api_exception_handler,
    general_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
)
from app.core.logging import setup_logging
from app.core.metrics import get_metrics
from app.core.middleware import LoggingMiddleware, RequestIDMiddleware, TimingMiddleware
from app.core.rate_limit import RateLimitMiddleware, init_rate_limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import init_db
from app.infra.redis import cache_service
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.receipts.router import router as receipts_router
from app.modules.reports.router import router as reports_router
from app.modules.transactions.router import router as transactions_router
from app.modules.users.router import router as users_router

settings = get_settings()

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize Sentry if DSN is provided
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
        )
        logger = app.state.logger
        logger.info("Sentry initialized", extra={"environment": settings.SENTRY_ENVIRONMENT})

    # Startup
    logger = app.state.logger
    logger.info("Application starting up")

    # Initialize rate limiter
    init_rate_limiter()
    logger.info("Rate limiter initialized")

    # Check Redis connection
    if cache_service.ping():
        logger.info("Redis connection successful")
    else:
        logger.warning("Redis connection failed - caching disabled")

    # Initialize database tables (only in development)
    if settings.is_development:
        logger.info("Initializing database tables (development mode)")
        try:
            init_db()
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)

    yield

    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
        },
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Store logger in app state
    from app.core.logging import get_logger

    app.state.logger = get_logger(__name__)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Custom middleware (order matters!)
    app.add_middleware(SecurityHeadersMiddleware)  # First - security headers
    app.add_middleware(RateLimitMiddleware)  # Second - rate limiting
    app.add_middleware(RequestIDMiddleware)  # Third - request ID
    app.add_middleware(TimingMiddleware)  # Fourth - timing
    app.add_middleware(LoggingMiddleware)  # Last - logging

    # Exception handlers
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(AuthenticationError, base_api_exception_handler)
    app.add_exception_handler(AuthorizationError, base_api_exception_handler)
    app.add_exception_handler(NotFoundError, base_api_exception_handler)
    app.add_exception_handler(ValidationError, base_api_exception_handler)
    app.add_exception_handler(ConflictError, base_api_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include routers
    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(users_router, prefix=settings.API_V1_PREFIX)
    app.include_router(categories_router, prefix=settings.API_V1_PREFIX)
    app.include_router(transactions_router, prefix=settings.API_V1_PREFIX)
    app.include_router(receipts_router, prefix=settings.API_V1_PREFIX)
    app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
    app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)

    # Health check endpoint
    @app.get("/health", tags=["monitoring"])
    async def health_check() -> dict:
        """
        Health check endpoint with comprehensive dependency status.
        
        Returns:
            Health status with individual dependency checks
        """
        from fastapi import status as http_status
        from fastapi.responses import JSONResponse
        from sqlalchemy import text
        
        from app.db.session import engine
        from app.infra.s3 import S3Service

        status_data = {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "dependencies": {},
        }

        # Check database
        db_status = "unhealthy"
        db_error = None
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
        
        status_data["dependencies"]["database"] = {
            "status": db_status,
            "error": db_error if db_error else None,
        }

        # Check Redis
        redis_status = "unhealthy"
        redis_error = None
        try:
            if cache_service.ping():
                redis_status = "healthy"
            else:
                redis_status = "unhealthy"
                redis_error = "Ping failed"
        except Exception as e:
            redis_status = "unhealthy"
            redis_error = str(e)
        
        status_data["dependencies"]["redis"] = {
            "status": redis_status,
            "error": redis_error if redis_error else None,
        }

        # Check S3 (optional - only if configured)
        s3_status = "not_configured"
        s3_error = None
        if settings.AWS_S3_BUCKET_NAME:
            try:
                # Try to check S3 connectivity by creating a service instance
                s3_service = S3Service()
                if s3_service.s3:
                    # Try a simple operation (head_bucket) to verify connectivity
                    try:
                        s3_service.s3.head_bucket(Bucket=settings.AWS_S3_BUCKET_NAME)
                        s3_status = "healthy"
                    except Exception as e:
                        s3_status = "unhealthy"
                        s3_error = f"S3 bucket access failed: {str(e)}"
                else:
                    s3_status = "unhealthy"
                    s3_error = "S3 client not initialized"
            except Exception as e:
                s3_status = "unhealthy"
                s3_error = str(e)
        
        status_data["dependencies"]["s3"] = {
            "status": s3_status,
            "error": s3_error if s3_error else None,
        }

        # Determine overall status
        critical_deps = [db_status]
        optional_deps = [redis_status, s3_status]
        
        if all(status == "healthy" for status in critical_deps):
            if all(status in ("healthy", "not_configured") for status in optional_deps):
                overall_status = "healthy"
                status_code = http_status.HTTP_200_OK
            else:
                overall_status = "degraded"  # Critical OK but optional services down
                status_code = http_status.HTTP_200_OK
        else:
            overall_status = "unhealthy"  # Critical service down
            status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE

        status_data["status"] = overall_status

        return JSONResponse(content=status_data, status_code=status_code)

    # Metrics endpoint
    @app.get("/metrics", tags=["monitoring"], include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint."""
        return get_metrics()

    @app.get("/")
    async def root() -> dict:
        """Root endpoint."""
        return {
            "message": "Welcome to Expense Tracker API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create app instance
app = create_app()
