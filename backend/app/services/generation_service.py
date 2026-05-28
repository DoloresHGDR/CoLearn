"""
Servicio encargado de la generación de contenido con OpenRouter.

Se utiliza para:
- construir prompts
- generar actividades educativas
- centralizar la configuración del modelo
"""

import logging
import requests

from app.core.config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)


# Genera actividades educativas a partir del contexto recuperado
def generate_activity(
    level,
    focuses,
    context
):
    focus_text = ", ".join(focuses)

    prompt = f"""
You are an educational AI tutor.

IMPORTANT:
- Always respond in Spanish
- Generate EXACTLY 3 questions
- Avoid repetition
- Use friendly language

The 3 questions must follow Bloom's Taxonomy (Bloom, 1956) difficulty levels:
- QUESTION EASY: targets "remember" or "understand" (levels 1-2) — recall facts or explain concepts
- QUESTION MEDIUM: targets "apply" or "analyze" (levels 3-4) — use knowledge or break down ideas
- QUESTION HARD: targets "evaluate" or "create" (levels 5-6) — judge, argue or build on the content

Student level:
{level}

Pedagogical focuses:
{focus_text}

Context:
{context}

FORMAT:

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
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.9,
                "top_p": 0.95,
                "max_tokens": 1024
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        raise Exception("La IA tardó demasiado en responder. Intenta de nuevo.")
    except requests.exceptions.ConnectionError:
        raise Exception("No se pudo conectar con el servicio de IA. Verifica tu conexión.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al llamar a OpenRouter: {str(e)}")

    if "error" in data:
        raise Exception(f"Error de OpenRouter: {data['error']['message']}")

    if "choices" not in data or not data["choices"]:
        raise Exception("La IA no devolvió ninguna respuesta válida.")

    generated_text = data["choices"][0]["message"]["content"]
    logger.info("Actividad generada correctamente por OpenRouter")
    return generated_text

