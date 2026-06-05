"""
Servicio de generación de actividades educativas.
Todas las llamadas a IA usan OpenRouter (GPT-3.5-turbo).
"""

import logging

import requests
from fastapi import HTTPException

from app.core.config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)


def generate_activity(level, focuses, context):
    """Genera preguntas educativas sobre el texto usando OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY no está configurada.")

    focus_text = ", ".join(focuses)

    prompt = f"""Sos un tutor educativo para alumnos de 7mo grado de primaria (12-13 años) en Argentina.

IMPORTANTE:
- Responde SIEMPRE en español
- Genera EXACTAMENTE 3 preguntas sobre el texto que se te da abajo
- Las preguntas deben ser sobre el CONTENIDO del texto, no sobre habilidades en abstracto
- Usa lenguaje claro para preadolescentes de 12-13 años
- Evita vocabulario tecnico innecesario

Las 3 preguntas deben seguir la Taxonomia de Bloom (Bloom, 1956):
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
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 1024
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise Exception(f"Error de OpenRouter: {data['error']['message']}")
        if "choices" not in data or not data["choices"]:
            raise Exception("OpenRouter no devolvio ninguna respuesta valida.")

        logger.info("Actividad generada correctamente por OpenRouter")
        return data["choices"][0]["message"]["content"]

    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Error al generar actividad: {str(e)}")
