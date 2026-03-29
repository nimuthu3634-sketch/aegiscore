from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.entities import User
from app.services.realtime import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    settings = get_settings()
    ip_address = (
        websocket.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or websocket.headers.get("x-real-ip")
        or (websocket.client.host if websocket.client else None)
        or "unknown"
    )
    retry_after = rate_limiter.hit(
        "websocket-alerts",
        ip_address,
        limit=settings.websocket_rate_limit_attempts,
        window_seconds=settings.websocket_rate_limit_window_seconds,
    )
    if retry_after is not None:
        await websocket.close(code=4408, reason="Rate limit exceeded")
        return

    token = websocket.cookies.get(settings.auth_cookie_name) or websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_access_token(token)
    except ValueError:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload.get("sub"), User.is_active.is_(True)).one_or_none()
        if user is None:
            await websocket.close(code=4403)
            return
    finally:
        db.close()

    await manager.connect("alerts", websocket)
    await websocket.send_json({"event": "connected", "user": user.email})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("alerts", websocket)
