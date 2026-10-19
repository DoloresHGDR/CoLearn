"""
Tests del módulo de seguimiento docente: métricas de la clase.

Verifican que las métricas que ve el docente se calculan bien a partir de las
respuestas registradas de los alumnos, y la regla que elige el nivel de la
próxima pregunta. Los repositorios se reemplazan por dobles de prueba
(sin base de datos real).
"""

from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.services.metrics_service import _recommended_level, _score_by_difficulty, get_metrics

CLASE = {"id": "clase-1", "name": "El ciclo del agua", "teacher_id": "docente-1"}


def make_answer(question_id, score, difficulty):
    """Arma una respuesta registrada tal como la devuelve la base de datos."""
    return {
        "question_id": question_id,
        "correct": "si" if score >= 7 else "no",
        "score": score,
        "difficulty": difficulty,
        "created_at": f"2026-10-01T10:0{question_id}:00+00:00",
    }


# --- Puntaje por nivel de dificultad ---

class TestPuntajePorDificultad:

    def test_promedia_cada_nivel_por_separado(self):
        """Cada nivel tiene su propio promedio, calculado solo con sus respuestas."""
        respuestas = [
            make_answer(1, 10, "easy"),
            make_answer(2, 8, "easy"),
            make_answer(3, 6, "medium"),
            make_answer(4, 3, "medium"),
            make_answer(5, 2, "hard"),
        ]
        assert _score_by_difficulty(respuestas) == {"easy": 9.0, "medium": 4.5, "hard": 2.0}

    def test_redondea_a_un_decimal(self):
        """Un promedio periódico (20/3 = 6,666...) se redondea a un decimal: 6,7."""
        respuestas = [make_answer(1, 10, "easy"), make_answer(2, 6, "easy"), make_answer(3, 4, "easy")]
        assert _score_by_difficulty(respuestas) == {"easy": 6.7}

    def test_omite_niveles_sin_respuestas(self):
        """Si el alumno no respondió preguntas de un nivel, ese nivel no aparece."""
        respuestas = [make_answer(1, 9, "easy"), make_answer(5, 4, "hard")]
        assert _score_by_difficulty(respuestas) == {"easy": 9.0, "hard": 4.0}


# --- Métricas de la clase para el docente ---

@pytest.fixture
def clase_con_dos_alumnos(mocker):
    """
    Clase con dos alumnos inscriptos: Ana respondió 3 preguntas y Bruno ninguna.
    Los repositorios se reemplazan por dobles de prueba.
    """
    respuestas = {
        "alumno-1": [
            make_answer(1, 10, "easy"),
            make_answer(2, 7, "easy"),
            make_answer(5, 3, "hard"),
        ],
        "alumno-2": [],
    }
    filas = [
        # PostgreSQL calcula el promedio con AVG y lo devuelve como Decimal: (10 + 7 + 3) / 3
        {"student_id": "alumno-1", "name": "Ana", "email": "ana@alumno.escuela.edu.ar",
         "message_count": 9, "answers_submitted": 3,
         "average_score": Decimal("6.6666666666666667"), "joined_at": "2026-10-01T09:00:00+00:00"},
        # Sin respuestas, COALESCE(AVG(score), 0) devuelve 0
        {"student_id": "alumno-2", "name": "Bruno", "email": "bruno@alumno.escuela.edu.ar",
         "message_count": 2, "answers_submitted": 0,
         "average_score": Decimal("0"), "joined_at": "2026-10-01T09:05:00+00:00"},
    ]
    mocker.patch("app.services.metrics_service.get_class_by_id", return_value=CLASE)
    mocker.patch("app.services.metrics_service.get_class_metrics", return_value=filas)
    mocker.patch(
        "app.services.metrics_service.get_student_answer_history",
        side_effect=lambda class_id, student_id: respuestas[student_id],
    )
    mocker.patch("app.services.metrics_service.get_feedback_stats",
                 return_value={"total": 2, "positive": 1})


