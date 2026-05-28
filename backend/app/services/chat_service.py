"""
Servicio de chat: maneja la conversación del alumno con la IA.

Flujo:
1. Verifica que el alumno esté inscrito en la clase
2. Carga el índice RAG del texto del docente desde caché
3. Busca fragmentos relevantes según el mensaje del alumno
4. Arma el prompt con historial + contexto + mensaje nuevo
5. Llama a OpenRouter y guarda la respuesta
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.cache import generate_file_hash, load_cache
from app.core.config import OPENROUTER_API_KEY
from app.models.schemas import ChatMessage, ChatResponse
from app.rag.chunker import model as embedding_model
from app.rag.indexer import search_context
from app.repositories.chat_repository import get_history, get_recent_history, save_message
from app.repositories.class_repository import get_class_by_id, is_enrolled

import requests

logger = logging.getLogger(__name__)

# Cantidad de mensajes anteriores que se le manda a la IA como historial
HISTORY_LIMIT = 10


def _load_rag_for_class(classroom):
    """Carga el índice RAG de una clase desde el caché."""
    file_path = classroom["file_path"]
    if not file_path:
        raise HTTPException(status_code=500, detail="La clase no tiene archivo asociado.")

    # Leer el archivo para obtener su hash y cargar el caché
    try:
        with open(file_path, "rb") as f:
            content = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="No se encontró el archivo de la clase.")

    file_hash = generate_file_hash(content)
    cached = load_cache(file_hash)

    if not cached:
        raise HTTPException(
            status_code=500,
            detail="El contenido de la clase no está procesado. Contactá al docente."
        )

    return cached


def _build_prompt(context, history, message):
    """Arma el prompt completo para la IA con contexto, historial y mensaje nuevo."""

    # Convertir el historial en texto
    history_text = ""
    for msg in history:
        label = "Alumno" if msg["role"] == "user" else "Tutor"
        history_text += f"{label}: {msg['content']}\n"

    return f"""Eres un tutor educativo que ayuda a alumnos a comprender textos escolares.

Reglas importantes:
- Responde SIEMPRE en español
- Usa lenguaje simple y amigable, como si hablaras con un alumno de secundaria
- Guía al alumno hacia la respuesta con preguntas o pistas, NO des la respuesta directamente
- Basa tus respuestas ÚNICAMENTE en el texto proporcionado abajo
- Si el alumno pregunta algo que no está en el texto, díselo amablemente
- Sé breve y claro

Texto de la clase:
{context}

Conversación hasta ahora:
{history_text}
Alumno: {message}
Tutor:"""


def send_message(class_id, student_id, message) -> ChatResponse:
    """Procesa el mensaje del alumno y devuelve la respuesta de la IA."""

    # Verificar que la clase existe
    classroom = get_class_by_id(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")

    # Verificar que el alumno está inscrito
    if not is_enrolled(class_id, student_id):
        raise HTTPException(status_code=403, detail="No estás inscrito en esta clase.")

    # Cargar RAG y buscar contexto relevante
    cached = _load_rag_for_class(classroom)
    context = search_context(
        question=message,
        chunks=cached["chunks"],
        index=cached["index"],
        model=embedding_model
    )

    # Si no hay contexto relevante, la pregunta está fuera del tema del texto
    if not context:
        off_topic_reply = (
            "Esa pregunta no parece estar relacionada con el texto de la clase. "
            "¿Querés preguntarme algo sobre el material que subió el docente?"
        )
        now = datetime.now(timezone.utc).isoformat()
        save_message(class_id=class_id, student_id=student_id, role="user", content=message, created_at=now)
        assistant_time = datetime.now(timezone.utc).isoformat()
        save_message(class_id=class_id, student_id=student_id, role="assistant", content=off_topic_reply, created_at=assistant_time)
        return ChatResponse(reply=off_topic_reply)

    # Cargar historial reciente para mantener coherencia
    history = get_recent_history(class_id, student_id, limit=HISTORY_LIMIT)

    # Armar prompt y llamar a la IA
    prompt = _build_prompt(context=context, history=history, message=message)

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
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error al contactar la IA: {str(e)}")

    if "error" in data:
        raise HTTPException(status_code=502, detail=f"Error de OpenRouter: {data['error']['message']}")

    reply = data["choices"][0]["message"]["content"].strip()

    # Guardar con timestamps distintos para mantener el orden correcto
    user_time = datetime.now(timezone.utc).isoformat()
    save_message(class_id=class_id, student_id=student_id, role="user", content=message, created_at=user_time)
    assistant_time = datetime.now(timezone.utc).isoformat()
    save_message(class_id=class_id, student_id=student_id, role="assistant", content=reply, created_at=assistant_time)

    logger.info(f"Chat: alumno {student_id} en clase {class_id}")
    return ChatResponse(reply=reply)


def get_chat_history(class_id, student_id) -> list[ChatMessage]:
    """Devuelve el historial completo de chat de un alumno en una clase."""

    classroom = get_class_by_id(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")

    if not is_enrolled(class_id, student_id):
        raise HTTPException(status_code=403, detail="No estás inscrito en esta clase.")

    rows = get_history(class_id, student_id)
    return [ChatMessage(role=r["role"], content=r["content"], created_at=r["created_at"]) for r in rows]
