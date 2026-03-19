from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.challenge_manager import manager
import json

router = APIRouter()

@router.websocket("/api/v1/ws/challenge/{room_code}/{student_id}/{student_name}")
async def challenge_websocket(websocket: WebSocket, room_code: str, student_id: str, student_name: str):
    connected = await manager.connect(websocket, room_code, student_id, student_name)
    if not connected:
        return
        
    try:
        while True:
            # Esperar mensajes del cliente
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            
            if data.get("type") == "submit_answer":
                # Procesar la respuesta del estudiante
                answer_val = data.get("answer")
                try:
                    answer_int = int(answer_val)
                    await manager.submit_answer(room_code, student_id, answer_int)
                except ValueError:
                    # Ignorar o enviar feedback de que debe ser un número
                    pass
                    
    except WebSocketDisconnect:
        manager.disconnect(room_code, student_id)
        room = manager.active_rooms.get(room_code)
        
        # Broadcast que alguien se desconectó
        if room:
            # Si el juego ya había empezado, podríamos terminarlo o simplemente actualizar el leaderboard
            if room["status"] == "waiting":
                await manager._broadcast_lobby(room_code)
            else:
                await manager._broadcast_leaderboard(room_code)
                await manager._check_game_over(room_code)
