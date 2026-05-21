"""
Servicio encargado de transformar la respuesta del modelo
en estructuras utilizables por el sistema.

Se utiliza para:
- extraer preguntas
- obtener introducción y reflexión
- parsear evaluaciones de Gemini
- convertir texto en modelos Pydantic
"""

from app.models.schemas import Question

# Etiquetas que usa el modelo para generar actividades
_LABELS = [
    "INTRODUCTION:",
    "QUESTION EASY:",
    "QUESTION MEDIUM:",
    "QUESTION HARD:",
    "REFLECTION:",
]

# Etiquetas que usa Gemini para evaluar respuestas
_EVAL_LABELS = ["CORRECT:", "FEEDBACK:", "SCORE:"]


def _extract_section(text: str, label: str, all_labels: list = None) -> str:
    """Extrae el contenido entre una etiqueta y la siguiente."""
    labels = all_labels or _LABELS
    start = text.find(label)
    if start == -1:
        return ""

    content_start = start + len(label)

    # Buscar dónde termina esta sección (empieza otra etiqueta)
    end = len(text)
    for other_label in labels:
        if other_label == label:
            continue
        pos = text.find(other_label, content_start)
        if pos != -1 and pos < end:
            end = pos

    return text[content_start:end].strip()


# Parsea la evaluación devuelta por Gemini en un diccionario
def parse_evaluation(text: str) -> dict:
    correct_raw = _extract_section(text, "CORRECT:", _EVAL_LABELS).lower()
    feedback = _extract_section(text, "FEEDBACK:", _EVAL_LABELS)
    score_raw = _extract_section(text, "SCORE:", _EVAL_LABELS)

    # Normalizar el resultado
    if "si" in correct_raw or "sí" in correct_raw or "yes" in correct_raw:
        correct = "si"
    elif "parcial" in correct_raw or "partial" in correct_raw:
        correct = "parcial"
    else:
        correct = "no"

    # Intentar convertir el puntaje a entero
    try:
        score = int("".join(filter(str.isdigit, score_raw.split("\n")[0])))
        score = max(0, min(score, 10))  # limitar entre 0 y 10
    except (ValueError, IndexError):
        score = 0 if correct == "no" else (5 if correct == "parcial" else 10)

    return {"correct": correct, "feedback": feedback, "score": score}


# Convierte el texto generado por la IA en datos estructurados
def parse_generated_activity(text: str) -> dict:
    introduction = _extract_section(text, "INTRODUCTION:")
    reflection = _extract_section(text, "REFLECTION:")

    questions = []

    easy_text = _extract_section(text, "QUESTION EASY:")
    if easy_text:
        questions.append(Question(id=1, question=easy_text, difficulty="easy"))

    medium_text = _extract_section(text, "QUESTION MEDIUM:")
    if medium_text:
        questions.append(Question(id=2, question=medium_text, difficulty="medium"))

    hard_text = _extract_section(text, "QUESTION HARD:")
    if hard_text:
        questions.append(Question(id=3, question=hard_text, difficulty="hard"))

    return {
        "introduction": introduction,
        "questions": questions,
        "reflection": reflection
    }