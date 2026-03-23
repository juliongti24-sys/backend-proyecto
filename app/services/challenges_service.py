"""
challenges_service.py - Motor de Emparejamiento (Matchmaking) y Desafíos.
Usando estado en memoria para el MVP (KISS) y sincronización por HTTP Polling.
"""
import uuid
import random
from typing import Dict, Any, Optional
from app import database
from bson import ObjectId

# Estado en memoria
waiting_queue: list = []  # IDs de estudiantes en espera
active_matches: Dict[str, Dict[str, Any]] = {}  # match_id -> datos de la partida

async def _get_random_exercises(count: int = 5) -> list:
    """Extrae ejercicios aleatorios de la colección 'cursos'."""
    cursor = database.db.cursos.aggregate([
        {"$unwind": "$capitulos"},
        {"$unwind": "$capitulos.ejercicios"},
        {"$sample": {"size": count}},
        {"$project": {"_id": 0, "ejercicio": "$capitulos.ejercicios"}}
    ])
    results = await cursor.to_list(length=count)
    return [r["ejercicio"] for r in results]

async def enter_queue(student_id: str, room_code: str = None) -> Dict[str, Any]:
    global waiting_queue, active_matches
    
    # Si ya está en una partida activa
    for m_id, m_data in active_matches.items():
        if student_id in m_data["players"]:
            return {"status": m_data["status"], "match_id": m_id}

    if student_id not in waiting_queue:
        waiting_queue.append(student_id)

    # Lógica de match
    if len(waiting_queue) >= 2:
        player1_id = waiting_queue.pop(0)
        player2_id = waiting_queue.pop(0)
        
        # Obtener info de los jugadores (fotos y nombres)
        p1_data = await database.db.users.find_one({"_id": ObjectId(player1_id)})
        p2_data = await database.db.users.find_one({"_id": ObjectId(player2_id)})

        match_id = str(uuid.uuid4())
        exercises = await _get_random_exercises(5)
        
        active_matches[match_id] = {
            "status": "active",
            "players": [player1_id, player2_id],
            "player_info": {
                player1_id: {
                    "nombre": p1_data.get("nombre", "Estudiante 1"),
                    "foto_perfil": p1_data.get("foto_perfil")
                },
                player2_id: {
                    "nombre": p2_data.get("nombre", "Estudiante 2"),
                    "foto_perfil": p2_data.get("foto_perfil")
                }
            },
            "scores": {player1_id: 0, player2_id: 0},
            "exercises": exercises,
            "created_at": str(uuid.uuid1())
        }
        
        if student_id in [player1_id, player2_id]:
            return {"status": "matched", "match_id": match_id}

    return {"status": "waiting", "match_id": None}

async def get_current_status(student_id: str) -> Dict[str, Any]:
    """Retorna el estado de la partida actual del estudiante."""
    for m_id, m_data in active_matches.items():
        if student_id in m_data["players"]:
            # Para la respuesta pública, ocultamos la respuesta_correcta de los ejercicios
            public_exercises = []
            for idx, ex in enumerate(m_data["exercises"]):
                public_exercises.append({
                    "question_index": idx,
                    "pregunta": ex.get("pregunta", ""),
                    "opciones": ex.get("opciones", []),
                    "tipo": ex.get("tipo", "opcion_multiple")
                })
            
            return {
                "status": m_data["status"],
                "match_id": m_id,
                "scores": m_data["scores"],
                "player_info": m_data["player_info"],
                "exercises": public_exercises,
                "opponent_id": [p for p in m_data["players"] if p != student_id][0]
            }
            
    if student_id in waiting_queue:
        return {"status": "waiting", "match_id": None}
        
    return {"status": "none", "match_id": None}

def submit_answer(match_id: str, student_id: str, question_index: int, answer: str) -> Dict[str, Any]:
    match = active_matches.get(match_id)
    if not match:
        raise LookupError("Partida no encontrada")
        
    if student_id not in match["players"]:
        raise ValueError("No participas en esta partida")
        
    if question_index < 0 or question_index >= len(match["exercises"]):
        raise ValueError("Pregunta no válida")
        
    correct_answer = match["exercises"][question_index].get("respuesta_correcta", "").strip()
    is_correct = (answer.strip() == correct_answer)
    
    if is_correct:
        match["scores"][student_id] += 10
        
    # Verificar si ya terminaron todos? Por ahora simple: retorna score.
    return {
        "correct": is_correct,
        "score_update": match["scores"][student_id],
        "current_scores": match["scores"]
    }

def leave_match(student_id: str) -> bool:
    global waiting_queue, active_matches
    
    if student_id in waiting_queue:
        waiting_queue.remove(student_id)
        return True
        
    for m_id, m_data in list(active_matches.items()):
        if student_id in m_data["players"]:
            # Marcar partida como terminada o eliminarla
            del active_matches[m_id]
            return True
            
    return False
