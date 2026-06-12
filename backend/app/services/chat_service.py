"""
Servicio de chat con flujo guiado de aprendizaje.

Flujo:
1. __init__  → bienvenida + introducción del tema + pedido de leer el texto
2. Alumno listo → primera pregunta (nivel adaptativo según desempeño)
3. Respuesta → evaluación. Si es incorrecta en el primer intento, se da una
   pista y se ofrece un segundo intento antes de avanzar (portón de reintento,
   inspirado en Mastery Learning de Bloom 1968, acotado a MAX_ATTEMPTS).
4. Todo respondido → reflexión de cierre + chat libre sobre el texto

El estado del flujo (qué pregunta está activa, si es reintento) se deriva de la
base de datos, no del texto de los mensajes.
"""

import logging
import re
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.cache import generate_file_hash, load_cache
from app.core.llm import call_openrouter
from app.models.schemas import ChatMessage, ChatResponse
from app.rag.chunker import model as embedding_model
from app.rag.indexer import search_context
from app.repositories.chat_repository import get_history, get_recent_history, save_message
from app.repositories.class_repository import (
    get_class_by_id,
    is_enrolled,
    get_practice_index,
    set_practice_index,
)
from app.repositories.question_repository import get_questions_by_class
from app.repositories.class_answer_repository import (
    get_answers_by_student,
    save_student_answer,
    update_student_answer,
)
from app.repositories.metrics_repository import get_my_stats
from app.services.metrics_service import _recommended_level

# Máximo de intentos por pregunta antes de avanzar (portón de dominio)
MAX_ATTEMPTS = 2

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


# Comando explícito con el que el alumno pide reintentar las preguntas (modo práctica)
_PRACTICAR = ["practicar", "practica", "practicá", "reintentar", "volver a intentar",
              "de nuevo las preguntas", "ejercitar", "repasar las preguntas"]


def _quiere_practicar(message: str) -> bool:
    """Detecta si el alumno pide reintentar las preguntas como práctica."""
    return any(kw in message.lower() for kw in _PRACTICAR)


def _get_next_question(questions, excluded_ids, class_id, student_id):
    """Devuelve la próxima pregunta sin tocar según el nivel adaptativo recomendado."""
    candidates = [q for q in questions if q["id"] not in excluded_ids]
    if not candidates:
        return None
    order = {"easy": 0, "medium": 1, "hard": 2}
    try:
        stats = get_my_stats(class_id, student_id)
        level = _recommended_level(int(stats["answers_submitted"]), float(stats["average_score"]))
        target = order[level]
        candidates.sort(key=lambda q: abs(order.get(q["difficulty"], 0) - target))
    except Exception:
        pass
    return candidates[0]


def _generar_pista(question_text, context, student_answer=None) -> str:
    """Genera una pista breve sin revelar la respuesta. Usada ante 'no sé' o respuesta incorrecta."""
    situacion = (
        f'respondió incorrectamente. Su respuesta fue: "{student_answer}"'
        if student_answer else "no sabe cómo responder"
    )
    prompt = f"""Sos un tutor educativo para UN alumno de 7mo grado de primaria (12-13 años) en Argentina.
Hablás con un solo alumno, en singular.

El alumno {situacion}
Pregunta: "{question_text}"

Texto de referencia:
---
{context[:1200] if context else "[No disponible]"}
---

Dale UNA pista breve (1-2 oraciones) que lo oriente hacia la respuesta SIN revelarla.
Respondé solo la pista, en español, en singular, de manera alentadora. No uses listas ni encabezados."""
    try:
        return _clean(call_openrouter(prompt))
    except Exception:
        return "Revisá con atención la parte del texto que habla de este tema, ahí está la respuesta."


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


def _save_pair(class_id, student_id, user_msg, ai_msg):
    """Guarda el par usuario/asistente con timestamps distintos."""
    save_message(class_id=class_id, student_id=student_id, role="user",
                 content=user_msg, created_at=datetime.now(timezone.utc).isoformat())
    save_message(class_id=class_id, student_id=student_id, role="assistant",
                 content=ai_msg, created_at=datetime.now(timezone.utc).isoformat())


