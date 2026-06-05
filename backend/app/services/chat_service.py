"""
Servicio de chat con flujo guiado de aprendizaje.

Flujo:
1. __init__  → bienvenida + pedido de leer el texto
2. Alumno listo → primera pregunta (nivel adaptativo)
3. Respuesta → evaluación + próxima pregunta o pista si dice "no sé"
4. Todo respondido → chat libre sobre el texto
"""

import logging
import re
from datetime import datetime, timezone

import requests
from fastapi import HTTPException

from app.core.cache import generate_file_hash, load_cache
from app.core.config import OPENROUTER_API_KEY
from app.models.schemas import ChatMessage, ChatResponse
from app.rag.chunker import model as embedding_model
from app.rag.indexer import search_context
from app.repositories.chat_repository import get_history, get_recent_history, save_message
from app.repositories.class_repository import get_class_by_id, is_enrolled
from app.repositories.question_repository import get_questions_by_class
from app.repositories.class_answer_repository import get_answers_by_student, save_student_answer
from app.repositories.metrics_repository import get_my_stats
from app.services.metrics_service import _recommended_level

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 10


def _clean(text: str) -> str:
    """Elimina markdown y emojis de las respuestas para mostrar solo texto limpio."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **negrita** → texto
    text = re.sub(r'\*(.+?)\*', r'\1', text)         # *cursiva* → texto
    text = re.sub(r'#{1,6}\s', '', text)             # ## encabezados
    # Eliminar emojis
    text = re.sub(r'[^\x00-\x7FáéíóúüñÁÉÍÓÚÜÑ¿¡\s\w.,;:!?()\-]', '', text)
    return text.strip()

# Palabras que indican que el alumno está listo para empezar
_READY = ["listo", "lista", "si", "sí", "ok", "dale", "leí", "lei",
          "comenzar", "empezar", "adelante", "ya", "vamos", "done"]

# Palabras que indican que el alumno no sabe la respuesta
_CANT = ["no sé", "no se", "no lo sé", "no lo se", "no tengo idea",
         "ni idea", "desconozco", "no entiendo", "no recuerdo", "no sabe"]


def _is_ready(message: str) -> bool:
    """Detecta si el alumno confirmó que está listo para empezar."""
    msg = message.lower().strip()
    # Solo keywords explícitos — no usar longitud para evitar falsos positivos
    return any(kw in msg for kw in _READY) and not _is_cant_answer(message)


def _is_cant_answer(message: str) -> bool:
    """Detecta si el alumno dice que no sabe la respuesta."""
    return any(kw in message.lower() for kw in _CANT)


def _get_next_question(questions, answered_ids, class_id, student_id):
    """Devuelve la próxima pregunta sin responder según el nivel adaptativo."""
    unanswered = [q for q in questions if q["id"] not in answered_ids]
    if not unanswered:
        return None
    order = {"easy": 0, "medium": 1, "hard": 2}
    try:
        stats = get_my_stats(class_id, student_id)
        level = _recommended_level(int(stats["answers_submitted"]), float(stats["average_score"]))
        target = order[level]
        unanswered.sort(key=lambda q: abs(order.get(q["difficulty"], 0) - target))
    except Exception:
        pass
    return unanswered[0]


def _get_last_asked_question(history, questions):
    """Encuentra la última pregunta de Bloom que se le hizo al alumno en el chat."""
    ai_messages = [m for m in reversed(history) if m["role"] == "assistant"]
    for ai_msg in ai_messages:
        content = ai_msg["content"]
        for q in questions:
            if q["question"][:50] in content:
                return q
    return None


def _load_rag(classroom):
    """Carga el índice RAG de una clase desde caché."""
    file_path = classroom["file_path"]
    if not file_path:
        return None
    try:
        with open(file_path, "rb") as f:
            content = f.read()
    except FileNotFoundError:
        return None
    return load_cache(generate_file_hash(content))


def _call_openrouter(prompt: str) -> str:
    """Llama a OpenRouter y devuelve el texto generado."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY no está configurada.")
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
        raise HTTPException(status_code=502, detail=f"Error de OpenRouter: {data['error']['message']}")
    return data["choices"][0]["message"]["content"].strip()


def _save_pair(class_id, student_id, user_msg, ai_msg):
    """Guarda el par usuario/asistente con timestamps distintos."""
    save_message(class_id=class_id, student_id=student_id, role="user",
                 content=user_msg, created_at=datetime.now(timezone.utc).isoformat())
    save_message(class_id=class_id, student_id=student_id, role="assistant",
                 content=ai_msg, created_at=datetime.now(timezone.utc).isoformat())


