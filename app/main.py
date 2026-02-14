from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import logging

from app.routers.api import router as api_router
from app.services.uptime import started_at, uptime_seconds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("app")

app = FastAPI(title="Docker/K8s Observability App", version="1.0.0")

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["path", "method", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["path"])

@app.middleware("http")
async def metrics_middleware(request, call_next):
    path = request.url.path
    method = request.method
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUESTS.labels(path=path, method=method, status=str(response.status_code)).inc()
    LATENCY.labels(path=path).observe(duration)
    return response

@app.get("/healthz")
def healthz():
    return {"status": "We Are Aight My G"}

@app.get("/readyz")
def readyz():
    # senere kan du sjekke DB/redis etc her
    return {"status": "ready"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {
        "message": "Hello Batman! This app will be containerized, then deployed with Kubernetes + ArgoCD later.",
        "started_at": started_at().isoformat(),
        "uptime_seconds": uptime_seconds(),
        "endpoints": ["/healthz", "/readyz", "/metrics", "/api/ping", "/api/uptime"]
    }
