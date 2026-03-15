from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket import alert_stream_manager, build_alert_stream_ready_payload

router = APIRouter()


@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await alert_stream_manager.connect(websocket)
    await alert_stream_manager.send_personal_message(build_alert_stream_ready_payload(), websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_stream_manager.disconnect(websocket)
