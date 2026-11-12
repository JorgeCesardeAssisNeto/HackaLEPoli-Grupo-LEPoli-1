import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from database import init_db, engine
from tasks.polling import start_scheduler, shutdown_scheduler
from routers import webhook_router, ingestion_router, causal_router, health_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("wearable_causal_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events:
      - Startup: Initializes relational database tables in open_health.db
                 Starts background APScheduler polling engine
      - Shutdown: Gracefully halts background tasks and disposes async DB connections
    """
    logger.info("Initializing Wearable Data Ingestion & Causal Inference Microservice...")
    logger.info("Connecting to relational database: %s", settings.DATABASE_PATH)
    await init_db()

    logger.info("Starting background APScheduler polling task for ROOK API...")
    start_scheduler()

    logger.info("Microservice successfully running on http://%s:%d", settings.HOST, settings.PORT)
    yield

    logger.info("Shutting down background tasks...")
    shutdown_scheduler()
    logger.info("Disposing database connection pool...")
    await engine.dispose()
    logger.info("Microservice stopped.")

app = FastAPI(
    title="Open Health — Wearable Ingestion & Causal Inference Service",
    description=(
        "Microservice running on Port 5050 that ingests Apple Watch, Garmin, and Galaxy Ring biometrics "
        "via ROOK API (Webhooks & Daily Polling) and runs a 3-Layer Causal Inference Engine (DAGs) "
        "to filter out lifestyle confounders before alerting clinicians."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Application Routers
app.include_router(webhook_router)
app.include_router(ingestion_router)
app.include_router(causal_router)
app.include_router(health_router)

@app.get("/", tags=["Root"])
async def root():
    """Service status and OpenAPI documentation entrypoint."""
    return {
        "service": "Open Health Wearable Data Ingestion & Causal Inference Microservice",
        "port": settings.PORT,
        "status": "online",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "inter_service_endpoints": {
            "fhir_lab_service": settings.FHIR_LAB_SERVICE_URL,
            "nhanes_baseline_service": settings.NHANES_BASELINE_SERVICE_URL
        },
        "supported_targets": [
            "TARGET_1_DEEP_SLEEP (< 16% vs Steps & Alcohol)",
            "TARGET_2_METABOLIC_RISK (Resting HR >= 72 bpm vs Screen Time & Caffeine)",
            "TARGET_3_INFLAMMATION_HRV (HRV RMSSD < 38 ms vs Short Sleep & Alcohol / 4-day rule)",
            "TARGET_4_ANEMIA_LOAD (Daytime HR > 92 bpm with low steps / ICD index + FHIR Lab)"
        ]
    }

if __name__ == "__main__":
    print(f"\n==================================================================")
    print(f"  Open Health — Wearable & Causal Inference Microservice")
    print(f"  Running on: http://{settings.HOST}:{settings.PORT}")
    print(f"==================================================================\n")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