def _evaluate_answer(question_text, student_answer, context, class_name) -> dict:
    """Evalúa la respuesta del alumno usando OpenRouter con el contexto del texto."""
    prompt = f"""Sos un tutor para alumnos de 7mo grado de primaria en Argentina.

Texto de la clase "{class_name}":
{context[:1500]}

Pregunta: {question_text}
Respuesta del alumno: {student_answer}

Evaluá brevemente. Respondé EXACTAMENTE en este formato:
CORRECTO: si / parcial / no
PUNTAJE: (0 al 10)
FEEDBACK: (1-2 oraciones alentadoras, sin revelar la respuesta completa)"""

    try:
        result = _call_openrouter(prompt)
        correct, score, feedback = "parcial", 5, "Bien intentado. Segui adelante."
        for line in result.strip().split("\n"):
            low = line.lower()
            if low.startswith("correcto:"):
                val = line.split(":", 1)[1].strip().lower()
                if "no" in val and "parcial" not in val:
                    correct = "no"
                elif "si" in val or "sí" in val:
                    correct = "si"
                else:
                    correct = "parcial"
            elif low.startswith("puntaje:") or low.startswith("score:"):
                try:
                    score = max(0, min(10, int(line.split(":", 1)[1].strip())))
                except Exception:
                    pass
            elif low.startswith("feedback:"):
                feedback = line.split(":", 1)[1].strip()

        # Forzar consistencia entre correcto y puntaje para evitar promedios incorrectos
        if correct == "no":
            score = min(score, 3)
        elif correct == "si":
            score = max(score, 7)
        else:
            score = max(4, min(score, 6))

        return {"correct": correct, "score": score, "feedback": _clean(feedback)}
    except Exception:
        return {"correct": "parcial", "score": 5, "feedback": "Bien intentado. Segui adelante."}


