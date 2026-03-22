"""
challenges.py - Endpoints para la Sala de Desafíos (Gamificación).
Utiliza polling HTTP en vez de WebSockets para cumplir con el MVP KISS.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.security import require_role
from app.services import challenges_service

router = APIRouter()
_student_guard = require_role("estudiante")

class ChallengeAnswer(BaseModel):
    question_index: int
    answer: str

@router.post("/api/v1/challenges/queue", status_code=200)
async def enter_queue(current_user: dict = Depends(_student_guard)):
    """
    Encola al estudiante o le devuelve su partida activa si ya la tiene.
    """
    return await challenges_service.enter_queue(current_user["user_id"])


@router.get("/api/v1/challenges/current", status_code=200)
async def get_current_status(current_user: dict = Depends(_student_guard)):
    """
    Retorna el estado actual del jugador (esperando, partida, scores).
    """
    status = await challenges_service.get_current_status(current_user["user_id"])
    if status["status"] == "none":
        # Para ser RESTful, un 404 está bien o un objeto explícito
        return {"status": "none", "match_id": None}
    return status


@router.post("/api/v1/challenges/{match_id}/answer", status_code=200)
async def submit_answer(
    match_id: str,
    payload: ChallengeAnswer,
    current_user: dict = Depends(_student_guard)
):
    try:
        return challenges_service.submit_answer(
            match_id=match_id,
            student_id=current_user["user_id"],
            question_index=payload.question_index,
            answer=payload.answer
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/v1/challenges/current", status_code=200)
async def leave_match(current_user: dict = Depends(_student_guard)):
    """
    Abandona la cola o la partida activa.
    """
    left = challenges_service.leave_match(current_user["user_id"])
    return {"message": "Has abandonado la sala", "success": left}
