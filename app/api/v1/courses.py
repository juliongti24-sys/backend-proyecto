from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from app import database
from bson import ObjectId
from app.core.security import get_current_user

router = APIRouter()

@router.get("/", status_code=200)
async def get_courses():
    """
    Retorna la lista de todos los cursos registrados en la base de datos.
    """
    courses = await database.db.get_collection("cursos").find().to_list(100)
    for course in courses:
        course["_id"] = str(course["_id"])
    return courses

@router.get("/{course_id}", status_code=200)
async def get_course_details(course_id: str):
    """
    Retorna los detalles de un curso específico.
    """
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="ID de curso inválido")
    
    course = await database.db.get_collection("cursos").find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    course["_id"] = str(course["_id"])
    return course

@router.post("/{course_id}/enroll", status_code=200)
async def enroll_course(course_id: str, current_user: Any = Depends(get_current_user)):
    """
    Inscribe al estudiante actual en un curso.
    """
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="ID de curso inválido")
    
    # Verificar si el curso existe
    course = await database.db.get_collection("cursos").find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Actualizar el usuario agregando el curso a su lista
    await database.db.get_collection("users").update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$addToSet": {"cursos_inscritos": course_id}}
    )
    
    return {"message": "Inscripción exitosa", "course_id": course_id}
