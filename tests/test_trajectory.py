"""
test_trajectory.py – Specs para el motor de trayectoria estilo Duolingo.

Cubre:
  - GET  /api/v1/trajectory/courses                                   (listar cursos)
  - GET  /api/v1/trajectory/courses/{course_id}/chapters/{idx}/questions  (preguntas LaTeX)
  - POST /api/v1/trajectory/answer                                    (validar respuesta)

Seguridad:
  - Solo estudiantes autenticados pueden acceder.
  - Las respuestas correctas se ocultan en GET pero se validan en POST.
"""
import pytest
from bson import ObjectId
from tests.conftest import (
    STUDENT_ID,
    TEACHER_ID,
    COURSE_ID,
    auth_headers,
    seed_student,
    seed_course,
)


# ════════════════════════════════════════════════════════════════════
#  Listar cursos disponibles
# ════════════════════════════════════════════════════════════════════

class TestListCourses:
    """GET /api/v1/trajectory/courses"""

    @pytest.mark.asyncio
    async def test_list_courses_success(self, client, mock_db):
        """Retorna lista de cursos con titulo, descripcion, nivel y número de capítulos."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        resp = await client.get(
            "/api/v1/trajectory/courses",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        curso = data[0]
        assert "titulo" in curso
        assert "descripcion" in curso
        assert "nivel" in curso
        assert "num_capitulos" in curso
        # No debe incluir los ejercicios completos
        assert "capitulos" not in curso

    @pytest.mark.asyncio
    async def test_list_courses_empty(self, client, mock_db):
        """Si no hay cursos, retorna lista vacía."""
        await seed_student(mock_db)

        resp = await client.get(
            "/api/v1/trajectory/courses",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_courses_no_auth(self, client, mock_db):
        """Sin headers → 422."""
        resp = await client.get("/api/v1/trajectory/courses")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_courses_wrong_role(self, client, mock_db):
        """IDOR: un maestro no puede acceder al endpoint de trayectoria → 403."""
        resp = await client.get(
            "/api/v1/trajectory/courses",
            headers=auth_headers(TEACHER_ID, "maestro"),
        )
        assert resp.status_code == 403


# ════════════════════════════════════════════════════════════════════
#  Obtener preguntas de un capítulo
# ════════════════════════════════════════════════════════════════════

class TestGetChapterQuestions:
    """GET /api/v1/trajectory/courses/{course_id}/chapters/{chapter_index}/questions"""

    @pytest.mark.asyncio
    async def test_get_questions_success(self, client, mock_db):
        """Retorna preguntas con LaTeX (pregunta + opciones) pero SIN respuesta_correcta."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        resp = await client.get(
            f"/api/v1/trajectory/courses/{COURSE_ID}/chapters/0/questions",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "titulo" in data       # título del capítulo
        assert "ejercicios" in data
        assert len(data["ejercicios"]) >= 1

        # Cada ejercicio tiene pregunta y opciones en LaTeX
        ejercicio = data["ejercicios"][0]
        assert "pregunta" in ejercicio
        assert "$" in ejercicio["pregunta"]  # Contiene LaTeX
        assert "opciones" in ejercicio
        assert len(ejercicio["opciones"]) >= 3

        # SEGURIDAD: NO debe exponer la respuesta correcta
        assert "respuesta_correcta" not in ejercicio

    @pytest.mark.asyncio
    async def test_get_questions_course_not_found(self, client, mock_db):
        """Curso inexistente → 404."""
        await seed_student(mock_db)
        fake_id = str(ObjectId())

        resp = await client.get(
            f"/api/v1/trajectory/courses/{fake_id}/chapters/0/questions",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_questions_chapter_out_of_range(self, client, mock_db):
        """Índice de capítulo fuera de rango → 404."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        resp = await client.get(
            f"/api/v1/trajectory/courses/{COURSE_ID}/chapters/99/questions",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_questions_invalid_course_id(self, client, mock_db):
        """ID de curso inválido → 400."""
        await seed_student(mock_db)

        resp = await client.get(
            "/api/v1/trajectory/courses/not-valid/chapters/0/questions",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 400


# ════════════════════════════════════════════════════════════════════
#  Validar respuesta y asignar puntos
# ════════════════════════════════════════════════════════════════════

class TestSubmitAnswer:
    """POST /api/v1/trajectory/answer"""

    @pytest.mark.asyncio
    async def test_correct_answer(self, client, mock_db):
        """Respuesta correcta: retorna correct=True, explicacion, points_earned > 0."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        resp = await client.post(
            "/api/v1/trajectory/answer",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "course_id": COURSE_ID,
                "chapter_index": 0,
                "question_index": 0,
                "answer": "$x^8$",  # Respuesta correcta del seed
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is True
        assert "explicacion" in data
        assert data["points_earned"] > 0

        # Verificar que los puntos se actualizaron en la DB
        user = await mock_db.users.find_one({"_id": ObjectId(STUDENT_ID)})
        assert user["puntos"] > 100  # tenía 100 iniciales

    @pytest.mark.asyncio
    async def test_incorrect_answer(self, client, mock_db):
        """Respuesta incorrecta: correct=False, explicacion, points_earned=0."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        resp = await client.post(
            "/api/v1/trajectory/answer",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "course_id": COURSE_ID,
                "chapter_index": 0,
                "question_index": 0,
                "answer": "$x^{15}$",  # Respuesta incorrecta
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is False
        assert "explicacion" in data
        assert data["points_earned"] == 0

    @pytest.mark.asyncio
    async def test_answer_course_not_found(self, client, mock_db):
        """Curso inexistente → 404."""
        await seed_student(mock_db)
        fake_id = str(ObjectId())

        resp = await client.post(
            "/api/v1/trajectory/answer",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "course_id": fake_id,
                "chapter_index": 0,
                "question_index": 0,
                "answer": "X",
            },
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_answer_question_out_of_range(self, client, mock_db):
        """Índice de pregunta fuera de rango → 404."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        resp = await client.post(
            "/api/v1/trajectory/answer",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "course_id": COURSE_ID,
                "chapter_index": 0,
                "question_index": 99,
                "answer": "X",
            },
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_answer_no_auth(self, client, mock_db):
        """Sin headers → 422."""
        resp = await client.post(
            "/api/v1/trajectory/answer",
            json={
                "course_id": COURSE_ID,
                "chapter_index": 0,
                "question_index": 0,
                "answer": "X",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_answer_wrong_role(self, client, mock_db):
        """IDOR: maestro no puede responder ejercicios → 403."""
        await seed_course(mock_db)

        resp = await client.post(
            "/api/v1/trajectory/answer",
            headers=auth_headers(TEACHER_ID, "maestro"),
            json={
                "course_id": COURSE_ID,
                "chapter_index": 0,
                "question_index": 0,
                "answer": "$x^8$",
            },
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_answer_records_daily_progress(self, client, mock_db):
        """Al responder correctamente, se registra progreso diario en student_progress."""
        await seed_student(mock_db)
        await seed_course(mock_db)

        await client.post(
            "/api/v1/trajectory/answer",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "course_id": COURSE_ID,
                "chapter_index": 0,
                "question_index": 0,
                "answer": "$x^8$",
            },
        )

        # Verificar que se creó registro de progreso diario
        progress = await mock_db.student_progress.find_one(
            {"student_id": STUDENT_ID}
        )
        assert progress is not None
        assert progress["exercises_completed"] >= 1
