from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import admin, alerts, auth, dashboard, health, incidents, ml, observability, realtime

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(observability.router, tags=["observability"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(realtime.router, tags=["realtime"])
