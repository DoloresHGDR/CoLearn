import logging

from fastapi import HTTPException

from app.models.schemas import AnswerRecord, ClassMetrics, StudentMetrics, StudentProgress
from app.repositories.class_repository import get_class_by_id, is_enrolled
from app.repositories.metrics_repository import get_class_metrics, get_student_answer_history, get_my_stats

logger = logging.getLogger(__name__)


def _calculate_trend(scores: list) -> str:
    """
    Calcula la tendencia de aprendizaje comparando la primera mitad
    de respuestas con la segunda (Siemens & Long, 2011 — Learning Analytics).
    """
    if len(scores) < 2:
        return "sin datos"

    mid = len(scores) // 2
    first_half_avg = sum(scores[:mid]) / mid
    second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

    diff = second_half_avg - first_half_avg
    if diff >= 1:
        return "mejorando"
    elif diff <= -1:
        return "bajando"
    else:
        return "estable"


# Devuelve las métricas de participación y progreso de una clase para el docente
def get_metrics(class_id: str, teacher_id: str) -> ClassMetrics:
    # Verificar que la clase pertenece al docente
    class_row = get_class_by_id(class_id)
    if not class_row:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if class_row["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta clase.")

    rows = get_class_metrics(class_id)

    students = []
    for row in rows:
        # Obtener historial de respuestas para calcular tendencia
        history_rows = get_student_answer_history(class_id, row["student_id"])
        answer_history = [
            AnswerRecord(
                question_id=h["question_id"],
                correct=h["correct"],
                score=h["score"],
                created_at=h["created_at"],
            )
            for h in history_rows
        ]
        scores = [h["score"] for h in history_rows]

        students.append(StudentMetrics(
            student_id=row["student_id"],
            name=row["name"],
            email=row["email"],
            message_count=row["message_count"],
            answers_submitted=row["answers_submitted"],
            average_score=round(float(row["average_score"]), 1),
            score_trend=_calculate_trend(scores),
            answer_history=answer_history,
            joined_at=row["joined_at"],
        ))

    return ClassMetrics(
        class_id=class_id,
        class_name=class_row["name"],
        enrolled_count=len(students),
        students=students,
    )


def _recommended_level(answers_submitted: int, average_score: float) -> str:
    """
    Determina el nivel recomendado según el desempeño del alumno.
    Basado en Mastery Learning (Bloom, 1968): el alumno avanza de nivel
    solo cuando demuestra dominio del nivel actual (≥ 75% de puntaje).
    """
    if answers_submitted < 2 or average_score < 5.0:
        return "easy"
    if average_score < 7.0:
        return "medium"
    return "hard"


# Devuelve el progreso propio del alumno en una clase (para dificultad adaptativa)
def get_my_progress(class_id: str, student_id: str) -> StudentProgress:
    class_row = get_class_by_id(class_id)
    if not class_row:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if not is_enrolled(class_id, student_id):
        raise HTTPException(status_code=403, detail="No estás inscrito en esta clase.")

    row = get_my_stats(class_id, student_id)
    answers_submitted = int(row["answers_submitted"])
    average_score = round(float(row["average_score"]), 1)

    return StudentProgress(
        answers_submitted=answers_submitted,
        average_score=average_score,
        recommended_level=_recommended_level(answers_submitted, average_score),
    )
