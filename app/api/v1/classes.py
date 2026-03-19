import string
import random
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import db
from app.models.classes import ClassCreate

router = APIRouter()

def generate_access_code(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@router.post("/api/v1/teacher/classes", status_code=status.HTTP_201_CREATED)
async def create_class(class_data: ClassCreate):
    # Generar código único
    codigo = generate_access_code()
    
    # Asegurarnos de que el código no exista
    while await db.classes.find_one({"codigo_acceso": codigo}):
        codigo = generate_access_code()

    # Preparar el documento
    class_dict = class_data.model_dump()
    class_dict["codigo_acceso"] = codigo
    class_dict["estudiantes"] = []
    
    # Guardar en base de datos
    result = await db.classes.insert_one(class_dict)
    
    # Recuperar el documento insertado
    created_class = await db.classes.find_one({"_id": result.inserted_id})
    if created_class:
        created_class["_id"] = str(created_class["_id"])
    
    return created_class


@router.get("/api/v1/teacher/classes/{maestro_id}")
async def get_teacher_classes(maestro_id: str):
    cursor = db.classes.find({"maestro_id": maestro_id})
    clases = await cursor.to_list(length=100)
    
    # Convertir ObjectIds a string
    for clase in clases:
        clase["_id"] = str(clase["_id"])
        
    return clases


class JoinClassRequest(BaseModel):
    estudiante_id: str
    codigo_acceso: str

@router.post("/api/v1/student/classes/join", status_code=status.HTTP_200_OK)
async def join_class(data: JoinClassRequest):
    # Buscar la clase por código
    clase = await db.classes.find_one({"codigo_acceso": data.codigo_acceso})
    
    if not clase:
        raise HTTPException(
            status_code=404,
            detail="Código de clase inválido."
        )
        
    # Verificar si el estudiante ya está en la clase
    if data.estudiante_id in clase.get("estudiantes", []):
        raise HTTPException(
            status_code=400,
            detail="Ya estás inscrito en esta clase."
        )
        
    # Agregar estudiante a la lista de la clase mediante $push
    await db.classes.update_one(
        {"_id": clase["_id"]},
        {"$push": {"estudiantes": data.estudiante_id}}
    )
    
    return {"message": "Te has unido a la clase exitosamente."}


@router.get("/api/v1/student/classes/{estudiante_id}")
async def get_student_classes(estudiante_id: str):
    # Buscar todas las clases donde el ID del estudiante esté en el arreglo 'estudiantes'
    cursor = db.classes.find({"estudiantes": estudiante_id})
    clases = await cursor.to_list(length=100)
    
    # Convertir ObjectIds a string
    for clase in clases:
        clase["_id"] = str(clase["_id"])
        
    return clases

from bson import ObjectId

@router.get("/api/v1/classes/{class_id}")
async def get_class_info(class_id: str):
    try:
        # Convert string to ObjectId
        obj_id = ObjectId(class_id)
    except:
        raise HTTPException(status_code=400, detail="ID de clase inválido")
        
    clase = await db.classes.find_one({"_id": obj_id})
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
        
    clase["_id"] = str(clase["_id"])
    
    # Obtener nombre del maestro
    maestro = await db.users.find_one({"_id": ObjectId(clase["maestro_id"])})
    if maestro:
        clase["nombre_maestro"] = maestro.get("nombre", "Maestro Desconocido")
    else:
        clase["nombre_maestro"] = "Maestro Desconocido"
        
    return clase
