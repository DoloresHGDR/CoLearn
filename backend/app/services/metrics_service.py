import logging

from fastapi import HTTPException

from app.models.schemas import ClassMetrics, StudentMetrics
from app.repositories.class_repository import get_class_by_id
from app.repositories.metrics_repository import get_class_metrics

logger = logging.getLogger(__name__)


# Devuelve las métricas de participación de una clase para el docente
def get_metrics(class_id: str, teacher_id: str) -> ClassMetrics:
    # Verificar que la clase pertenece al docente
    class_row = get_class_by_id(class_id)
    if not class_row:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if class_row["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta clase.")

    rows = get_class_metrics(class_id)

    students = [
        StudentMetrics(
            student_id=row["student_id"],
            name=row["name"],
            email=row["email"],
            message_count=row["message_count"],
            answers_submitted=row["answers_submitted"],
            average_score=round(float(row["average_score"]), 1),
            joined_at=row["joined_at"],
        )
        for row in rows
    ]

    return ClassMetrics(
        class_id=class_id,
        class_name=class_row["name"],
        enrolled_count=len(students),
        students=students,
    )
