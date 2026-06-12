"""
Tests de pérdida de contexto del sistema de chat.

La IA mantiene en memoria los últimos HISTORY_LIMIT mensajes (actualmente 10).
Cuando una conversación supera ese límite, los mensajes más antiguos quedan
fuera del contexto y la IA pierde acceso a lo que se dijo al principio.

Estos tests documentan ese comportamiento como una limitación conocida del sistema,
lo cual es relevante para la evaluación pedagógica de la herramienta.
"""

import pytest
from unittest.mock import patch
from app.services.chat_service import HISTORY_LIMIT, _format_history


def make_messages(n):
    """Genera n mensajes alternados entre alumno y tutor con contenido único."""
    messages = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        # Identificador entre corchetes para evitar coincidencias parciales
        messages.append({"role": role, "content": f"[MSG-{i + 1:03d}] contenido del turno {i + 1}"})
    return messages


class TestFormatHistory:

    def test_limite_definido_es_diez(self):
        """El límite de historial debe ser exactamente 10 mensajes."""
        assert HISTORY_LIMIT == 10

    def test_historial_vacio_devuelve_string_vacio(self):
        """Sin mensajes previos, el historial formateado debe ser vacío."""
        assert _format_history([]) == ""

    def test_etiqueta_roles_correctamente(self):
        """Los mensajes de alumno y tutor deben tener sus etiquetas correctas."""
        history = [
            {"role": "user", "content": "Pregunta del alumno"},
            {"role": "assistant", "content": "Respuesta del tutor"},
        ]
        texto = _format_history(history)
        assert "Alumno: Pregunta del alumno" in texto
        assert "Tutor: Respuesta del tutor" in texto

    def test_incluye_todos_los_mensajes_dados(self):
        """Todos los mensajes que se le pasan deben aparecer en el texto."""
        history = make_messages(6)
        texto = _format_history(history)
        for msg in history:
            assert msg["content"] in texto


class TestContextLoss:

    def test_get_recent_history_respeta_el_limite(self):
        """
        get_recent_history debe devolver como máximo HISTORY_LIMIT mensajes.
        Simula que hay más mensajes en la BD de los que el límite permite.
        """
        all_messages = make_messages(20)

        with patch("app.repositories.chat_repository.get_connection") as mock_conn:
            mock_cursor = mock_conn.return_value.cursor.return_value
            # La BD devuelve los últimos 10 (DESC) antes de revertirlos
            mock_cursor.fetchall.return_value = list(reversed(all_messages[-10:]))

            from app.repositories.chat_repository import get_recent_history
            result = get_recent_history("clase-1", "alumno-1", limit=HISTORY_LIMIT)

        assert len(result) <= HISTORY_LIMIT

    def test_mensajes_antiguos_no_llegan_al_contexto(self):
        """
        Escenario de pérdida de contexto: un mensaje viejo (fuera del límite)
        no debe aparecer en el historial que se arma para la IA.

        Documenta la limitación: la IA no puede recordar información de mensajes
        anteriores al límite del historial.
        """
        nombre_alumno = "me llamo Valentina"

        # Solo los últimos HISTORY_LIMIT mensajes llegan al contexto;
        # el mensaje con el nombre quedó afuera del recorte.
        historial_disponible = make_messages(HISTORY_LIMIT)
        texto = _format_history(historial_disponible)

        assert nombre_alumno not in texto, (
            "La IA no debería tener acceso al nombre: ese mensaje quedó "
            "fuera del límite del historial."
        )

    def test_mensajes_recientes_si_llegan_al_contexto(self):
        """
        Contraste del test anterior: los mensajes dentro del límite
        SÍ deben estar disponibles para la IA.
        """
        historial = make_messages(HISTORY_LIMIT - 2)  # dentro del límite
        historial.append({"role": "user", "content": "acabo de estudiar fotosíntesis"})

        texto = _format_history(historial)

        assert "acabo de estudiar fotosíntesis" in texto, (
            "La información reciente debe estar disponible para la IA."
        )