def send_message(class_id, student_id, message) -> ChatResponse:
    """Procesa el mensaje del alumno siguiendo el flujo guiado de aprendizaje."""

    classroom = get_class_by_id(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if not is_enrolled(class_id, student_id):
        raise HTTPException(status_code=403, detail="No estás inscrito en esta clase.")

    history = get_history(class_id, student_id)
    questions = get_questions_by_class(class_id)
    answered = get_answers_by_student(class_id, student_id)
    answered_ids = {a["question_id"] for a in answered}

    cached = _load_rag(classroom)
    class_name = classroom["name"]
    focuses = classroom.get("focuses", "comprensión lectora")

    # ── CASO 1: Inicio — el frontend manda __init__ cuando el chat está vacío ──
    if message == "__init__":
        focuses_text = ", ".join(focuses.split(","))
        intro = (
            f'Hola! Soy tu tutor de la clase "{class_name}".\n\n'
            f"En esta actividad vamos a trabajar: {focuses_text}.\n\n"
            f"Antes de empezar, te pido que leas el texto que te asigno tu docente. "
            f'Cuando hayas terminado de leerlo, escribime "Listo" y empezamos con las preguntas.'
        )
        save_message(class_id=class_id, student_id=student_id, role="assistant",
                     content=intro, created_at=datetime.now(timezone.utc).isoformat())
        return ChatResponse(reply=intro)

    # ── CASO 2: Alumno listo — aplica cuando no hay pregunta activa pendiente ──
    # Fix: antes solo chequeaba len(answered)==0, pero si el alumno dice "listo"
    # a mitad del progreso, debe recibir la siguiente pregunta, no ser evaluado.
    unanswered = [q for q in questions if q["id"] not in answered_ids]
    last_q_check = _get_last_asked_question(history, questions)
    no_question_pending = last_q_check is None or last_q_check["id"] in answered_ids

    if _is_ready(message) and unanswered and no_question_pending:
        next_q = _get_next_question(questions, answered_ids, class_id, student_id)
        if next_q:
            labels = {"easy": "Nivel facil", "medium": "Nivel medio", "hard": "Nivel dificil"}
            reply = (
                f"Genial, empecemos. {labels.get(next_q['difficulty'], '')}\n\n"
                f"{next_q['question']}"
            )
        else:
            reply = "No hay preguntas registradas para esta clase todavia. Podes preguntarme lo que quieras sobre el texto."
        _save_pair(class_id, student_id, message, reply)
        return ChatResponse(reply=reply)

    # ── CASO 3: Hay preguntas sin responder → evaluar respuesta y continuar ──
    if unanswered:
        last_q = _get_last_asked_question(history, questions)

        if last_q and last_q["id"] not in answered_ids:
            # Si el alumno dice que no sabe → dar pista
            if _is_cant_answer(message):
                rag_context = search_context(
                    question=last_q["question"],
                    chunks=cached["chunks"],
                    index=cached["index"],
                    model=embedding_model
                ) if cached else ""
                hint_prompt = (
                    f"El alumno de 7mo grado no sabe responder: \"{last_q['question']}\"\n"
                    f"Contexto del texto: {rag_context[:800]}\n"
                    f"Dales UNA pista breve sin revelar la respuesta. Sé alentador."
                )
                try:
                    hint = _call_openrouter(hint_prompt)
                except Exception:
                    hint = "Te doy una pista: busca en el texto la parte que habla sobre este tema. Leelo con atencion y vas a encontrar la respuesta."
                _save_pair(class_id, student_id, message, hint)
                return ChatResponse(reply=hint)

            # Evaluar la respuesta
            rag_context = search_context(
                question=last_q["question"],
                chunks=cached["chunks"],
                index=cached["index"],
                model=embedding_model
            ) if cached else ""
            eval_result = _evaluate_answer(last_q["question"], message, rag_context, class_name)

            # Guardar en student_answers
            save_student_answer(
                class_id=class_id,
                student_id=student_id,
                question_id=last_q["id"],
                answer=message,
                correct=eval_result["correct"],
                feedback=eval_result["feedback"],
                score=eval_result["score"],
                created_at=datetime.now(timezone.utc).isoformat()
            )

            # Próxima pregunta
            answered_ids.add(last_q["id"])
            next_q = _get_next_question(questions, answered_ids, class_id, student_id)

            reply = _clean(eval_result["feedback"])

            # Si la respuesta fue incorrecta, agregar sugerencia antes de continuar
            if eval_result["correct"] == "no":
                reply += "\n\nTe recomiendo releer esa parte del texto antes de continuar. La siguiente pregunta esta relacionada con el mismo material."

            if next_q:
                labels = {"easy": "Pregunta de nivel facil", "medium": "Pregunta de nivel medio", "hard": "Pregunta de nivel dificil"}
                # Si respondio mal, forzar nivel igual o mas facil para la siguiente
                if eval_result["correct"] == "no":
                    easier_order = {"easy": 0, "medium": 1, "hard": 2}
                    current_order = easier_order.get(last_q["difficulty"], 1)
                    next_q_candidates = [q for q in questions if q["id"] not in answered_ids]
                    next_q_candidates.sort(key=lambda q: easier_order.get(q["difficulty"], 1))
                    # Preferir mismo nivel o mas facil
                    same_or_easier = [q for q in next_q_candidates if easier_order.get(q["difficulty"], 1) <= current_order]
                    if same_or_easier:
                        next_q = same_or_easier[0]
                reply += f"\n\n{labels.get(next_q['difficulty'], '')}\n{next_q['question']}"
            else:
                all_answers = get_answers_by_student(class_id, student_id)
                avg = sum(a["score"] for a in all_answers) / len(all_answers) if all_answers else 0
                reply += (
                    f"\n\nTerminaste todas las preguntas. Tu promedio fue {avg:.1f}/10. "
                    f"Si tenes alguna duda sobre el texto, preguntame."
                )

            _save_pair(class_id, student_id, message, reply)
            return ChatResponse(reply=reply)

    # ── CASO 4: Chat libre (todas las preguntas respondidas o sin preguntas) ──
    rag_context = search_context(
        question=message,
        chunks=cached["chunks"],
        index=cached["index"],
        model=embedding_model
    ) if cached else ""

    if not rag_context:
        off_topic = (
            "Esa pregunta no parece estar relacionada con el texto de la clase. "
            "¿Querés preguntarme algo sobre el material que leíste?"
        )
        _save_pair(class_id, student_id, message, off_topic)
        return ChatResponse(reply=off_topic)

    recent = get_recent_history(class_id, student_id, HISTORY_LIMIT)
    history_text = "".join(
        f"{'Alumno' if m['role'] == 'user' else 'Tutor'}: {m['content']}\n"
        for m in recent
    )

    prompt = f"""Sos un tutor educativo para alumnos de 7mo grado de primaria (12-13 años) en Argentina.

Reglas:
- Respondé SIEMPRE en español
- Usá lenguaje claro para preadolescentes, no infantil
- Guiá con preguntas o pistas, NO des respuestas directas
- Basate ÚNICAMENTE en el texto de abajo
- Sé breve y alentador

Texto de la clase:
{rag_context}

Conversación:
{history_text}
Alumno: {message}
Tutor:"""

    try:
        reply = _call_openrouter(prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al contactar la IA: {str(e)}")

    _save_pair(class_id, student_id, message, reply)
    logger.info(f"Chat libre: alumno {student_id} en clase {class_id}")
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
