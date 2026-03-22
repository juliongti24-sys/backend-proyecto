"""
student_service.py – Capa repositorio para operaciones del estudiante.

Patrón Repositorio: Toda la lógica de acceso a datos está aquí,
los routers solo orquestan y responden HTTP.
"""
import os
from datetime import date

from bson import ObjectId
from app import database


async def leave_class(student_id: str, class_id: str) -> dict:
    """
    Elimina al estudiante del array 'estudiantes' de la clase.
    Retorna dict con resultado o lanza excepciones descriptivas.
    """
    try:
        oid = ObjectId(class_id)
    except Exception:
        raise ValueError("ID de clase inválido.")

    clase = await database.db.classes.find_one({"_id": oid})
    if not clase:
        raise LookupError("Clase no encontrada.")

    if student_id not in clase.get("estudiantes", []):
        raise PermissionError("No estás inscrito en esta clase.")

    await database.db.classes.update_one(
        {"_id": oid},
        {"$pull": {"estudiantes": student_id}},
    )
    return {"message": "Te has dado de baja de la clase exitosamente."}


async def get_class_activities(student_id: str, class_id: str) -> list:
    """
    Retorna las actividades asignadas a la clase.
    Verifica que la clase exista y que el estudiante esté inscrito.
    """
    try:
        oid = ObjectId(class_id)
    except Exception:
        raise ValueError("ID de clase inválido.")

    clase = await database.db.classes.find_one({"_id": oid})
    if not clase:
        raise LookupError("Clase no encontrada.")

    if student_id not in clase.get("estudiantes", []):
        raise PermissionError("No estás inscrito en esta clase.")

    cursor = database.db.activities.find({"class_id": class_id})
    activities = await cursor.to_list(length=100)
    for act in activities:
        act["_id"] = str(act["_id"])
    return activities


async def update_profile(student_id: str, data: dict) -> dict:
    """
    Actualiza el perfil del estudiante.
    Si se incluye foto_perfil nueva, elimina la foto anterior del disco.
    """
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise ValueError("ID de usuario inválido.")

    user = await database.db.users.find_one({"_id": oid})
    if not user:
        raise LookupError("Usuario no encontrado.")

    # Construir solo los campos no-None
    update_fields = {k: v for k, v in data.items() if v is not None}
    if not update_fields:
        # Nada que actualizar, retornar usuario actual
        user.pop("password", None)
        user["_id"] = str(user["_id"])
        return user

    # Limpieza de foto huérfana
    if "foto_perfil" in update_fields:
        old_photo = user.get("foto_perfil")
        if old_photo:
            # Eliminar archivo físico si existe
            old_path = old_photo.lstrip("/")  # "uploads/old-uuid.jpg"
            if os.path.exists(old_path):
                os.remove(old_path)

    await database.db.users.update_one({"_id": oid}, {"$set": update_fields})

    updated = await database.db.users.find_one({"_id": oid})
    updated.pop("password", None)
    updated["_id"] = str(updated["_id"])
    return updated


async def get_progress(student_id: str) -> dict:
    """
    Retorna puntos totales, racha, y registros de progreso diario.
    """
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise ValueError("ID de usuario inválido.")

    user = await database.db.users.find_one({"_id": oid})
    if not user:
        raise LookupError("Usuario no encontrado.")

    # Obtener progreso diario
    cursor = database.db.student_progress.find(
        {"student_id": student_id}
    ).sort("date", -1)
    daily = await cursor.to_list(length=30)
    for d in daily:
        d["_id"] = str(d["_id"])

    return {
        "puntos": user.get("puntos", 0),
        "racha": user.get("racha", 0),
        "daily_progress": daily,
    }
