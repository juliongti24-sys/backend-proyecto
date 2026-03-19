from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class ClassBase(BaseModel):
    nombre_clase: str = Field(..., min_length=1, description="Nombre de la clase")

class ClassCreate(ClassBase):
    maestro_id: str = Field(..., description="ID del maestro que crea la clase")

class ClassDB(ClassCreate):
    id: Optional[str] = Field(None, alias="_id")
    codigo_acceso: str = Field(..., min_length=6, max_length=6, description="Código único de 6 caracteres")
    estudiantes: List[str] = Field(default_factory=list, description="Lista de IDs de estudiantes enrolados")
    
    model_config = ConfigDict(populate_by_name=True)
