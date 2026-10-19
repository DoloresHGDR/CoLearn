"""
Tests del módulo de seguimiento docente: resumen de la clase con IA.

El resumen se guarda junto con una "huella" de los datos de desempeño
(cantidad de respuestas : suma de puntajes). Estos tests verifican que solo
se llama a la IA cuando esa huella cambia. La base de datos y la llamada a
OpenRouter se reemplazan por dobles de prueba.
"""

import pytest
import requests
from fastapi import HTTPException

from app.models.schemas import ClassMetrics, StudentMetrics
from app.services.summary_service import get_class_summary


def make_class(summary="", fingerprint=""):
    """Arma la fila de la clase con el último resumen guardado y su huella."""
    return {
        "id": "clase-1",
        "name": "El ciclo del agua",
        "teacher_id": "docente-1",
        "summary": summary,
        "summary_fingerprint": fingerprint,
    }


def make_metrics():
    """Métricas de una clase con dos alumnos: Ana respondió 4 de las 5 preguntas y Bruno ninguna."""
    ana = StudentMetrics(
        student_id="alumno-1", name="Ana", email="ana@alumno.escuela.edu.ar",
        message_count=9, answers_submitted=4, average_score=7.5,
        score_by_difficulty={"easy": 9.0, "medium": 6.0},
        answer_history=[], joined_at="2026-10-01T09:00:00+00:00",
    )
    bruno = StudentMetrics(
        student_id="alumno-2", name="Bruno", email="bruno@alumno.escuela.edu.ar",
        message_count=2, answers_submitted=0, average_score=0.0,
        score_by_difficulty={}, answer_history=[], joined_at="2026-10-01T09:05:00+00:00",
    )
    return ClassMetrics(class_id="clase-1", class_name="El ciclo del agua",
                        enrolled_count=2, students=[ana, bruno])


def mock_dependencies(mocker, clase, total, sum_scores):
    """
    Reemplaza la base de datos y la IA por dobles de prueba.
    total y sum_scores son los datos de desempeño actuales de la clase.
    Devuelve los dobles de la IA y del guardado para revisar si se usaron.
    """
    mocker.patch("app.services.summary_service.get_class_by_id", return_value=clase)
    mocker.patch("app.services.summary_service.get_class_answer_stats",
                 return_value={"total": total, "sum_scores": sum_scores})
    mocker.patch("app.services.summary_service.get_metrics", return_value=make_metrics())
    # La actividad tiene 5 preguntas (2 fáciles, 2 medias y 1 difícil)
    mocker.patch("app.services.summary_service.get_questions_by_class",
                 return_value=[{"id": i} for i in range(1, 6)])
    ia = mocker.patch("app.services.summary_service.call_openrouter", return_value="Resumen nuevo.")
    guardar = mocker.patch("app.services.summary_service.update_class_summary")
    return ia, guardar


