"""
students.py – Endpoints del módulo Estudiante.

Seguridad:
  - Todos los endpoints usan require_role("estudiante") para prevenir IDOR.
  - El user_id se toma del header X-User-ID, nunca del path.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.database import db
from app.core.security import require_role
from app.models.activities import StudentProfileUpdate
from app.services import student_service

router = APIRouter()

# Dependencia reutilizable: solo estudiantes
_student_guard = require_role("estudiante")


# ══════════════════════ Unirse a una clase (Con código) ══════════════════════

class JoinRequest(BaseModel):
    codigo_acceso: str

@router.post(
    "/classes/join",
    status_code=status.HTTP_200_OK,
)
async def join_class(data: JoinRequest, current_user: dict = Depends(_student_guard)):
    student_id = current_user["user_id"]
    
    # 1. Buscar la clase por código
    clase = await db.classes.find_one({"codigo_acceso": data.codigo_acceso})
    if not clase:
        raise HTTPException(status_code=404, detail="El código de clase no es válido.")

    # 2. Verificar duplicados (Seguridad solicitada)
    if student_id in clase.get("estudiantes", []):
        raise HTTPException(
            status_code=400, 
            detail="El alumno ya está inscrito en esta clase"
        )

    # 3. Agregar el alumno de forma segura (evita carrera entre requests)
    result = await db.classes.update_one(
        {"_id": clase["_id"], "estudiantes": {"$ne": student_id}},
        {"$push": {"estudiantes": student_id}},
    )
    if result.modified_count == 0:
        raise HTTPException(
            status_code=400,
            detail="El alumno ya está inscrito en esta clase"
        )

    return {"message": "Inscripción exitosa.", "clase": clase.get("nombre_clase")}


# ══════════════════════ Darse de baja de una clase ══════════════════════

@router.delete(
    "/api/v1/student/classes/{class_id}/leave",
    status_code=status.HTTP_200_OK,
)
async def leave_class(class_id: str, current_user: dict = Depends(_student_guard)):
    try:
        result = await student_service.leave_class(
            student_id=current_user["user_id"],
            class_id=class_id,
        )
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de clase inválido.")
    except LookupError:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    except PermissionError:
        raise HTTPException(status_code=400, detail="No estás inscrito en esta clase.")


# ════════════════════ Consultar actividades de una clase ════════════════════

@router.get(
    "/api/v1/student/classes/{class_id}/activities",
    status_code=status.HTTP_200_OK,
)
async def get_class_activities(class_id: str, current_user: dict = Depends(_student_guard)):
    try:
        return await student_service.get_class_activities(
            student_id=current_user["user_id"],
            class_id=class_id,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de clase inválido.")
    except LookupError:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    except PermissionError:
        raise HTTPException(status_code=403, detail="No estás inscrito en esta clase.")


# ══════════════════════════ Editar perfil ══════════════════════════

@router.put(
    "/api/v1/student/profile",
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    data: StudentProfileUpdate,
    current_user: dict = Depends(_student_guard),
):
    try:
        return await student_service.update_profile(
            student_id=current_user["user_id"],
            data=data.model_dump(exclude_none=True),
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido.")
    except LookupError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")


# ═══════════════════════ Progreso del estudiante ═══════════════════════

@router.get(
    "/api/v1/student/progress",
    status_code=status.HTTP_200_OK,
)
async def get_progress(current_user: dict = Depends(_student_guard)):
    try:
        return await student_service.get_progress(
            student_id=current_user["user_id"],
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido.")
    except LookupError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
