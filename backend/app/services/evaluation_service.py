import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.cache import generate_file_hash, load_cache
from app.rag.evaluator import evaluate_answer
from app.rag.reader import read_file
from app.repositories.class_answer_repository import save_student_answer
from app.repositories.class_repository import get_class_by_id, is_enrolled
from app.repositories.question_repository import get_questions_by_class
from app.services.parser_service import parse_evaluation

logger = logging.getLogger(__name__)


def _get_class_text(class_row) -> str:
    """Carga el texto del documento de la clase desde caché o desde disco."""
    file_path = class_row.get("file_path")
    if not file_path:
        return ""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        file_hash = generate_file_hash(content)
        cached = load_cache(file_hash)
        # Usar el texto ya procesado del caché si existe
        if cached and "text" in cached:
            return cached["text"]
        # Si no hay caché, leer el archivo directamente
        return read_file(file_path)
    except Exception as e:
        logger.warning(f"No se pudo cargar el texto de la clase: {e}")
        return ""


# Evalúa la respuesta de un alumno a una pregunta de la clase
def evaluate_student_answer(class_id: str, student_id: str, question_id: int, answer: str) -> dict:
    # Verificar que el alumno pertenece a la clase
    if not is_enrolled(class_id, student_id):
        raise HTTPException(status_code=403, detail="No estás inscripto en esta clase.")

    # Obtener la pregunta solicitada
    questions = get_questions_by_class(class_id)
    question_row = next((q for q in questions if q["id"] == question_id), None)
    if not question_row:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada en esta clase.")

    # Cargar el texto real del documento como contexto para Gemini
    class_row = get_class_by_id(class_id)
    context = _get_class_text(class_row) if class_row else ""

    # Llamar al evaluador de Gemini
    try:
        raw_response = evaluate_answer(
            question=question_row["question"],
            student_answer=answer,
            context=context,
            difficulty=question_row["difficulty"],
        )
    except Exception as e:
        logger.error(f"Error al evaluar respuesta: {e}")
        raise HTTPException(status_code=502, detail=f"Error al evaluar con Gemini: {str(e)}")

    # Parsear la respuesta del evaluador
    result = parse_evaluation(raw_response)

    # Guardar en la base de datos
    now = datetime.now(timezone.utc).isoformat()
    save_student_answer(
        class_id=class_id,
        student_id=student_id,
        question_id=question_id,
        answer=answer,
        correct=result["correct"],
        feedback=result["feedback"],
        score=result["score"],
        created_at=now,
    )

    logger.info(f"Respuesta evaluada: alumno={student_id}, clase={class_id}, resultado={result['correct']}")
    return result
