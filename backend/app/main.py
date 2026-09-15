"""
FastAPI Main Application Entry Point
Secure PDF Document Authentication Using Cryptographic Hashing and QR Codes
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import generate, verify
from app.schemas.response_models import HealthResponse

settings.init_storage()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes required local storage directories upon startup.
    """
    settings.init_storage()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(generate.router, prefix=settings.API_PREFIX)
app.include_router(verify.router, prefix=settings.API_PREFIX)
app.mount(
    f"{settings.API_PREFIX}/visual-results",
    StaticFiles(directory=settings.OUTPUT_DIR),
    name="visual-results",
)
app.mount(
    f"{settings.API_PREFIX}/forensic-results",
    StaticFiles(directory=settings.FORENSIC_RESULTS_DIR),
    name="forensic-results",
)


@app.get("/", tags=["System Information"])
async def root():
    """Root endpoint welcoming clients and indicating operational status."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }


@app.get(
    f"{settings.API_PREFIX}/health",
    response_model=HealthResponse,
    tags=["System Information"],
    status_code=status.HTTP_200_OK
)
async def health_check():
    """System health check endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION
    )
