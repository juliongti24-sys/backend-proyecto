from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from bson import ObjectId
from app.database import db
from app.models.users import StudentCreate, UserLogin, TeacherCreate, TeacherUpdate
router = APIRouter()
admin_router = APIRouter()

# Configuración para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register/student", status_code=status.HTTP_201_CREATED)
async def register_student(student: StudentCreate):
    # 1. Verificar si el correo o matrícula ya existen en la base de datos
    existing_user = await db.users.find_one({
        "$or": [{"correo": student.correo}, {"matricula": student.matricula}]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo o matrícula ya están registrados."
        )

    # 2. Encriptar la contraseña
    hashed_password = pwd_context.hash(student.password)

    # 3. Preparar el documento para MongoDB
    student_dict = student.dict()
    student_dict["password"] = hashed_password
    student_dict["rol"] = "estudiante" # Asignamos el rol automáticamente
    student_dict["racha"] = 0 # Inicializamos valores de gamificación
    student_dict["puntos"] = 0

    # 4. Guardar en la base de datos
    await db.users.insert_one(student_dict)

    return {"message": "Estudiante registrado exitosamente"}

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(credentials: UserLogin):
    # 1. Buscar al usuario por su correo en MongoDB
    user = await db.users.find_one({"correo": credentials.correo})
    
    # Si no existe el usuario, lanzamos error (Mismo mensaje por seguridad)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Correo o contraseña incorrectos."
        )

    # 2. Verificar si la contraseña coincide con la encriptada
    password_valida = pwd_context.verify(credentials.password, user["password"])
    
    if not password_valida:
        raise HTTPException(
            status_code=400,
            detail="Correo o contraseña incorrectos."
        )

    # 3. Si todo está correcto, le damos la bienvenida
    return {
        "message": "¡Inicio de sesión exitoso!",
        "user": {
            "_id": str(user["_id"]),
            "nombre": user.get("nombre"),
            "correo": user.get("correo"),
            "matricula": user.get("matricula"),
            "rol": user.get("rol"),
            "puntos": user.get("puntos", 0)
        }
    }

@admin_router.post("/register/teacher", status_code=status.HTTP_201_CREATED)
async def register_teacher(teacher: TeacherCreate):
    # 1. Verificar si el correo o num_empleado ya existen
    existing_user = await db.users.find_one({
        "$or": [{"correo": teacher.correo}, {"num_empleado": teacher.num_empleado}]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo o número de empleado ya están registrados."
        )

    # 2. Encriptar la contraseña
    pwd = teacher.password
    if len(pwd) > 50:
        pwd = pwd[:50]
    hashed_password = pwd_context.hash(pwd)

    # 3. Preparar el documento para MongoDB
    teacher_dict = teacher.dict()
    teacher_dict["password"] = hashed_password
    teacher_dict["rol"] = "maestro" # Asignamos el rol de maestro
    
    # 4. Guardar en la base de datos
    await db.users.insert_one(teacher_dict)
    return {"message": "Maestro registrado exitosamente por el administrador."}


@admin_router.get("/teachers")
async def get_teachers():
    # 1. Buscar todos los usuarios que tengan el rol "maestro"
    cursor = db.users.find({"rol": "maestro"})
    maestros = await cursor.to_list(length=100) # Límite de 100 por ahora
    
    # 2. Limpiar la información por seguridad 
    for maestro in maestros:
        maestro["_id"] = str(maestro["_id"]) # MongoDB usa ObjectIds, los pasamos a texto
        maestro.pop("password", None)        # Ocultamos la contraseña
    return maestros


# ── Editar maestro ──
@admin_router.put("/teachers/{teacher_id}")
async def update_teacher(teacher_id: str, teacher: TeacherUpdate):
    # 1. Convertir el string a ObjectId de MongoDB
    try:
        oid = ObjectId(teacher_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de maestro inválido.")

    # 2. Actualizar solo los campos editables con $set
    result = await db.users.update_one(
        {"_id": oid},
        {"$set": {
            "nombre": teacher.nombre,
            "correo": teacher.correo,
            "num_empleado": teacher.num_empleado,
            "telefono": teacher.telefono
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Maestro no encontrado.")

    return {"message": "Maestro actualizado exitosamente."}


# ── Eliminar maestro ──
@admin_router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: str):
    # 1. Convertir el string a ObjectId de MongoDB
    try:
        oid = ObjectId(teacher_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de maestro inválido.")

    # 2. Eliminar el documento
    result = await db.users.delete_one({"_id": oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Maestro no encontrado.")

    return {"message": "Maestro eliminado exitosamente."}