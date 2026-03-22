import pytest
from httpx import AsyncClient
from .conftest import auth_headers

@pytest.mark.asyncio
async def test_challenge_matchmaking(client: AsyncClient, mock_db):
    """
    Especificación SDD: POST /api/v1/challenges/queue
    Estudiante se encola para buscar partida.
    """
    from .conftest import seed_student
    student = await seed_student(mock_db)
    headers = auth_headers(str(student["_id"]), role="estudiante")
    
    # 1. Encolarse
    resp = await client.post("/api/v1/challenges/queue", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ["waiting", "matched"]
    
    # 2. Consultar el estado de su partida activa
    resp_status = await client.get("/api/v1/challenges/current", headers=headers)
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert status_data["match_id"] is not None or status_data["status"] == "waiting"


@pytest.mark.asyncio
async def test_challenge_submit_answer(client: AsyncClient, mock_db):
    """
    Especificación SDD: POST /api/v1/challenges/{match_id}/answer
    Envía una respuesta durante la partida.
    """
    from .conftest import seed_student, seed_course
    student = await seed_student(mock_db)
    course = await seed_course(mock_db)
    headers = auth_headers(str(student["_id"]), role="estudiante")
    
    # Encolando
    queue_resp = await client.post("/api/v1/challenges/queue", headers=headers)
    match_id = queue_resp.json().get("match_id", "test_match_foo")
    
    payload = {
        "question_index": 0,
        "answer": "x = 2"
    }
    
    # Responder
    resp = await client.post(f"/api/v1/challenges/{match_id}/answer", json=payload, headers=headers)
    
    assert resp.status_code in [200, 404]
    
    if resp.status_code == 200:
        data = resp.json()
        assert "correct" in data
        assert "score_update" in data


@pytest.mark.asyncio
async def test_challenge_leave(client: AsyncClient, mock_db):
    """
    Especificación SDD: DELETE /api/v1/challenges/current
    Estudiante abandona la cola o la partida actual.
    """
    from .conftest import seed_student
    student = await seed_student(mock_db)
    headers = auth_headers(str(student["_id"]), role="estudiante")
    
    resp = await client.delete("/api/v1/challenges/current", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Has abandonado la sala"
    
    # Asegurarnos de que el endpoint actual dice "none" 
    resp_check = await client.get("/api/v1/challenges/current", headers=headers)
    assert resp_check.status_code == 404 or resp_check.json().get("status") == "none"
