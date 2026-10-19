import logging
from collections import defaultdict

from fastapi import HTTPException

from app.models.schemas import AnswerRecord, ClassMetrics, StudentMetrics
from app.repositories.class_repository import get_class_by_id
from app.repositories.feedback_repository import get_feedback_stats
from app.repositories.metrics_repository import get_class_metrics, get_student_answer_history

logger = logging.getLogger(__name__)


def _score_by_difficulty(history_rows: list) -> dict:
    """
    Calcula el puntaje promedio por nivel de dificultad (easy/medium/hard).
    Solo incluye niveles con al menos una respuesta.
    Más honesto que una tendencia temporal porque las preguntas tienen distinta dificultad.
    """
    scores = defaultdict(list)
    for h in history_rows:
        scores[h["difficulty"]].append(h["score"])
    return {
        level: round(sum(vals) / len(vals), 1)
        for level, vals in scores.items()
    }


# Devuelve las métricas de participación y progreso de una clase para el docente
def get_metrics(class_id: str, teacher_id: str) -> ClassMetrics:
    class_row = get_class_by_id(class_id)
    if not class_row:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if class_row["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta clase.")

    rows = get_class_metrics(class_id)

    students = []
    for row in rows:
        history_rows = get_student_answer_history(class_id, row["student_id"])
        answer_history = [
            AnswerRecord(
                question_id=h["question_id"],
                correct=h["correct"],
                score=h["score"],
                difficulty=h["difficulty"],
                created_at=h["created_at"],
            )
            for h in history_rows
        ]

        students.append(StudentMetrics(
            student_id=row["student_id"],
            name=row["name"],
            email=row["email"],
            message_count=row["message_count"],
            answers_submitted=row["answers_submitted"],
            average_score=round(float(row["average_score"]), 1),
            score_by_difficulty=_score_by_difficulty(history_rows),
            answer_history=answer_history,
            joined_at=row["joined_at"],
        ))

    feedback = get_feedback_stats(class_id)

    return ClassMetrics(
        class_id=class_id,
        class_name=class_row["name"],
        enrolled_count=len(students),
        students=students,
        feedback_total=feedback["total"],
        feedback_positive=feedback["positive"],
    )


def _recommended_level(answers_submitted: int, average_score: float) -> str:
    """
    Determina el nivel recomendado según el desempeño del alumno.
    Basado en Mastery Learning (Bloom, 1968): el alumno avanza de nivel
    solo cuando demuestra dominio del nivel actual.
    Menos de 2 respuestas o promedio < 5/10 → "easy"; promedio < 7/10 → "medium";
    desde 7/10 (≥ 70 % de puntaje) → "hard".
    """
    if answers_submitted < 2 or average_score < 5.0:
        return "easy"
    if average_score < 7.0:
        return "medium"
    return "hard"
