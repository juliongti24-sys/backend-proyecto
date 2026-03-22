from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_role
from app.services import teacher_service

router = APIRouter()

# Solo maestros pueden acceder
_teacher_guard = require_role("maestro")

@router.get("/api/v1/teacher/analytics", status_code=200)
async def get_analytics(current_user: dict = Depends(_teacher_guard)):
    """
    Retorna analíticas del grupo para el maestro autenticado.
    """
    try:
        # El teacher_id se toma del token (current_user["user_id"])
        analytics = await teacher_service.get_teacher_analytics(current_user["user_id"])
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
