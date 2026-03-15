from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.connection_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await manager.send_personal_message(
        {"type": "welcome", "message": "AegisCore WebSocket scaffold connected."},
        websocket,
    )

    try:
        while True:
            payload = await websocket.receive_text()
            await manager.send_personal_message(
                {"type": "ack", "message": f"Received: {payload}"},
                websocket,
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
