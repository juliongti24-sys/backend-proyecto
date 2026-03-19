from pydantic import BaseModel, EmailStr, Field

#Creación de un estudiante
class StudentCreate(BaseModel):
    nombre: str = Field(..., min_length=3, description="Nombre completo del estudiante")
    correo: EmailStr = Field(..., description="Correo electrónico válido")
    matricula: str = Field(..., description="Matrícula universitaria")
    telefono: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6, description="Contraseña en texto plano")

#Login
class UserLogin(BaseModel):
    correo: EmailStr = Field(..., description="Correo del usuario")
    password: str = Field(..., description="Contraseña en texto plano")

class TeacherCreate(BaseModel):
    nombre: str
    correo: EmailStr
    num_empleado: str
    telefono: str
    password: str

class TeacherUpdate(BaseModel):
    nombre: str
    correo: EmailStr
    num_empleado: str
    telefono: str