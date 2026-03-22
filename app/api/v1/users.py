import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from bson import ObjectId

from app.database import db
from passlib.context import CryptContext

router = APIRouter()

# Configuración para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    if password and len(password) > 50:
        password = password[:50]
    return pwd_context.hash(password)

@router.get("/api/v1/users/{user_id}")
async def get_user_profile(user_id: str):
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # Eliminar password
    user.pop("password", None)
    
    # Convertir _id a string
    user["_id"] = str(user["_id"])
    
    return user

@router.put("/api/v1/users/{user_id}")
async def update_user_profile(
    user_id: str,
    nombre: str = Form(...),
    correo: str = Form(...),
    telefono: str = Form(...),
    password: Optional[str] = Form(None),
    foto_perfil: Optional[UploadFile] = File(None)
):
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    update_data = {
        "nombre": nombre,
        "correo": correo,
        "telefono": telefono
    }
    
    if password:
        update_data["password"] = get_password_hash(password)
        
    if foto_perfil and foto_perfil.filename:
        # Save file to uploads folder
        os.makedirs("uploads", exist_ok=True)
        file_extension = foto_perfil.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join("uploads", unique_filename)
        
        with open(file_path, "wb") as f:
            content = await foto_perfil.read()
            f.write(content)
            
        update_data["foto_perfil"] = f"/uploads/{unique_filename}"
        
    await db.users.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    # Retrieve updated user and strip password
    updated_user = await db.users.find_one({"_id": obj_id})
    updated_user.pop("password", None)
    updated_user["_id"] = str(updated_user["_id"])
    
    return updated_user
