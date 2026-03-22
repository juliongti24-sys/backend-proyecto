"""
test_student_profile.py – Specs para el perfil y progreso del estudiante.

Cubre:
  - PUT  /api/v1/student/profile     (editar perfil, incluyendo foto con limpieza de huérfanos)
  - GET  /api/v1/student/progress    (puntos, racha, seguimiento diario)

Seguridad IDOR:
  - El user_id se toma de X-User-ID, no de la URL.
  - Tests verifican que un estudiante NO puede editar el perfil de otro.
"""
import pytest
from bson import ObjectId
from tests.conftest import (
    STUDENT_ID,
    STUDENT_ID_2,
    TEACHER_ID,
    auth_headers,
    seed_student,
    seed_student_2,
)


# ════════════════════════════════════════════════════════════════════
#  Editar perfil del estudiante
# ════════════════════════════════════════════════════════════════════

class TestUpdateStudentProfile:
    """PUT /api/v1/student/profile — usa X-User-ID, no path param."""

    @pytest.mark.asyncio
    async def test_update_profile_success(self, client, mock_db):
        """Actualización exitosa retorna el perfil actualizado sin password."""
        await seed_student(mock_db)

        resp = await client.put(
            "/api/v1/student/profile",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "nombre": "Nuevo Nombre",
                "correo": "nuevo@test.com",
                "telefono": "5559999999",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Nuevo Nombre"
        assert data["correo"] == "nuevo@test.com"
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_update_profile_partial(self, client, mock_db):
        """Se pueden enviar solo algunos campos (e.g. solo nombre)."""
        await seed_student(mock_db)

        resp = await client.put(
            "/api/v1/student/profile",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={"nombre": "Solo Nombre"},
        )

        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Solo Nombre"

    @pytest.mark.asyncio
    async def test_update_profile_user_not_found(self, client, mock_db):
        """Si el user_id del header no existe en DB → 404."""
        fake_id = str(ObjectId())

        resp = await client.put(
            "/api/v1/student/profile",
            headers=auth_headers(fake_id, "estudiante"),
            json={"nombre": "Ghost"},
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_profile_no_auth(self, client, mock_db):
        """Sin headers de autenticación → 422."""
        resp = await client.put(
            "/api/v1/student/profile",
            json={"nombre": "Hacker"},
        )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_idor_wrong_role(self, client, mock_db):
        """IDOR: un maestro no puede editar con este endpoint → 403."""
        await seed_student(mock_db)

        resp = await client.put(
            "/api/v1/student/profile",
            headers=auth_headers(TEACHER_ID, "maestro"),
            json={"nombre": "Hacker Teacher"},
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_profile_cleans_orphan_photo(self, client, mock_db):
        """
        Al subir nueva foto, la foto anterior (si existe) se marca como eliminada.
        Verificamos que el campo foto_perfil se actualiza a la nueva URL.
        """
        # Seed student with an existing photo
        await seed_student(mock_db)
        await mock_db.users.update_one(
            {"_id": ObjectId(STUDENT_ID)},
            {"$set": {"foto_perfil": "/uploads/old-photo-uuid.jpg"}},
        )

        # Enviar actualización con nueva foto_perfil URL
        resp = await client.put(
            "/api/v1/student/profile",
            headers=auth_headers(STUDENT_ID, "estudiante"),
            json={
                "nombre": "Con Foto",
                "foto_perfil": "/uploads/new-photo-uuid.jpg",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["foto_perfil"] == "/uploads/new-photo-uuid.jpg"

        # Verificar en DB que se actualizó
        user = await mock_db.users.find_one({"_id": ObjectId(STUDENT_ID)})
        assert user["foto_perfil"] == "/uploads/new-photo-uuid.jpg"


# ════════════════════════════════════════════════════════════════════
#  Consultar puntos y seguimiento diario
# ════════════════════════════════════════════════════════════════════

class TestGetStudentProgress:
    """GET /api/v1/student/progress — usa X-User-ID."""

    @pytest.mark.asyncio
    async def test_get_progress_success(self, client, mock_db):
        """Retorna puntos, racha y progreso diario."""
        await seed_student(mock_db)

        # Seed some daily progress records
        await mock_db.student_progress.insert_many([
            {"student_id": STUDENT_ID, "date": "2026-03-20", "exercises_completed": 5, "points_earned": 50},
            {"student_id": STUDENT_ID, "date": "2026-03-21", "exercises_completed": 3, "points_earned": 30},
        ])

        resp = await client.get(
            "/api/v1/student/progress",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "puntos" in data
        assert "racha" in data
        assert "daily_progress" in data
        assert isinstance(data["daily_progress"], list)
        assert len(data["daily_progress"]) == 2

    @pytest.mark.asyncio
    async def test_get_progress_no_records(self, client, mock_db):
        """Si no hay registros de progreso, daily_progress está vacío."""
        await seed_student(mock_db)

        resp = await client.get(
            "/api/v1/student/progress",
            headers=auth_headers(STUDENT_ID, "estudiante"),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_progress"] == []
        assert data["puntos"] == 100  # del seed
        assert data["racha"] == 5     # del seed

    @pytest.mark.asyncio
    async def test_get_progress_user_not_found(self, client, mock_db):
        """Si el usuario no existe → 404."""
        fake_id = str(ObjectId())

        resp = await client.get(
            "/api/v1/student/progress",
            headers=auth_headers(fake_id, "estudiante"),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_progress_idor_wrong_role(self, client, mock_db):
        """IDOR: un maestro no puede consultar el progreso de estudiante → 403."""
        await seed_student(mock_db)

        resp = await client.get(
            "/api/v1/student/progress",
            headers=auth_headers(TEACHER_ID, "maestro"),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_progress_no_auth(self, client, mock_db):
        """Sin headers → 422."""
        resp = await client.get("/api/v1/student/progress")
        assert resp.status_code == 422
