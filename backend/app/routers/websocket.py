from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.services.websocket import alert_stream_manager, build_alert_stream_ready_payload
from app.utils.auth import get_current_active_websocket_user

router = APIRouter()


@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    try:
        get_current_active_websocket_user(websocket)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await alert_stream_manager.connect(websocket)
    await alert_stream_manager.send_personal_message(build_alert_stream_ready_payload(), websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_stream_manager.disconnect(websocket)
