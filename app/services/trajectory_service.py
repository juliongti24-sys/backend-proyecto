"""
trajectory_service.py - Motor de trayectoria estilo Duolingo.
"""
from datetime import date
from typing import Dict, Any, List
from bson import ObjectId
from app import database

async def get_courses() -> List[Dict[str, Any]]:
    cursor = database.db.cursos.find({})
    courses = await cursor.to_list(length=100)
    
    result = []
    for c in courses:
        result.append({
            "_id": str(c["_id"]),
            "titulo": c.get("titulo"),
            "descripcion": c.get("descripcion"),
            "nivel": c.get("nivel"),
            "num_capitulos": len(c.get("capitulos", []))
        })
    return result

async def get_chapter_questions(course_id: str, chapter_index: int) -> Dict[str, Any]:
    try:
        oid = ObjectId(course_id)
    except Exception:
        raise ValueError("ID de curso inválido")
        
    curso = await database.db.cursos.find_one({"_id": oid})
    if not curso:
        raise LookupError("Curso no encontrado")
        
    capitulos = curso.get("capitulos", [])
    if chapter_index < 0 or chapter_index >= len(capitulos):
        raise LookupError("Capítulo no encontrado")
        
    capitulo = capitulos[chapter_index]
    ejercicios_publicos = []
    
    for idx, ej in enumerate(capitulo.get("ejercicios", [])):
        ejercicios_publicos.append({
            "question_index": idx,
            "pregunta": ej.get("pregunta"),
            "opciones": ej.get("opciones"),
            "tipo": ej.get("tipo", "opcion_multiple")
        })
        
    return {
        "titulo": capitulo.get("titulo"),
        "ejercicios": ejercicios_publicos
    }

async def validate_answer(student_id: str, course_id: str, chapter_index: int, question_index: int, answer: str) -> Dict[str, Any]:
    try:
        c_oid = ObjectId(course_id)
        s_oid = ObjectId(student_id)
    except Exception:
        raise ValueError("ID no válido")

    curso = await database.db.cursos.find_one({"_id": c_oid})
    if not curso:
        raise LookupError("Curso no encontrado")

    capitulos = curso.get("capitulos", [])
    if chapter_index < 0 or chapter_index >= len(capitulos):
        raise LookupError("Capítulo no encontrado")
        
    ejercicios = capitulos[chapter_index].get("ejercicios", [])
    if question_index < 0 or question_index >= len(ejercicios):
        raise LookupError("Pregunta no encontrada")
        
    ejercicio = ejercicios[question_index]
    correct_answer = ejercicio.get("respuesta_correcta", "").strip()
    is_correct = (answer.strip() == correct_answer)
    points_earned = 10 if is_correct else 0
    
    if is_correct:
        # Puntos de usuario
        await database.db.users.update_one(
            {"_id": s_oid},
            {"$inc": {"puntos": points_earned}}
        )
        
        # Progreso diario
        today_str = date.today().isoformat()
        await database.db.student_progress.update_one(
            {"student_id": student_id, "date": today_str},
            {
                "$inc": {"exercises_completed": 1, "points_earned": points_earned},
                "$setOnInsert": {"student_id": student_id, "date": today_str}
            },
            upsert=True
        )

    return {
        "correct": is_correct,
        "explicacion": ejercicio.get("explicacion", ""),
        "points_earned": points_earned
    }
