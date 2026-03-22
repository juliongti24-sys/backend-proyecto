"""
test_student_classes.py – Specs para endpoints de clases del estudiante.

Cubre:
  - DELETE /api/v1/student/classes/{class_id}/leave  (darse de baja)
  - GET    /api/v1/student/classes/{class_id}/activities  (consultar actividades/avisos)

Seguridad IDOR:
  - Cada test autenticado verifica que un estudiante NO puede actuar en nombre de otro.
"""
import pytest
from bson import ObjectId
from tests.conftest import (
    STUDENT_ID,
    STUDENT_ID_2,
    TEACHER_ID,
    CLASS_ID,
    auth_headers,
    seed_student,
    seed_student_2,
    seed_class,
)


# ════════════════════════════════════════════════════════════════════
#  Darse de baja de una clase
# ════════════════════════════════════════════════════════════════════

class TestLeaveClass:
    """DELETE /api/v1/student/classes/{class_id}/leave"""

    @pytest.mark.asyncio
    async def test_leave_class_success(self, client, mock_db):
        """El estudiante autenticado puede darse de baja de una clase en la que está inscrito."""
        await seed_student(mock_db)
        await seed_class(mock_db, students=[STUDENT_ID])

        resp = await client.delete(
            f"/api/v1/student/classes/{CLASS_ID}/leave",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data

        # Verificar en la DB que el estudiante ya no está en la lista
        clase = await mock_db.classes.find_one({"_id": ObjectId(CLASS_ID)})
        assert STUDENT_ID not in clase["estudiantes"]

    @pytest.mark.asyncio
    async def test_leave_class_not_enrolled(self, client, mock_db):
        """Si el estudiante no está inscrito en la clase, retorna 400."""
        await seed_student(mock_db)
        await seed_class(mock_db, students=[])  # sin estudiantes

        resp = await client.delete(
            f"/api/v1/student/classes/{CLASS_ID}/leave",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_leave_class_not_found(self, client, mock_db):
        """Si la clase no existe, retorna 404."""
        await seed_student(mock_db)
        fake_class_id = str(ObjectId())

        resp = await client.delete(
            f"/api/v1/student/classes/{fake_class_id}/leave",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_leave_class_invalid_id(self, client, mock_db):
        """Si el ID de clase es inválido, retorna 400."""
        await seed_student(mock_db)

        resp = await client.delete(
            "/api/v1/student/classes/invalid-id/leave",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_leave_class_no_auth(self, client, mock_db):
        """Sin headers de autenticación → 422 (header requerido faltante)."""
        resp = await client.delete(f"/api/v1/student/classes/{CLASS_ID}/leave")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_leave_class_idor_forbidden(self, client, mock_db):
        """
        IDOR: un maestro NO puede usar el endpoint de estudiante → 403.
        """
        await seed_student(mock_db)
        await seed_class(mock_db, students=[STUDENT_ID])

        resp = await client.delete(
            f"/api/v1/student/classes/{CLASS_ID}/leave",
            headers=auth_headers(TEACHER_ID, "maestro"),  # Rol incorrecto
        )

        assert resp.status_code == 403


# ════════════════════════════════════════════════════════════════════
#  Consultar actividades / avisos de una clase
# ════════════════════════════════════════════════════════════════════

class TestGetClassActivities:
    """GET /api/v1/student/classes/{class_id}/activities"""

    @pytest.mark.asyncio
    async def test_get_activities_success(self, client, mock_db):
        """Retorna lista de actividades asignadas a la clase."""
        await seed_student(mock_db)
        await seed_class(mock_db, students=[STUDENT_ID])

        # Insertar una actividad para la clase
        await mock_db.activities.insert_one({
            "class_id": CLASS_ID,
            "titulo": "Actividad de Prueba",
            "descripcion": "Resolver ejercicios de semana 1",
            "ejercicios": [],
            "fecha_limite": "2026-04-01",
        })

        resp = await client.get(
            f"/api/v1/student/classes/{CLASS_ID}/activities",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["titulo"] == "Actividad de Prueba"

    @pytest.mark.asyncio
    async def test_get_activities_empty(self, client, mock_db):
        """Si no hay actividades, retorna lista vacía."""
        await seed_student(mock_db)
        await seed_class(mock_db, students=[STUDENT_ID])

        resp = await client.get(
            f"/api/v1/student/classes/{CLASS_ID}/activities",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_activities_class_not_found(self, client, mock_db):
        """Clase inexistente → 404."""
        await seed_student(mock_db)
        fake = str(ObjectId())

        resp = await client.get(
            f"/api/v1/student/classes/{fake}/activities",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_activities_not_enrolled(self, client, mock_db):
        """Si el estudiante no está inscrito en la clase → 403."""
        await seed_student(mock_db)
        await seed_class(mock_db, students=[])  # sin el estudiante

        resp = await client.get(
            f"/api/v1/student/classes/{CLASS_ID}/activities",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_activities_idor_wrong_role(self, client, mock_db):
        """IDOR: un maestro no puede consultar como estudiante → 403."""
        await seed_class(mock_db, students=[STUDENT_ID])

        resp = await client.get(
            f"/api/v1/student/classes/{CLASS_ID}/activities",
            headers=auth_headers(TEACHER_ID, "maestro"),
        )

        assert resp.status_code == 403