def _format_history(messages) -> str:
    """Formatea el historial reciente para incluirlo en el prompt del tutor."""
    return "".join(
        f"{'Alumno' if m['role'] == 'user' else 'Tutor'}: {m['content']}\n"
        for m in messages
    )


def _procesar_mensaje(question_text, student_answer, context, class_name) -> dict:
    """
    Clasifica la intención del mensaje del alumno y, si es una respuesta, la evalúa.
    Una sola llamada al modelo (no agrega costo respecto a solo evaluar).

    Devuelve un dict con:
    - intencion: 'respuesta' | 'ayuda' | 'fuera_de_tema'
    - si 'respuesta': correct, score, feedback
    - si 'ayuda' o 'fuera_de_tema': mensaje
    """
    context_block = context[:2500] if context else "[Texto no disponible]"
    prompt = f"""Sos un tutor educativo para UN alumno de 7mo grado de primaria (12-13 años) en Argentina.
Hablás con un solo alumno, en singular y con trato cercano.

Texto de la clase "{class_name}":
---
{context_block}
---

Pregunta actual: {question_text}
Mensaje del alumno: "{student_answer}"

PASO 1 — Clasificá la intención del mensaje en una sola categoría:
- RESPUESTA: intenta responder la pregunta (aunque sea incompleto o equivocado)
- AYUDA: pide una pista, dice que no sabe, no entiende, o pide que le expliques
- FUERA_DE_TEMA: quiere hablar de otra cosa que no tiene que ver con el texto

Reglas:
- Respondé SIEMPRE en español y en singular
- Si dudás entre RESPUESTA y AYUDA, elegí AYUDA
- Nunca reveles la respuesta completa

Formato EXACTO (sin texto antes ni después):
INTENCION: respuesta / ayuda / fuera_de_tema

Si la intención es "respuesta", agregá:
CORRECTO: si / parcial / no
PUNTAJE: [número del 0 al 10]
FEEDBACK: [1-2 oraciones alentadoras]

Si la intención es "ayuda", agregá:
MENSAJE: [una pista breve que oriente sin revelar la respuesta]

Si la intención es "fuera_de_tema", agregá:
MENSAJE: [recordale con amabilidad que eso está fuera del texto y volvé a la pregunta]"""

    try:
        result = call_openrouter(prompt)
        intencion = "respuesta"
        correct, score = "parcial", 5
        feedback_lines, mensaje_lines = [], []
        capturing = None

        for line in result.strip().split("\n"):
            low = line.lower().strip()
            if low.startswith("intencion:"):
                val = line.split(":", 1)[1].strip().lower()
                if "ayuda" in val:
                    intencion = "ayuda"
                elif "fuera" in val:
                    intencion = "fuera_de_tema"
                else:
                    intencion = "respuesta"
                capturing = None
            elif low.startswith("correcto:"):
                val = line.split(":", 1)[1].strip().lower()
                if "si" in val or "sí" in val:
                    correct = "si"
                elif "parcial" in val:
                    correct = "parcial"
                else:
                    correct = "no"
                capturing = None
            elif low.startswith("puntaje:"):
                try:
                    nums = re.findall(r'\d+', line.split(":", 1)[1])
                    if nums:
                        score = max(0, min(10, int(nums[0])))
                except Exception:
                    pass
                capturing = None
            elif low.startswith("feedback:"):
                feedback_lines = [line.split(":", 1)[1].strip()]
                capturing = "feedback"
            elif low.startswith("mensaje:"):
                mensaje_lines = [line.split(":", 1)[1].strip()]
                capturing = "mensaje"
            elif capturing == "feedback" and line.strip():
                feedback_lines.append(line.strip())
            elif capturing == "mensaje" and line.strip():
                mensaje_lines.append(line.strip())

        if intencion == "respuesta":
            feedback = " ".join(feedback_lines) if feedback_lines else "Bien intentado. Segui adelante."
            # Forzar consistencia entre correcto y puntaje para evitar promedios incorrectos
            if correct == "no":
                score = min(score, 3)
            elif correct == "si":
                score = max(score, 7)
            else:
                score = max(4, min(score, 6))
            return {"intencion": "respuesta", "correct": correct, "score": score, "feedback": _clean(feedback)}

        # ayuda o fuera_de_tema → devolver el mensaje del tutor
        mensaje = " ".join(mensaje_lines) if mensaje_lines else ""
        if not mensaje:
            mensaje = ("Te doy una pista: revisá con atención la parte del texto que habla de esto."
                       if intencion == "ayuda"
                       else "Eso está fuera del texto de la clase. Volvamos a la pregunta.")
        return {"intencion": intencion, "mensaje": _clean(mensaje)}

    except Exception:
        # Ante un fallo, tratamos el mensaje como respuesta parcial (camino seguro)
        return {"intencion": "respuesta", "correct": "parcial", "score": 5, "feedback": "Bien intentado. Segui adelante."}


