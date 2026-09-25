from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from core.database import init_db

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DataQ – Intelligent data quality, reconciliation and analytics platform",
)

# CORS for local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# Import and include routers (will be expanded)
from api import sources, quality, health, reconciliation, trusted, ai, audit, exceptions, dashboard  # noqa: E402

app.include_router(sources.router, prefix="/sources", tags=["Sources"])
app.include_router(quality.router, prefix="/quality", tags=["Quality"])
app.include_router(reconciliation.router, prefix="/reconciliation", tags=["Reconciliation"])
app.include_router(trusted.router, prefix="/trusted", tags=["Trusted Data"])
app.include_router(ai.router, prefix="/ai", tags=["AI Analyst"])
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(audit.router, prefix="/audit", tags=["Audit"])
app.include_router(exceptions.router, prefix="/exceptions", tags=["Exceptions"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])