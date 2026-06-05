import logging

import requests

from app.core.config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)


def evaluate_answer(question, student_answer, context, difficulty):
    """Evalúa la respuesta del alumno usando OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY no está configurada en el archivo .env")

    prompt = f"""Sos un tutor pedagogico para alumnos de 7mo grado de primaria (12-13 años) en Argentina.
Evalua la respuesta del alumno de forma clara y alentadora.

Reglas:
- Si esta bien, decilo claramente
- Si esta parcialmente bien, explicalo
- Si esta mal, decilo con amabilidad
- Nunca inventes informacion fuera del contexto
- Usa lenguaje apropiado para preadolescentes de 7mo grado

Dificultad de la pregunta: {difficulty}

Contexto del texto:
{context}

Pregunta: {question}

Respuesta del alumno: {student_answer}

Devuelve EXACTAMENTE este formato:

CORRECT:
si/no/parcial

FEEDBACK:
...

SCORE:
(numero del 0 al 10)
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
                "temperature": 0.7,
                "max_tokens": 512
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise Exception(f"Error de OpenRouter: {data['error']['message']}")
        logger.info("Evaluacion generada correctamente por OpenRouter")
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        raise Exception(f"Error al evaluar: {str(e)}")
