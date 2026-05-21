import logging
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Crear el cliente de Gemini con la API key del entorno
_api_key = os.getenv("GOOGLE_API_KEY")
if _api_key:
    _client = genai.Client(api_key=_api_key)
else:
    _client = None
    logger.warning("GOOGLE_API_KEY no está configurada. El evaluador no funcionará.")


# Evalúa la respuesta del alumno usando Gemini
def evaluate_answer(question, student_answer, context, difficulty):
    if not _client:
        raise Exception("GOOGLE_API_KEY no está configurada en el archivo .env")

    prompt = f"""
Eres un tutor pedagógico amable pero honesto.
Debes evaluar la respuesta de un alumno.

Reglas:
- Si está bien, dilo claramente
- Si está parcialmente bien, explícalo
- Si está mal, dilo claramente pero con amabilidad
- Nunca inventes información fuera del contexto
- Usa lenguaje simple para un alumno de secundaria

La dificultad de esta pregunta es:
{difficulty}

Contexto:
{context}

Pregunta:
{question}

Respuesta del alumno:
{student_answer}

Devuelve EXACTAMENTE este formato:

CORRECT:
si/no/parcial

FEEDBACK:
...

SCORE:
(número del 0 al 10)
"""

    try:
        response = _client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )

        if response is None or not response.text:
            raise Exception("Gemini no devolvió ninguna respuesta válida.")

        logger.info("Evaluación generada correctamente por Gemini")
        return response.text

    except Exception as e:
        raise Exception(f"Error al evaluar con Gemini: {str(e)}")
