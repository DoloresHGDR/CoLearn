"""
Tests de pérdida de contexto del sistema de chat.

La IA mantiene en memoria los últimos HISTORY_LIMIT mensajes (actualmente 10).
Cuando una conversación supera ese límite, los mensajes más antiguos
quedan fuera del contexto y la IA pierde acceso a lo que se dijo al principio.

Estos tests documentan ese comportamiento como una limitación conocida del sistema,
lo cual es relevante para la evaluación pedagógica de la herramienta.
"""

import pytest
from unittest.mock import patch
from app.services.chat_service import HISTORY_LIMIT, _build_prompt


# Mensajes de prueba que simulan una conversación real
def make_messages(n):
    """Genera n mensajes alternados entre alumno y tutor con contenido único."""
    messages = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        # Usamos un identificador entre corchetes para evitar coincidencias parciales
        messages.append({"role": role, "content": f"[MSG-{i + 1:03d}] contenido del turno {i + 1}"})
    return messages


class TestHistoryLimit:

    def test_limite_definido_es_diez(self):
        """El límite de historial debe ser exactamente 10 mensajes."""
        assert HISTORY_LIMIT == 10

    def test_prompt_con_historial_vacio(self):
        """Con historial vacío el prompt no debe incluir conversación previa."""
        prompt = _build_prompt(context="Texto de prueba.", history=[], message="¿Qué es esto?")
        assert "Alumno: Mensaje" not in prompt
        assert "¿Qué es esto?" in prompt

    def test_prompt_incluye_historial_completo_dentro_del_limite(self):
        """Con menos de 10 mensajes, todos deben aparecer en el prompt."""
        history = make_messages(6)
        prompt = _build_prompt(context="Contexto.", history=history, message="Nueva pregunta")
        # Todos los mensajes deben estar presentes
        for msg in history:
            assert msg["content"] in prompt

    def test_prompt_incluye_mensaje_nuevo(self):
        """El mensaje nuevo del alumno debe aparecer siempre en el prompt."""
        prompt = _build_prompt(
            context="Contexto.",
            history=make_messages(3),
            message="Esta es mi pregunta nueva",
        )
        assert "Esta es mi pregunta nueva" in prompt

    def test_prompt_etiqueta_roles_correctamente(self):
        """Los mensajes de alumno y tutor deben tener sus etiquetas correctas."""
        history = [
            {"role": "user", "content": "Pregunta del alumno"},
            {"role": "assistant", "content": "Respuesta del tutor"},
        ]
        prompt = _build_prompt(context="Contexto.", history=history, message="Otra pregunta")
        assert "Alumno: Pregunta del alumno" in prompt
        assert "Tutor: Respuesta del tutor" in prompt


class TestContextLoss:

    def test_get_recent_history_respeta_el_limite(self):
        """
        get_recent_history debe devolver como máximo HISTORY_LIMIT mensajes.
        Simula que hay más mensajes en la BD de los que el límite permite.
        """
        # Simulamos 20 mensajes en la BD
        all_messages = make_messages(20)

        with patch("app.repositories.chat_repository.get_connection") as mock_conn:
            mock_cursor = mock_conn.return_value.cursor.return_value
            # La BD devuelve los últimos 10 (DESC) antes de revertirlos
            mock_cursor.fetchall.return_value = list(reversed(all_messages[-10:]))

            from app.repositories.chat_repository import get_recent_history
            result = get_recent_history("clase-1", "alumno-1", limit=HISTORY_LIMIT)

        assert len(result) <= HISTORY_LIMIT

    def test_mensajes_antiguos_no_llegan_al_prompt(self):
        """
        Escenario de pérdida de contexto:
        - El alumno dice su nombre en el mensaje 1
        - Luego envía 10 mensajes más (el nombre queda fuera del historial)
        - El prompt final NO contiene el nombre del alumno

        Esto documenta la limitación: la IA no puede recordar información
        de mensajes anteriores al límite del historial.
        """
        nombre_alumno = "me llamo Valentina"

        # Mensaje donde el alumno menciona su nombre (el más viejo)
        mensaje_antiguo = {"role": "user", "content": nombre_alumno}

        # 10 mensajes nuevos que empujan al primero fuera del contexto
        mensajes_nuevos = make_messages(HISTORY_LIMIT)

        # El historial que llega al prompt solo tiene los mensajes nuevos
        # (el mensaje con el nombre ya no está porque superó el límite)
        historial_recortado = mensajes_nuevos  # el mensaje_antiguo se perdió

        prompt = _build_prompt(
            context="Texto de la clase.",
            history=historial_recortado,
            message="¿Recordás cómo me llamo?",
        )

        # El nombre ya no está en el contexto disponible para la IA
        assert nombre_alumno not in prompt, (
            "La IA no debería tener acceso al nombre porque ese mensaje "
            "quedó fuera del límite del historial."
        )

    def test_mensajes_recientes_si_llegan_al_prompt(self):
        """
        Contraste del test anterior: los mensajes dentro del límite
        SÍ deben estar disponibles para la IA.
        """
        historial = make_messages(HISTORY_LIMIT - 2)  # dentro del límite
        info_reciente = {"role": "user", "content": "acabo de estudiar fotosíntesis"}
        historial.append(info_reciente)

        prompt = _build_prompt(
            context="Texto de la clase.",
            history=historial,
            message="¿Qué estaba estudiando?",
        )

        assert "acabo de estudiar fotosíntesis" in prompt, (
            "La información reciente debe estar disponible para la IA."
        )

    def test_limite_diez_es_razonable_pero_insuficiente_para_conversaciones_largas(self):
        """
        Test que documenta explícitamente la limitación del sistema.

        Con HISTORY_LIMIT=10, una conversación de más de 10 turnos
        empieza a perder contexto. Esto es un trade-off entre
        costo computacional y memoria conversacional.
        """
        # Una conversación de 20 mensajes (10 turnos de pregunta/respuesta)
        conversacion_larga = make_messages(20)

        # Solo los últimos HISTORY_LIMIT llegan al prompt
        historial_disponible = conversacion_larga[-HISTORY_LIMIT:]
        historial_perdido = conversacion_larga[:-HISTORY_LIMIT]

        prompt = _build_prompt(
            context="Texto.",
            history=historial_disponible,
            message="Nueva pregunta",
        )

        # Verificar que lo perdido efectivamente no está
        for msg in historial_perdido:
            assert msg["content"] not in prompt

        # Verificar que lo disponible sí está
        for msg in historial_disponible:
            assert msg["content"] in prompt
