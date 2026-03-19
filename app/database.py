import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
# 1. Cargar las variables de entorno desde el archivo .env
load_dotenv()

# 2. Obtener la URL de forma segura
MONGO_URL = os.getenv("MONGO_URL")

# Validación de seguridad: Si olvidamos crear el .env, el programa nos avisará
if not MONGO_URL:
    raise ValueError("ERROR: No se encontró la variable MONGO_URL en el archivo .env")

# 3. Creamos el cliente asíncrono de Motor
client = AsyncIOMotorClient(MONGO_URL)

# 4. Seleccionamos la base de datos (MathBoost)
db = client.mathboost_db

print(" Conectando a la base de datos MongoDB Atlas (credenciales seguras)...")