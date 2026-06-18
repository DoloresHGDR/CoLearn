"""
Servicio de generación de actividades educativas.
Todas las llamadas a IA usan OpenRouter (GPT-3.5-turbo).
"""

import logging

from fastapi import HTTPException

from app.core.llm import call_openrouter

logger = logging.getLogger(__name__)


def generate_activity(level, focuses, context):
    """Genera preguntas educativas sobre el texto usando OpenRouter."""
    focus_text = ", ".join(focuses)

    prompt = f"""Sos un tutor educativo para UN alumno de 7mo grado de primaria (12-13 años) en Argentina.
Te dirigís a un solo alumno, en singular y con trato cercano.

IMPORTANTE:
- Responde SIEMPRE en español
- La introducción y la reflexión deben hablarle a UN SOLO alumno en singular: NO uses "chicos", "ustedes" ni el plural. Usá "vos" (ej. "hoy vas a...", "prestá atención", "¿qué aprendiste?")
- Genera EXACTAMENTE 3 preguntas sobre el texto que se te da abajo
- Las preguntas deben ser sobre el CONTENIDO del texto, no sobre habilidades en abstracto
- Usa lenguaje claro para preadolescentes de 12-13 años
- Evita vocabulario tecnico innecesario

Las 3 preguntas deben seguir la Taxonomia de Bloom revisada (Anderson y Krathwohl, 2001):
- QUESTION EASY: apunta a "recordar" o "entender" (niveles 1-2) — recordar datos o explicar conceptos del texto
- QUESTION MEDIUM: apunta a "aplicar" o "analizar" (niveles 3-4) — usar lo aprendido o comparar ideas del texto
- QUESTION HARD: apunta a "evaluar" o "crear" (niveles 5-6) — dar una opinion con fundamentos o imaginar un escenario

Nivel: {level}
Enfoques pedagogicos: {focus_text}

Texto de la clase:
{context}

FORMATO DE RESPUESTA (respeta exactamente):

INTRODUCTION:
...

QUESTION EASY:
...

QUESTION MEDIUM:
...

QUESTION HARD:
...

REFLECTION:
...
"""

    try:
        content = call_openrouter(prompt, temperature=0.9, max_tokens=1024)
        logger.info("Actividad generada correctamente por OpenRouter")
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Error al generar actividad: {str(e)}")
