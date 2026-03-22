#admin_students_service.py - CRUD completo para administrar alumnos.

from typing import Dict, Any
from bson import ObjectId
from app import database
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_all_students() -> list:
    cursor = database.db.users.find({"rol": "estudiante"}, {"password": 0})
    students = await cursor.to_list(length=100)
    for s in students:
        s["_id"] = str(s["_id"])
    return students

async def create_student(data: Dict[str, Any]) -> Dict[str, Any]:
    existing = await database.db.users.find_one({"correo": data.get("correo")})
    if existing:
        raise ValueError("El correo ya está registrado.")
    
    pwd = data.get("password")
    if not pwd or not isinstance(pwd, str):
        raise ValueError("La contraseña debe ser una cadena de texto no vacía")
    
    # Bcrypt limit fix: Truncate to 50 to stay under 72-byte limit
    if len(pwd) > 50:
        pwd = pwd[:50]
        
    hashed_password = pwd_context.hash(pwd)
    
    new_user = {
        "nombre": data.get("nombre", "Sin nombre"),
        "correo": data.get("correo"),
        "password": hashed_password,
        "rol": "estudiante",
        "puntos": 0,
        "racha": 0,
        "foto_perfil": None,
        "matricula": data.get("matricula", "N/A"),
        "telefono": data.get("telefono", "N/A")
    }
    
    res = await database.db.users.insert_one(new_user)
    created_user = await database.db.users.find_one({"_id": res.inserted_id}, {"password": 0})
    created_user["_id"] = str(created_user["_id"])
    return created_user

async def update_student(student_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise LookupError("ID no válido")

    if not data:
        raise ValueError("No hay campos a actualizar")
        
    res = await database.db.users.update_one({"_id": oid}, {"$set": data})
    if res.matched_count == 0:
        raise LookupError("Estudiante no encontrado")
        
    updated = await database.db.users.find_one({"_id": oid}, {"password": 0})
    updated["_id"] = str(updated["_id"])
    return updated

async def delete_student(student_id: str) -> bool:
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise LookupError("ID no válido")
        
    res = await database.db.users.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise LookupError("Estudiante no encontrado")
        
    return True