def send_message(class_id, student_id, message) -> ChatResponse:
    """Procesa el mensaje del alumno siguiendo el flujo guiado de aprendizaje."""

    classroom = get_class_by_id(class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")
    if not is_enrolled(class_id, student_id):
        raise HTTPException(status_code=403, detail="No estás inscrito en esta clase.")

    history = get_history(class_id, student_id)
    questions = get_questions_by_class(class_id)
    answers = get_answers_by_student(class_id, student_id)
    answer_map = {a["question_id"]: a for a in answers}

    cached = _load_rag(classroom)
    class_name = classroom["name"]
    focuses = classroom.get("focuses", "comprensión lectora")

    def _is_closed(q):
        """Pregunta cerrada: respondida bien/parcial, o que ya agotó sus intentos."""
        a = answer_map.get(q["id"])
        return a is not None and (a["correct"] != "no" or a["attempts"] >= MAX_ATTEMPTS)

    open_questions = [q for q in questions if not _is_closed(q)]
    touched_ids = set(answer_map.keys())

    # ── CASO 1: Inicio — el frontend manda __init__ cuando el chat está vacío ──
    if message == "__init__":
        intro_generada = classroom.get("introduction", "")
        focuses_text = ", ".join(focuses.split(","))
        partes = [f'Hola! Soy tu tutor de la clase "{class_name}".']
        if intro_generada:
            partes.append(intro_generada)
        else:
            partes.append(f"En esta actividad vamos a trabajar: {focuses_text}.")
        partes.append(
            'Antes de empezar, leé el texto que asignó tu docente. '
            'Cuando termines, escribime "Listo" y arrancamos con las preguntas.'
        )
        intro = "\n\n".join(partes)
        save_message(class_id=class_id, student_id=student_id, role="assistant",
                     content=intro, created_at=datetime.now(timezone.utc).isoformat())
        return ChatResponse(reply=intro)

    # ── MODO PRÁCTICA: el alumno reintenta las preguntas; NO cuenta para la nota ──
    # (estado formativo — Black & Wiliam, 1998. Las respuestas no se guardan en métricas)
    practice_index = get_practice_index(class_id, student_id)
    if practice_index is not None and questions:
        if practice_index >= len(questions):
            set_practice_index(class_id, student_id, None)  # índice fuera de rango → cerrar
        else:
            current_q = questions[practice_index]
            rag_context = search_context(
                question=current_q["question"], chunks=cached["chunks"],
                index=cached["index"], model=embedding_model
            ) if cached else ""
            resultado = _procesar_mensaje(current_q["question"], message, rag_context, class_name)

            # Pide ayuda o se va de tema → responder sin avanzar
            if resultado["intencion"] in ("ayuda", "fuera_de_tema"):
                _save_pair(class_id, student_id, message, resultado["mensaje"])
                return ChatResponse(reply=resultado["mensaje"])

            # Es una respuesta → feedback (sin guardar ni portón) y avanzar a la siguiente
            next_index = practice_index + 1
            reply = resultado["feedback"]
            if next_index < len(questions):
                set_practice_index(class_id, student_id, next_index)
                reply += f"\n\nSiguiente pregunta de práctica:\n{questions[next_index]['question']}"
            else:
                set_practice_index(class_id, student_id, None)
                reply += ("\n\n¡Terminaste la práctica! Como te dije, esto no afectó tu nota. "
                          'Si querés practicar de nuevo escribí "practicar", o preguntame cualquier duda.')
            _save_pair(class_id, student_id, message, reply)
            return ChatResponse(reply=reply)

    # Determinar la pregunta activa según el ESTADO en la base de datos (no por texto):
    #  1) si hay una pregunta con reintento pendiente, esa es la activa (robusto)
    #  2) si no, la última que la IA preguntó y que sigue sin tocar (vía historial)
    pending_retry = None
    for q in questions:
        a = answer_map.get(q["id"])
        if a and a["correct"] == "no" and a["attempts"] < MAX_ATTEMPTS:
            pending_retry = q
            break

    if pending_retry is not None:
        active_question = pending_retry
    else:
        last_q = _get_last_asked_question(history, questions)
        active_question = last_q if (last_q and last_q["id"] not in touched_ids) else None

    # ── CASO 2: Alumno listo y sin pregunta activa → dar la primera/siguiente ──
    if _is_ready(message) and open_questions and active_question is None:
        next_q = _get_next_question(questions, touched_ids, class_id, student_id)
        if next_q:
            # La dificultad se usa internamente (métricas y orden adaptativo),
            # pero NO se le muestra al alumno para no condicionar su respuesta.
            reply = (
                f"Genial, empecemos con la primera pregunta.\n\n"
                f"{next_q['question']}"
            )
        else:
            reply = "No hay preguntas registradas para esta clase todavia. Podes preguntarme lo que quieras sobre el texto."
        _save_pair(class_id, student_id, message, reply)
        return ChatResponse(reply=reply)

    # ── CASO 3: Hay una pregunta activa → clasificar intención y aplicar portón ──
    if active_question is not None:
        is_retry = pending_retry is not None
        prev = answer_map.get(active_question["id"]) if is_retry else None

        if not cached:
            logger.warning(f"Caché RAG no disponible para clase {class_id} — evaluando sin contexto")
        rag_context = search_context(
            question=active_question["question"],
            chunks=cached["chunks"],
            index=cached["index"],
            model=embedding_model
        ) if cached else ""

        resultado = _procesar_mensaje(active_question["question"], message, rag_context, class_name)

        # El alumno pide ayuda o se va de tema → responder sin consumir intento ni avanzar
        if resultado["intencion"] in ("ayuda", "fuera_de_tema"):
            _save_pair(class_id, student_id, message, resultado["mensaje"])
            return ChatResponse(reply=resultado["mensaje"])

        # Intención = respuesta → evaluar con el portón de dominio
        now = datetime.now(timezone.utc).isoformat()

        # Primer intento incorrecto → guardar (queda abierta), dar pista y pedir reintento
        if resultado["correct"] == "no" and not is_retry:
            save_student_answer(
                class_id=class_id, student_id=student_id, question_id=active_question["id"],
                answer=message, correct=resultado["correct"], feedback=resultado["feedback"],
                score=resultado["score"], created_at=now, attempts=1,
            )
            hint = _generar_pista(active_question["question"], rag_context, student_answer=message)
            reply = (
                f"{resultado['feedback']}\n\n"
                f"Pista: {hint}\n\n"
                f"Intentá una vez más:\n{active_question['question']}"
            )
            _save_pair(class_id, student_id, message, reply)
            return ChatResponse(reply=reply)

        # Cerrar la pregunta: primer intento bien/parcial, o segundo intento (cualquier resultado)
        if is_retry:
            update_student_answer(
                class_id=class_id, student_id=student_id, question_id=active_question["id"],
                answer=message, correct=resultado["correct"], feedback=resultado["feedback"],
                score=resultado["score"], attempts=prev["attempts"] + 1,
            )
        else:
            save_student_answer(
                class_id=class_id, student_id=student_id, question_id=active_question["id"],
                answer=message, correct=resultado["correct"], feedback=resultado["feedback"],
                score=resultado["score"], created_at=now, attempts=1,
            )

        touched_ids.add(active_question["id"])
        next_q = _get_next_question(questions, touched_ids, class_id, student_id)
        reply = resultado["feedback"]

        if next_q:
            # Sin etiqueta de dificultad: el alumno no debe saber si es facil o dificil.
            reply += f"\n\nSiguiente pregunta:\n{next_q['question']}"
        else:
            refreshed = get_answers_by_student(class_id, student_id)
            avg = sum(a["score"] for a in refreshed) / len(refreshed) if refreshed else 0
            reflection = classroom.get("reflection", "")
            closing = f"\n\n¡Terminaste todas las preguntas! Tu promedio fue {avg:.1f}/10."
            if reflection:
                closing += f"\n\nPara cerrar, una reflexión:\n{reflection}"
            closing += ("\n\nDesde ahora estás en modo libre y esto ya no afecta tu nota. "
                        'Podés preguntarme cualquier duda sobre el texto, o escribir "practicar" '
                        "para volver a intentar las preguntas y desafiarte.")
            reply += closing

        _save_pair(class_id, student_id, message, reply)
        return ChatResponse(reply=reply)

    # ── ESTADO APRENDIZAJE: terminó las preguntas → dudas libres + opción de practicar ──
    # El alumno pide reintentar las preguntas → arranca el modo práctica (no cuenta)
    if _quiere_practicar(message) and questions:
        set_practice_index(class_id, student_id, 0)
        reply = ("¡Dale! Vamos a practicar las preguntas. Esto es solo para vos, no afecta tu nota.\n\n"
                 + questions[0]["question"])
        _save_pair(class_id, student_id, message, reply)
        return ChatResponse(reply=reply)

    # Chat libre: la IA maneja el mensaje (saludo, duda sobre el texto o tema fuera del material).
    # No cortamos por "sin coincidencia RAG" para no responder brusco a un simple saludo.
    rag_context = search_context(
        question=message,
        chunks=cached["chunks"],
        index=cached["index"],
        model=embedding_model
    ) if cached else ""

    recent = get_recent_history(class_id, student_id, HISTORY_LIMIT)
    history_text = _format_history(recent)

    prompt = f"""Sos un tutor educativo para UN alumno de 7mo grado de primaria (12-13 años) en Argentina.
El alumno ya terminó las preguntas evaluativas; ahora es un momento libre de aprendizaje (sin nota).
Hablás con un solo alumno, en singular y con trato cercano.

Reglas:
- Respondé SIEMPRE en español y en singular
- Si el alumno saluda o dice algo social, respondé con calidez y ofrecele tu ayuda
- Si pregunta sobre el texto, respondé basándote ÚNICAMENTE en el texto de abajo, guiando sin dar todo servido
- Si pregunta algo que no está en el texto, decile con amabilidad que eso está fuera del material de la clase
- Si viene al caso, recordale que puede escribir "practicar" para reintentar las preguntas sin que afecte su nota
- Máximo 3-4 oraciones. No uses listas, asteriscos ni encabezados

Texto de la clase:
---
{rag_context if rag_context else "[Sin coincidencias para este mensaje]"}
---

Conversación reciente:
{history_text}
Alumno: {message}
Tutor:"""

    try:
        reply = call_openrouter(prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al contactar la IA: {str(e)}")

    _save_pair(class_id, student_id, message, reply)
    logger.info(f"Aprendizaje (chat libre): alumno {student_id} en clase {class_id}")
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
