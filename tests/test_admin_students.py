import pytest
from httpx import AsyncClient

# Dependiendo de tu config exacta, debes usar auth_headers para generar encabezados seguros
from .conftest import auth_headers

@pytest.mark.asyncio
async def test_admin_list_students(client: AsyncClient, mock_db):
    """
    Especificación SDD: GET /api/v1/admin/students
    """
    from .conftest import seed_student, seed_teacher
    student = await seed_student(mock_db)
    teacher = await seed_teacher(mock_db)
    
    # 1. Admin accede
    admin_headers = auth_headers("admin_user_1", role="admin")
    resp_admin = await client.get("/api/v1/admin/students", headers=admin_headers)
    assert resp_admin.status_code == 200, "Admin debe poder listar alumnos"
    data = resp_admin.json()
    assert isinstance(data, list)
    
    # 2. RBAC: Estudiante no puede acceder
    student_headers = auth_headers(str(student["_id"]), role="estudiante")
    resp_student = await client.get("/api/v1/admin/students", headers=student_headers)
    assert resp_student.status_code == 403, "Estudiantes deben recibir 403 Forbidden"
    
    # 3. RBAC: Maestro no puede acceder
    teacher_headers = auth_headers(str(teacher["_id"]), role="maestro")
    resp_teacher = await client.get("/api/v1/admin/students", headers=teacher_headers)
    assert resp_teacher.status_code == 403, "Maestros deben recibir 403 Forbidden"


@pytest.mark.asyncio
async def test_admin_create_student(client: AsyncClient):
    """
    Especificación SDD: POST /api/v1/admin/students
    Admin puede crear un alumno nuevo.
    """
    admin_headers = auth_headers("admin_user_1", role="admin")
    payload = {
        "nombre": "Nuevo Alumno Admin",
        "correo": "admin_student@mathboost.com",
        "password": "securepassword123"
    }
    
    resp = await client.post("/api/v1/admin/students", json=payload, headers=admin_headers)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}. Response: {resp.text}"
    data = resp.json()
    assert data["correo"] == payload["correo"]
    assert "password" not in data, "La contraseña no debe exponerse"

@pytest.mark.asyncio
async def test_admin_update_student(client: AsyncClient, mock_db):
    """
    Especificación SDD: PUT /api/v1/admin/students/{student_id}
    Admin puede modificar el perfil de un alumno.
    """
    from .conftest import seed_student
    student = await seed_student(mock_db)
    admin_headers = auth_headers("admin_user_1", role="admin")
    student_id = str(student["_id"])
    
    payload = {
        "nombre": "Estudiante Actualizado por Admin",
    }
    
    resp = await client.put(f"/api/v1/admin/students/{student_id}", json=payload, headers=admin_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}. Response: {resp.text}"

    data = resp.json()
    assert data["nombre"] == payload["nombre"]


@pytest.mark.asyncio
async def test_admin_delete_student(client: AsyncClient, mock_db):
    """
    Especificación SDD: DELETE /api/v1/admin/students/{student_id}
    Admin puede eliminar a un alumno.
    """
    from .conftest import seed_student
    student = await seed_student(mock_db)
    admin_headers = auth_headers("admin_user_1", role="admin")
    student_id = str(student["_id"])
    
    resp = await client.delete(f"/api/v1/admin/students/{student_id}", headers=admin_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}. Response: {resp.text}"
    assert resp.json()["message"] == "Estudiante eliminado exitosamente"
    
    # Si volvemos a intentar eliminar el mismo estudiante, debería ser 404
    resp_retry = await client.delete(f"/api/v1/admin/students/{student_id}", headers=admin_headers)
    assert resp_retry.status_code == 404
