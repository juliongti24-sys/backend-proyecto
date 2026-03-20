from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import auth, classes, users, challenges

app = FastAPI(title="API de MathBoost")

# --- GUARDIA DE SEGURIDAD (CORS) ---
# Esto le dice a FastAPI: "Permite que cualquier frontend se conecte conmigo"

origins = [
    "frontend-proyecto-integrador-nine.vercel.app",  # URL de producción
    "http://localhost:3000",          # Para seguir probando local
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # El asterisco permite CUALQUIER origen
    allow_credentials=False,  # DEBE ser False cuando usamos el asterisco "*"
    allow_methods=["*"],      # Permite POST, GET, etc.
    allow_headers=["*"],      # Permite cualquier encabezado
)

# Montar carpeta uploads
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Rutas
app.include_router(auth.router, tags=["Auth"])
app.include_router(classes.router, tags=["Classes"])
app.include_router(users.router, tags=["Users"])
app.include_router(challenges.router, tags=["Challenges"])
