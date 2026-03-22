from fastapi import APIRouter, Depends
from typing import List, Any
from app import database

router = APIRouter()

@router.get("/api/v1/courses", status_code=200)
async def get_courses():
    """
    Retorna la lista de todos los cursos registrados en la colección 'cursos'.
    """
    cursor = database.db.cursos.find({}, {"capitulos.ejercicios": 0})  # Evitar cargar todos los ejercicios para el catálogo
    courses = await cursor.to_list(length=100)
    
    # Convertir _id de MongoDB a string
    for course in courses:
        course["_id"] = str(course["_id"])
        
    return courses
