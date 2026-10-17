"""FastAPI application entrypoint for ClaimGuard."""
import logging
import platform
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db
from backend.routers import claims, stream
from backend.ml.inference import detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("claimguard")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database on startup."""
    logger.info("Initializing ClaimGuard database schemas...")
    init_db()
    logger.info("Database schemas initialized successfully.")
    yield
    logger.info("ClaimGuard shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time AI Healthcare Claims Risk Intelligence API",
    lifespan=lifespan,
)

# Enable CORS for frontend Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(claims.router, prefix=settings.API_PREFIX)
app.include_router(stream.router)

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint explicitly returning execution environment target and latency percentiles."""
    metrics = detector.get_latency_metrics()
    return {
        "status": "HEALTHY" if detector.model is not None else "DEGRADED",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "execution_target": settings.EXECUTION_TARGET,
        "database": settings.DATABASE_URL.split("///")[-1],
        "model_version": detector.model_version,
        "model_loaded_from_disk": detector.model_loaded_from_disk,
        "machine_architecture": platform.machine(),
        "latency_p50_ms": metrics["p50_ms"],
        "latency_p95_ms": metrics["p95_ms"],
        "latency_metrics": metrics,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
