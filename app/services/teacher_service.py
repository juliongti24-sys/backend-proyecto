from bson import ObjectId
from app import database
from typing import List, Dict, Any

async def get_teacher_analytics(teacher_id: str) -> Dict[str, Any]:
    """
    Obtiene analíticas detalladas de los grupos de un maestro.
    """
    # 1. Obtener todas las clases del maestro
    cursor = database.db.classes.find({"maestro_id": teacher_id})
    clases = await cursor.to_list(length=100)
    
    if not clases:
        return {
            "total_clases": 0,
            "total_alumnos": 0,
            "promedio_general_puntos": 0,
            "clases": [],
            "estudiantes": []
        }

    # 2. Recopilar IDs de todos los estudiantes únicos
    student_ids = set()
    for clase in clases:
        student_ids.update(clase.get("estudiantes", []))
    
    # 3. Obtener datos de los estudiantes
    students_data = []
    if student_ids:
        # Convertir IDs a ObjectId si es necesario (asumiendo que se guardan como strings en classes.estudiantes)
        # pero en users son ObjectIds. 
        # IMPORTANTE: En classes.estudiantes se guardan como STRINGS según clases.py:76
        cursor_students = database.db.users.find({
            "_id": {"$in": [ObjectId(sid) for sid in student_ids]}
        }, {"password": 0})
        students_list = await cursor_students.to_list(length=500)
        
        for s in students_list:
            s["_id"] = str(s["_id"])
            students_data.append(s)

    # 4. Calcular estadísticas por clase
    clases_stats = []
    total_puntos_suma = 0
    alumnos_contados = 0

    for clase in clases:
        c_students_ids = clase.get("estudiantes", [])
        c_students = [s for s in students_data if s["_id"] in c_students_ids]
        
        puntos_clase = [s.get("puntos", 0) for s in c_students]
        promedio_puntos = sum(puntos_clase) / len(puntos_clase) if puntos_clase else 0
        
        total_puntos_suma += sum(puntos_clase)
        alumnos_contados += len(puntos_clase)
        
        clases_stats.append({
            "id": str(clase["_id"]),
            "nombre": clase["nombre_clase"],
            "total_alumnos": len(c_students),
            "promedio_puntos": promedio_puntos,
            "alumnos": [
                {"nombre": s["nombre"], "puntos": s.get("puntos", 0), "racha": s.get("racha", 0)}
                for s in c_students
            ]
        })

    promedio_general = total_puntos_suma / alumnos_contados if alumnos_contados > 0 else 0

    return {
        "total_clases": len(clases),
        "total_alumnos": len(student_ids),
        "promedio_general_puntos": promedio_general,
        "clases": clases_stats,
        "estudiantes_top": sorted(students_data, key=lambda x: x.get("puntos", 0), reverse=True)[:10]
    }
