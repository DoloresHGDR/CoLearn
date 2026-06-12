"""
Servicio de resumen de desempeño de la clase para el docente.
Genera un resumen con IA y lo cachea; solo se regenera cuando cambian los datos
(respuestas nuevas o cambios de puntaje por reintentos).
"""

import logging

from fastapi import HTTPException

from app.core.llm import call_openrouter
from app.repositories.class_repository import get_class_by_id, update_class_summary
from app.repositories.metrics_repository import get_class_answer_stats
from app.services.metrics_service import get_metrics

logger = logging.getLogger(__name__)

_NIVEL = {"easy": "fácil", "medium": "medio", "hard": "difícil"}


def _build_prompt(metrics) -> str:
    """Arma el prompt con los datos de desempeño de los alumnos."""
    lineas = []
    for s in metrics.students:
        if s.score_by_difficulty:
            niveles = ", ".join(f"{_NIVEL.get(k, k)} {v}/10" for k, v in s.score_by_difficulty.items())
        else:
            niveles = "sin respuestas"
        lineas.append(
            f"- {s.name}: {s.answers_submitted} de 3 preguntas respondidas, "
            f"promedio {s.average_score}/10 ({niveles})"
        )
    datos = "\n".join(lineas) if lineas else "Todavía no hay alumnos inscriptos."

    return f"""Sos un asistente que ayuda a un docente de 7mo grado de primaria a entender cómo va su clase "{metrics.class_name}".

Alumnos inscriptos: {metrics.enrolled_count}
Desempeño:
{datos}

Escribí un resumen breve (3 a 4 oraciones) para el docente, en español, que destaque:
- El nivel general de comprensión de la clase
- Qué alumnos necesitan más apoyo (nombralos) o no completaron la actividad
- Una recomendación concreta y accionable

Reglas:
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
    try:
        summary = call_openrouter(_build_prompt(metrics), temperature=0.5, max_tokens=400)
    except Exception:
        # Si la IA falla, devolvemos lo cacheado (si hay) en vez de romper la pantalla
        if classroom.get("summary"):
            return {"summary": classroom["summary"], "generated": False}
        raise HTTPException(status_code=502, detail="No se pudo generar el resumen en este momento.")

    update_class_summary(class_id, summary, fingerprint)
    logger.info(f"Resumen regenerado para clase {class_id}")
    return {"summary": summary, "generated": True}
