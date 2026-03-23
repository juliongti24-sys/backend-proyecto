from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.v1 import auth, classes, users, challenges, students, trajectory, admin_students, courses, teachers

app = FastAPI(title="API de MathBoost", strict_slashes=False)

# --- GUARDIA DE SEGURIDAD (CORS) ---
# Permitimos TODO temporalmente para depurar y asegurar conectividad
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta uploads
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Rutas con prefijos consistentes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(auth.admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(classes.router, prefix="/api/v1/classes", tags=["Classes"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(challenges.router, prefix="/api/v1/challenges", tags=["Challenges"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(trajectory.router, prefix="/api/v1/trajectory", tags=["Trajectory"])
app.include_router(admin_students.router, prefix="/api/v1/admin/students", tags=["Admin - Students"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])
app.include_router(teachers.router, prefix="/api/v1/teachers", tags=["Teachers"])
