"""
trajectory.py – Endpoints del motor de trayectoria estilo Duolingo.

Lee cursos de la colección 'cursos', sirve preguntas en LaTeX,
valida respuestas y asigna puntos.

Seguridad:
  - Solo estudiantes autenticados (require_role("estudiante")).
"""
from fastapi import APIRouter, HTTPException, status, Depends

from app.core.security import require_role
from app.models.activities import TrajectoryAnswer
from app.services import trajectory_service

router = APIRouter()

_student_guard = require_role("estudiante")


# ═══════════════════════ Listar cursos ═══════════════════════

@router.get(
    "/api/v1/trajectory/courses",
    status_code=status.HTTP_200_OK,
)
async def list_courses(current_user: dict = Depends(_student_guard)):
    return await trajectory_service.get_courses()


# ════════════════════ Preguntas de un capítulo ════════════════════

@router.get(
    "/api/v1/trajectory/courses/{course_id}/chapters/{chapter_index}/questions",
    status_code=status.HTTP_200_OK,
)
async def get_chapter_questions(
    course_id: str,
    chapter_index: int,
    current_user: dict = Depends(_student_guard),
):
    try:
        return await trajectory_service.get_chapter_questions(course_id, chapter_index)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de curso inválido.")
    except LookupError:
        raise HTTPException(status_code=404, detail="Curso no encontrado.")
    except IndexError:
        raise HTTPException(status_code=404, detail="Capítulo fuera de rango.")


# ════════════════════ Validar respuesta ════════════════════

@router.post(
    "/api/v1/trajectory/answer",
    status_code=status.HTTP_200_OK,
)
async def submit_answer(
    body: TrajectoryAnswer,
    current_user: dict = Depends(_student_guard),
):
    try:
        return await trajectory_service.validate_answer(
            student_id=current_user["user_id"],
            course_id=body.course_id,
            chapter_index=body.chapter_index,
            question_index=body.question_index,
            answer=body.answer,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de curso inválido.")
    except LookupError:
        raise HTTPException(status_code=404, detail="Curso no encontrado.")
    except IndexError:
        raise HTTPException(status_code=404, detail="Pregunta fuera de rango.")
