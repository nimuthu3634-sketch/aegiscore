from fastapi import APIRouter

from app.routers import alerts, auth, dashboard, health, incidents, integrations, logs, ml, websocket

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
