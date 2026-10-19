"""
Servicio de resumen de desempeño de la clase para el docente.
Genera un resumen con IA y lo cachea; solo se regenera cuando cambian los datos
(respuestas nuevas o cambios de puntaje por reintentos).
Los nombres de los alumnos no se envían a la IA: se reemplazan por códigos
([A1], [A2]...) y se restauran en el resumen que vuelve.
"""

import logging
import re

from fastapi import HTTPException

from app.core.llm import call_openrouter
from app.repositories.class_repository import get_class_by_id, update_class_summary
from app.repositories.metrics_repository import get_class_answer_stats
from app.repositories.question_repository import get_questions_by_class
from app.services.metrics_service import get_metrics

logger = logging.getLogger(__name__)

_NIVEL = {"easy": "fácil", "medium": "medio", "hard": "difícil"}

# Código de un alumno en el texto de la IA: [A1], [A2]... (también acepta A1 sin corchetes)
_ALIAS_PATTERN = re.compile(r"\[?\bA(\d+)\b\]?")


def _alias(position: int) -> str:
    """Código con el que se nombra al alumno ante la IA, en lugar de su nombre."""
    return f"[A{position}]"


def _restore_names(summary: str, students) -> str:
    """Reemplaza los códigos del resumen por los nombres reales de los alumnos."""
    names = {i: s.name for i, s in enumerate(students, start=1)}
    return _ALIAS_PATTERN.sub(lambda m: names.get(int(m.group(1)), m.group(0)), summary)


def _build_prompt(metrics, total_questions: int) -> str:
    """Arma el prompt con los datos de desempeño de los alumnos, sin sus nombres."""
    lineas = []
    for i, s in enumerate(metrics.students, start=1):
        if s.score_by_difficulty:
            niveles = ", ".join(f"{_NIVEL.get(k, k)} {v}/10" for k, v in s.score_by_difficulty.items())
        else:
            niveles = "sin respuestas"
        lineas.append(
            f"- {_alias(i)}: {s.answers_submitted} de {total_questions} preguntas respondidas, "
            f"promedio {s.average_score}/10 ({niveles})"
        )
    datos = "\n".join(lineas) if lineas else "Todavía no hay alumnos inscriptos."

    return f"""Sos un asistente que ayuda a un docente de 7mo grado de primaria a entender cómo va su clase "{metrics.class_name}".

Alumnos inscriptos: {metrics.enrolled_count}
Desempeño:
{datos}

Escribí un resumen breve (3 a 4 oraciones) para el docente, en español, que destaque:
- El nivel general de comprensión de la clase
- Qué alumnos necesitan más apoyo o no completaron la actividad (nombralos con su código)
- Una recomendación concreta y accionable

Reglas:
- Cada alumno aparece con un código entre corchetes (por ejemplo [A1]) en lugar de su nombre. Usá ese código tal cual, como si fuera un nombre, sin agregar "el alumno" ni artículos
- Sé honesto: si hay pocos datos, aclaralo y no inventes tendencias
- Tono profesional y claro, dirigido al docente (no al alumno)
- No uses listas, asteriscos ni encabezados; solo texto corrido"""


def get_class_summary(class_id: str, teacher_id: str) -> dict:
    """Resumen de desempeño de la clase, cacheado. Se regenera solo si cambian los datos."""
    classroom = get_class_by_id(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if classroom["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="No tenés acceso a esta clase.")

    stats = get_class_answer_stats(class_id)
    total = int(stats["total"])

    # Sin respuestas todavía → no llamamos a la IA (evita inventar tendencias)
    if total == 0:
        return {
            "summary": "Todavía no hay actividad suficiente para un resumen. Cuando tus alumnos "
                       "empiecen a responder las preguntas, vas a ver acá un análisis de su desempeño.",
            "generated": False,
        }

    fingerprint = f"{total}:{int(stats['sum_scores'])}"

    # Datos sin cambios desde la última generación → devolver el resumen cacheado
    if classroom.get("summary") and classroom.get("summary_fingerprint") == fingerprint:
        return {"summary": classroom["summary"], "generated": False}

    # Datos nuevos → generar con IA y guardar
    metrics = get_metrics(class_id, teacher_id)
    # Total real de preguntas de la actividad (no un número fijo)
    total_questions = len(get_questions_by_class(class_id))
    try:
        summary = call_openrouter(_build_prompt(metrics, total_questions), temperature=0.5, max_tokens=400)
    except Exception:
        # Si la IA falla, devolvemos lo cacheado (si hay) en vez de romper la pantalla
        if classroom.get("summary"):
            return {"summary": classroom["summary"], "generated": False}
        raise HTTPException(status_code=502, detail="No se pudo generar el resumen en este momento.")

    # Los nombres reales se recuperan acá, sin haber salido del servidor
    summary = _restore_names(summary, metrics.students)
    update_class_summary(class_id, summary, fingerprint)
    logger.info(f"Resumen regenerado para clase {class_id}")
    return {"summary": summary, "generated": True}
