"""
conftest.py – Fixtures compartidos para todos los tests de MathBoost.

Usa mongomock_motor para un motor async client en memoria,
y httpx.AsyncClient vinculado a la app FastAPI.
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from bson import ObjectId

# ──────────────────────────── Event Loop ────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Crear un único event loop para toda la sesión de tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ──────────────────────────── Fake DB ────────────────────────────

@pytest_asyncio.fixture()
async def mock_db():
    """
    Crea un cliente mongomock_motor en memoria y retorna la db 'test_mathboost'.
    Limpia todas las colecciones al finalizar.
    """
    client = AsyncMongoMockClient()
    db = client["test_mathboost"]
    yield db
    # Cleanup: drop all collections
    for col_name in await db.list_collection_names():
        await db.drop_collection(col_name)
    client.close()


# ──────────────────────────── Seed Data IDs ────────────────────────────

STUDENT_ID = str(ObjectId())
STUDENT_ID_2 = str(ObjectId())
TEACHER_ID = str(ObjectId())
CLASS_ID = str(ObjectId())
COURSE_ID = str(ObjectId())


# ──────────────────────────── Seed helpers ────────────────────────────

async def seed_student(db, student_id=STUDENT_ID):
    """Inserta un estudiante de prueba."""
    doc = {
        "_id": ObjectId(student_id),
        "nombre": "Test Student",
        "correo": "student@test.com",
        "matricula": "A00123456",
        "telefono": "5551234567",
        "password": "$2b$12$fakehash",
        "rol": "estudiante",
        "racha": 5,
        "puntos": 100,
    }
    await db.users.insert_one(doc)
    return doc


async def seed_student_2(db, student_id=STUDENT_ID_2):
    """Inserta un segundo estudiante (para pruebas IDOR)."""
    doc = {
        "_id": ObjectId(student_id),
        "nombre": "Other Student",
        "correo": "other@test.com",
        "matricula": "A00654321",
        "telefono": "5559876543",
        "password": "$2b$12$fakehash2",
        "rol": "estudiante",
        "racha": 0,
        "puntos": 0,
    }
    await db.users.insert_one(doc)
    return doc


async def seed_teacher(db, teacher_id=TEACHER_ID):
    """Inserta un maestro de prueba."""
    doc = {
        "_id": ObjectId(teacher_id),
        "nombre": "Test Teacher",
        "correo": "teacher@test.com",
        "num_empleado": "E001",
        "telefono": "5550001111",
        "password": "$2b$12$fakehashteacher",
        "rol": "maestro",
    }
    await db.users.insert_one(doc)
    return doc


async def seed_class(db, class_id=CLASS_ID, teacher_id=TEACHER_ID, students=None):
    """Inserta una clase de prueba con estudiantes enrolados."""
    doc = {
        "_id": ObjectId(class_id),
        "nombre_clase": "Álgebra 101",
        "maestro_id": teacher_id,
        "codigo_acceso": "ABC123",
        "estudiantes": students if students is not None else [STUDENT_ID],
    }
    await db.classes.insert_one(doc)
    return doc


async def seed_course(db, course_id=COURSE_ID):
    """Inserta un curso de prueba con ejercicios estilo Duolingo."""
    doc = {
        "_id": ObjectId(course_id),
        "titulo": "Álgebra Fundamental",
        "descripcion": "Curso de álgebra para pruebas.",
        "nivel": "Intermedio",
        "capitulos": [
            {
                "semana": 1,
                "titulo": "Fundamentos",
                "descripcion": "Leyes de exponentes.",
                "ejercicios": [
                    {
                        "tipo": "opcion_multiple",
                        "pregunta": "Simplifica: $x^3 \\cdot x^5$",
                        "opciones": ["$x^{15}$", "$x^8$", "$2x^8$", "$x^2$"],
                        "respuesta_correcta": "$x^8$",
                        "explicacion": "Exponentes se suman: $3 + 5 = 8$.",
                    },
                    {
                        "tipo": "opcion_multiple",
                        "pregunta": "Calcula: $\\sqrt{16x^4}$",
                        "opciones": ["$4x^2$", "$8x^2$", "$4x$", "$16x^2$"],
                        "respuesta_correcta": "$4x^2$",
                        "explicacion": "Raíz de 16 = 4, exponente 4/2 = 2.",
                    },
                ],
            },
            {
                "semana": 2,
                "titulo": "Polinomios",
                "descripcion": "Operaciones con polinomios.",
                "ejercicios": [
                    {
                        "tipo": "opcion_multiple",
                        "pregunta": "Suma: $(3x^2 + 2x - 5) + (x^2 - 4x + 1)$",
                        "opciones": [
                            "$4x^2 - 2x - 4$",
                            "$2x^2 + 6x - 4$",
                            "$4x^2 + 2x + 4$",
                            "$3x^4 - 2x^2 - 4$",
                        ],
                        "respuesta_correcta": "$4x^2 - 2x - 4$",
                        "explicacion": "Agrupamos términos semejantes.",
                    },
                ],
            },
        ],
    }
    await db.cursos.insert_one(doc)
    return doc


# ──────────────────────────── Auth Headers ────────────────────────────

def auth_headers(user_id: str, role: str = "estudiante") -> dict:
    """Genera headers X-User-ID y X-User-Role para tests autenticados."""
    return {"X-User-ID": user_id, "X-User-Role": role}


# ──────────────────────────── App + Client ────────────────────────────

@pytest_asyncio.fixture()
async def client(mock_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Crea un httpx.AsyncClient conectado a la app FastAPI,
    con la db de la app parcheada al mock_db en memoria.
    """
    # Parchar la db ANTES de importar la app para que todos los módulos la usen
    import app.database as database_module
    database_module.db = mock_db

    from app.main import app as fastapi_app

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
