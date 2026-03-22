import asyncio
from httpx import AsyncClient, ASGITransport
import app.main as main_app
import app.database as database_module
from mongomock_motor import AsyncMongoMockClient

async def debug_create_student():
    # Setup mock DB
    client_mock = AsyncMongoMockClient()
    db = client_mock["test_mathboost"]
    database_module.db = db
    
    transport = ASGITransport(app=main_app.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "nombre": "Nuevo Alumno Admin",
            "correo": "admin_student@mathboost.com",
            "password": "123456"
        }
        headers = {"X-User-ID": "admin_user_1", "X-User-Role": "admin"}
        
        print("Enviando POST a /api/v1/admin/students...")
        resp = await client.post("/api/v1/admin/students", json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(debug_create_student())
