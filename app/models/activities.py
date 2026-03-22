"""
Modelos Pydantic para Actividades y Progreso del Estudiante.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ──────────────────────── Ejercicio ────────────────────────

class Exercise(BaseModel):
    tipo: str = Field(default="opcion_multiple")
    pregunta: str
    opciones: List[str]
    respuesta_correcta: str
    explicacion: str


class ExercisePublic(BaseModel):
    """Ejercicio sin respuesta correcta — para enviar al estudiante."""
    tipo: str
    pregunta: str
    opciones: List[str]
    question_index: int


# ──────────────────────── Actividad ────────────────────────

class ActivityCreate(BaseModel):
    class_id: str = Field(..., description="ID de la clase")
    titulo: str = Field(..., min_length=1)
    descripcion: Optional[str] = ""
    fecha_limite: Optional[str] = None
    # Referencia a ejercicios del curso
    course_id: Optional[str] = None
    chapter_index: Optional[int] = None
    ejercicios: List[dict] = Field(default_factory=list)


class ActivityUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_limite: Optional[str] = None
    ejercicios: Optional[List[dict]] = None


# ──────────────────────── Progreso ────────────────────────

class DailyProgress(BaseModel):
    student_id: str
    date: str
    exercises_completed: int = 0
    points_earned: int = 0


# ──────────────────────── Perfil estudiante ────────────────────────

class StudentProfileUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    foto_perfil: Optional[str] = None


# ──────────────────────── Respuesta trayectoria ────────────────────────

class TrajectoryAnswer(BaseModel):
    course_id: str
    chapter_index: int
    question_index: int
    answer: str