class TestMetricasDeLaClase:

    def test_promedio_del_alumno_con_un_decimal(self, clase_con_dos_alumnos):
        """El promedio de Ana (20/3 = 6,666...) se muestra con un decimal: 6,7."""
        ana = get_metrics("clase-1", "docente-1").students[0]
        assert ana.answers_submitted == 3
        assert ana.average_score == 6.7

    def test_puntaje_por_nivel_sale_de_sus_respuestas(self, clase_con_dos_alumnos):
        """Fácil: (10 + 7) / 2 = 8,5. Difícil: 3. Medio no aparece porque no respondió ninguna."""
        ana = get_metrics("clase-1", "docente-1").students[0]
        assert ana.score_by_difficulty == {"easy": 8.5, "hard": 3.0}

    def test_historial_conserva_cada_respuesta(self, clase_con_dos_alumnos):
        """El historial muestra cada respuesta con su puntaje y su nivel, en orden."""
        ana = get_metrics("clase-1", "docente-1").students[0]
        assert [(r.question_id, r.score, r.difficulty) for r in ana.answer_history] == [
            (1, 10, "easy"),
            (2, 7, "easy"),
            (5, 3, "hard"),
        ]

    def test_alumno_sin_respuestas_queda_en_cero(self, clase_con_dos_alumnos):
        """Bruno está inscripto pero no respondió: promedio 0 y sin puntajes por nivel."""
        bruno = get_metrics("clase-1", "docente-1").students[1]
        assert bruno.answers_submitted == 0
        assert bruno.average_score == 0.0
        assert bruno.score_by_difficulty == {}
        assert bruno.answer_history == []

    def test_datos_generales_de_la_clase(self, clase_con_dos_alumnos):
        """La clase informa cuántos alumnos hay inscriptos y cómo votaron al tutor."""
        metricas = get_metrics("clase-1", "docente-1")
        assert metricas.enrolled_count == 2
        assert metricas.feedback_total == 2
        assert metricas.feedback_positive == 1

    def test_clase_inexistente_da_404(self, mocker):
        """Si la clase no existe, se responde 404."""
        mocker.patch("app.services.metrics_service.get_class_by_id", return_value=None)
        with pytest.raises(HTTPException) as error:
            get_metrics("no-existe", "docente-1")
        assert error.value.status_code == 404

    def test_otro_docente_no_puede_ver_las_metricas(self, mocker):
        """Un docente que no es dueño de la clase recibe 403 y no se leen los datos de los alumnos."""
        mocker.patch("app.services.metrics_service.get_class_by_id", return_value=CLASE)
        consulta = mocker.patch("app.services.metrics_service.get_class_metrics")
        with pytest.raises(HTTPException) as error:
            get_metrics("clase-1", "otro-docente")
        assert error.value.status_code == 403
        consulta.assert_not_called()


# --- Nivel recomendado para la próxima pregunta ---

class TestNivelRecomendado:

    def test_con_menos_de_dos_respuestas_empieza_en_facil(self):
        """Con 0 o 1 respuesta no hay datos suficientes: aunque sea un 10, sigue en 'easy'."""
        assert _recommended_level(0, 0.0) == "easy"
        assert _recommended_level(1, 10.0) == "easy"
        # Con 2 respuestas ya se tiene en cuenta el promedio
        assert _recommended_level(2, 10.0) == "hard"

    def test_promedio_menor_a_cinco_es_facil(self):
        """Con promedio por debajo de 5/10 el alumno sigue en 'easy'."""
        assert _recommended_level(3, 4.9) == "easy"

    def test_borde_cinco_ya_es_medio(self):
        """Un promedio de exactamente 5,0 alcanza para pasar a 'medium'."""
        assert _recommended_level(3, 5.0) == "medium"

    def test_promedio_menor_a_siete_es_medio(self):
        """Con promedio entre 5 y 7 (sin llegar a 7) el alumno queda en 'medium'."""
        assert _recommended_level(3, 6.9) == "medium"

    def test_borde_siete_ya_es_dificil(self):
        """Un promedio de exactamente 7,0 (70 %) alcanza para pasar a 'hard'."""
        assert _recommended_level(3, 7.0) == "hard"
