"""
Servicio encargado de transformar la respuesta del modelo
en estructuras utilizables por el sistema.

Se utiliza para:
- extraer preguntas
- obtener introducción y reflexión
- convertir texto en modelos Pydantic
"""

from app.models.schemas import Question

# Etiquetas que usa el modelo para generar actividades.
# Distribucion: 2 faciles + 2 medias + 1 dificil (mas practica en los niveles bajos).
_LABELS = [
    "INTRODUCTION:",
    "QUESTION EASY 1:",
    "QUESTION EASY 2:",
    "QUESTION MEDIUM 1:",
    "QUESTION MEDIUM 2:",
    "QUESTION HARD:",
    "REFLECTION:",
]

# Cada pregunta esperada con su nivel de dificultad, en orden de presentacion.
_QUESTION_SPEC = [
    ("QUESTION EASY 1:", "easy"),
    ("QUESTION EASY 2:", "easy"),
    ("QUESTION MEDIUM 1:", "medium"),
    ("QUESTION MEDIUM 2:", "medium"),
    ("QUESTION HARD:", "hard"),
]


def _extract_section(text: str, label: str, all_labels: list = None) -> str:
    """Extrae el contenido entre una etiqueta y la siguiente."""
    labels = all_labels or _LABELS
    start = text.find(label)
    if start == -1:
        return ""

    content_start = start + len(label)

    end = len(text)
    for other_label in labels:
        if other_label == label:
            continue
        pos = text.find(other_label, content_start)
        if pos != -1 and pos < end:
            end = pos

    return text[content_start:end].strip()


# Convierte el texto generado por la IA en datos estructurados
def parse_generated_activity(text: str) -> dict:
    introduction = _extract_section(text, "INTRODUCTION:")
    reflection = _extract_section(text, "REFLECTION:")

    questions = []
    qid = 1
    for label, difficulty in _QUESTION_SPEC:
        question_text = _extract_section(text, label)
        if question_text:
            questions.append(Question(id=qid, question=question_text, difficulty=difficulty))
            qid += 1

    return {
        "introduction": introduction,
        "questions": questions,
        "reflection": reflection
    }
