# Sahel Dev Backend - FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sahel Dev API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Sahel Dev API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Import routers
from routes import auth, monitors, status_pages, alerts, monitoring

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(monitors.router, prefix="/api/monitors", tags=["monitors"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(status_pages.router, prefix="/api/status-pages", tags=["status-pages"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])


# Run monitoring manually
@app.post("/api/run-monitoring")
async def run_monitoring():
    """Run monitoring check for all monitors (can be called by cron)"""
    from worker import MonitoringWorker
    worker = MonitoringWorker()
    worker.run_all()
    return {"message": "Monitoring check completed"}