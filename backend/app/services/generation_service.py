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

    # Los enfoques actuan como ENFASIS: se asignan de forma explicita a algunas preguntas (no a
    # todas) y el resto quedan como comprension general. La asignacion explicita por pregunta es
    # mas efectiva que un pedido general, que el modelo tiende a ignorar. El efecto es parcial
    # (mejor en enfoques de comprension que en vocabulario); afinar su consistencia es trabajo futuro.
    _slots = ["EASY 1", "EASY 2", "MEDIUM 1", "MEDIUM 2", "HARD"]
    # Los enfoques son un ENFASIS, no toman toda la actividad: solo algunas preguntas los trabajan
    # y el resto son de comprension general. EASY 1 y HARD quedan siempre generales (base literal y
    # opinion). Se asignan hasta 3 preguntas a enfoques (2 si hay un solo enfoque).
    _asignables = ["EASY 2", "MEDIUM 1", "MEDIUM 2"]
    _n = min(len(_asignables), 2 if len(focuses) == 1 else len(focuses))
    _foco_de = {_asignables[i]: focuses[i % len(focuses)] for i in range(_n)}
    asignacion = "\n".join(
        (f"- QUESTION {s}: debe trabajar especificamente el enfoque '{_foco_de[s]}'"
         if s in _foco_de
         else f"- QUESTION {s}: pregunta general de comprension del texto (sin enfoque especifico)")
        for s in _slots
    )

    prompt = f"""Sos un tutor educativo para UN alumno de 7mo grado de primaria (12-13 años) en Argentina.
Te dirigís a un solo alumno, en singular y con trato cercano.

IMPORTANTE:
- Responde SIEMPRE en español
- La introducción y la reflexión deben hablarle a UN SOLO alumno en singular: NO uses "chicos", "ustedes" ni el plural. Usá "vos" (ej. "hoy vas a...", "prestá atención", "¿qué aprendiste?")
- Genera EXACTAMENTE 5 preguntas sobre el texto que se te da abajo, distribuidas asi: 2 faciles, 2 medias y 1 dificil
- Las preguntas deben anclarse en el texto: en su contenido o en el vocabulario y las expresiones que aparecen en el. Evita solo las preguntas sobre habilidades en abstracto desconectadas del texto.
- Usa lenguaje claro para preadolescentes de 12-13 años
- Evita vocabulario tecnico innecesario

Las preguntas deben seguir la Taxonomia de Bloom revisada (Anderson y Krathwohl, 2001).
Se incluyen mas preguntas en los niveles bajos para dar mas practica y construir confianza
antes de exigir el juicio propio, que es lo mas demandante:
- EASY (2 preguntas, distintas entre si): apunta a "recordar" o "entender" (niveles 1-2) — recordar datos o explicar conceptos del texto
- MEDIUM (2 preguntas, distintas entre si): apunta a "aplicar" o "analizar" (niveles 3-4) — usar lo aprendido o comparar ideas del texto
- HARD (1 pregunta): apunta a "evaluar" o "crear" (niveles 5-6) — dar una opinion con fundamentos o imaginar un escenario

Nivel: {level}

Enfoques pedagogicos elegidos por el docente: {focus_text}
La actividad es, ante todo, de comprension lectora. Los enfoques son un enfasis: SOLO algunas
preguntas los trabajan, y las demas son preguntas generales de comprension del texto. Respeta la
asignacion de abajo y el nivel de dificultad de cada pregunta. En las preguntas con enfoque, al
leerlas tiene que notarse el enfoque.
Asignacion por pregunta:
{asignacion}

Texto de la clase:
{context}

FORMATO DE RESPUESTA (respeta exactamente):

INTRODUCTION:
...

QUESTION EASY 1:
...

QUESTION EASY 2:
...

QUESTION MEDIUM 1:
...

QUESTION MEDIUM 2:
...

QUESTION HARD:
...

REFLECTION:
...
"""

    try:
        content = call_openrouter(prompt, temperature=0.9, max_tokens=1400)
        logger.info("Actividad generada correctamente por OpenRouter")
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Error al generar actividad: {str(e)}")
