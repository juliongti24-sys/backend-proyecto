"""
admin_students.py - Endpoints para el CRUD de estudiantes exclusivo para administradores.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any

from app.core.security import require_role
from app.services import admin_students_service

router = APIRouter()

# Dependencia: Solo usuarios con rol "admin"
_admin_guard = require_role("admin")

@router.get("/api/v1/admin/students", status_code=200)
async def list_students(current_user: dict = Depends(_admin_guard)):
    return await admin_students_service.get_all_students()

@router.post("/api/v1/admin/students", status_code=201)
async def create_student(
    payload: Dict[str, Any] = Body(...), 
    current_user: dict = Depends(_admin_guard)
):
    try:
        return await admin_students_service.create_student(payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/api/v1/admin/students/{student_id}", status_code=200)
async def update_student(
    student_id: str, 
    payload: Dict[str, Any] = Body(...), 
    current_user: dict = Depends(_admin_guard)
):
    try:
        return await admin_students_service.update_student(student_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/api/v1/admin/students/{student_id}", status_code=200)
async def delete_student(
    student_id: str, 
    current_user: dict = Depends(_admin_guard)
):
    try:
        await admin_students_service.delete_student(student_id)
        return {"message": "Estudiante eliminado exitosamente"}
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