class TestResumenDeLaClase:

    def test_sin_respuestas_no_llama_a_la_ia(self, mocker):
        """Si ningún alumno respondió todavía, no se llama a la IA (no hay nada que resumir)."""
        ia, guardar = mock_dependencies(mocker, make_class(), total=0, sum_scores=0)

        resultado = get_class_summary("clase-1", "docente-1")

        assert resultado["generated"] is False
        assert "Todavía no hay actividad" in resultado["summary"]
        ia.assert_not_called()
        guardar.assert_not_called()

    def test_reutiliza_el_resumen_si_no_cambian_los_datos(self, mocker):
        """Con la misma huella (4 respuestas, suma 30) se devuelve el resumen guardado."""
        clase = make_class(summary="Resumen guardado.", fingerprint="4:30")
        ia, guardar = mock_dependencies(mocker, clase, total=4, sum_scores=30)

        resultado = get_class_summary("clase-1", "docente-1")

        assert resultado == {"summary": "Resumen guardado.", "generated": False}
        ia.assert_not_called()
        guardar.assert_not_called()

    def test_regenera_cuando_hay_una_respuesta_nueva(self, mocker):
        """Una respuesta nueva cambia la huella (4:30 → 5:38): se genera y se guarda otro resumen."""
        clase = make_class(summary="Resumen guardado.", fingerprint="4:30")
        ia, guardar = mock_dependencies(mocker, clase, total=5, sum_scores=38)

        resultado = get_class_summary("clase-1", "docente-1")

        assert resultado == {"summary": "Resumen nuevo.", "generated": True}
        ia.assert_called_once()
        guardar.assert_called_once_with("clase-1", "Resumen nuevo.", "5:38")

    def test_regenera_cuando_un_reintento_cambia_el_puntaje(self, mocker):
        """
        Un reintento no agrega respuestas pero cambia el puntaje (suma 30 → 34):
        la huella cambia (4:30 → 4:34) y el resumen se regenera.
        """
        clase = make_class(summary="Resumen guardado.", fingerprint="4:30")
        ia, guardar = mock_dependencies(mocker, clase, total=4, sum_scores=34)

        resultado = get_class_summary("clase-1", "docente-1")

        assert resultado == {"summary": "Resumen nuevo.", "generated": True}
        ia.assert_called_once()
        guardar.assert_called_once_with("clase-1", "Resumen nuevo.", "4:34")

    def test_si_la_ia_falla_devuelve_el_ultimo_resumen(self, mocker):
        """
        Si OpenRouter no responde, el docente ve el último resumen disponible.
        No se guarda nada, así la próxima consulta vuelve a intentar.
        """
        clase = make_class(summary="Resumen guardado.", fingerprint="4:30")
        ia, guardar = mock_dependencies(mocker, clase, total=5, sum_scores=38)
        ia.side_effect = requests.exceptions.Timeout("OpenRouter no responde")

        resultado = get_class_summary("clase-1", "docente-1")

        assert resultado == {"summary": "Resumen guardado.", "generated": False}
        guardar.assert_not_called()

    def test_si_la_ia_falla_sin_resumen_previo_da_502(self, mocker):
        """Si la IA falla y nunca se generó un resumen, se informa el error (502)."""
        ia, guardar = mock_dependencies(mocker, make_class(), total=5, sum_scores=38)
        ia.side_effect = requests.exceptions.Timeout("OpenRouter no responde")

        with pytest.raises(HTTPException) as error:
            get_class_summary("clase-1", "docente-1")

        assert error.value.status_code == 502
        guardar.assert_not_called()

    def test_prompt_usa_el_total_real_de_preguntas(self, mocker):
        """
        El prompt dice cuántas preguntas respondió cada alumno sobre el total
        real de la actividad (5), y no sobre un 3 fijo como antes.
        """
        ia, _ = mock_dependencies(mocker, make_class(), total=4, sum_scores=30)

        get_class_summary("clase-1", "docente-1")

        prompt = ia.call_args.args[0]
        assert "[A1]: 4 de 5 preguntas respondidas" in prompt
        assert "de 3 preguntas" not in prompt

    def test_prompt_incluye_a_quien_no_respondio(self, mocker):
        """Un alumno sin respuestas aparece igual en el prompt, para que el resumen pueda nombrarlo."""
        ia, _ = mock_dependencies(mocker, make_class(), total=4, sum_scores=30)

        get_class_summary("clase-1", "docente-1")

        prompt = ia.call_args.args[0]
        assert "[A2]: 0 de 5 preguntas respondidas" in prompt
        assert "sin respuestas" in prompt

    def test_el_prompt_no_incluye_datos_personales(self, mocker):
        """
        Protección de datos de menores: a la IA externa no le llega ningún nombre
        ni correo de los alumnos, solo los códigos [A1] y [A2].
        """
        ia, _ = mock_dependencies(mocker, make_class(), total=4, sum_scores=30)

        get_class_summary("clase-1", "docente-1")

        prompt = ia.call_args.args[0]
        for dato in ("Ana", "Bruno", "ana@alumno.escuela.edu.ar", "bruno@alumno.escuela.edu.ar"):
            assert dato not in prompt

    def test_el_resumen_muestra_los_nombres_reales(self, mocker):
        """El docente ve los nombres reales: los códigos de la respuesta se reemplazan en el servidor."""
        ia, guardar = mock_dependencies(mocker, make_class(), total=4, sum_scores=30)
        ia.return_value = "[A1] avanza bien, pero [A2] todavía no respondió ninguna pregunta."

        resultado = get_class_summary("clase-1", "docente-1")

        esperado = "Ana avanza bien, pero Bruno todavía no respondió ninguna pregunta."
        assert resultado == {"summary": esperado, "generated": True}
        guardar.assert_called_once_with("clase-1", esperado, "4:30")

    def test_codigo_sin_corchetes_tambien_se_reemplaza(self, mocker):
        """Si la IA escribe el código sin corchetes (A2), el nombre real se recupera igual."""
        ia, _ = mock_dependencies(mocker, make_class(), total=4, sum_scores=30)
        ia.return_value = "A2 necesita apoyo para empezar la actividad."

        resultado = get_class_summary("clase-1", "docente-1")

        assert resultado["summary"] == "Bruno necesita apoyo para empezar la actividad."

    def test_clase_inexistente_da_404(self, mocker):
        """Si la clase no existe, se responde 404 y no se llama a la IA."""
        ia, _ = mock_dependencies(mocker, None, total=4, sum_scores=30)

        with pytest.raises(HTTPException) as error:
            get_class_summary("no-existe", "docente-1")

        assert error.value.status_code == 404
        ia.assert_not_called()

    def test_otro_docente_no_puede_ver_el_resumen(self, mocker):
        """Un docente que no es dueño de la clase recibe 403 y no se llama a la IA."""
        ia, _ = mock_dependencies(mocker, make_class(), total=4, sum_scores=30)

        with pytest.raises(HTTPException) as error:
            get_class_summary("clase-1", "otro-docente")

        assert error.value.status_code == 403
        ia.assert_not_called()
