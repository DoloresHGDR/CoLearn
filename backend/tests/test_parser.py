"""
Tests unitarios para el parser de respuestas de la IA.
Verifica que la extracción de secciones funciona correctamente.
"""

import pytest
from app.services.parser_service import parse_generated_activity, parse_evaluation


# --- Tests de parse_generated_activity ---

class TestParseGeneratedActivity:

    def test_extrae_introduccion(self):
        """Debe extraer el texto de la sección INTRODUCTION."""
        texto = """
INTRODUCTION:
Este texto habla sobre el ciclo del agua.

QUESTION EASY:
¿Qué es la evaporación?

QUESTION MEDIUM:
¿Cómo se forma la lluvia?

QUESTION HARD:
¿Qué rol juega la temperatura en el ciclo hidrológico?

REFLECTION:
El ciclo del agua es fundamental para la vida.
"""
        resultado = parse_generated_activity(texto)
        assert "ciclo del agua" in resultado["introduction"]

    def test_extrae_tres_preguntas(self):
        """Debe extraer exactamente 3 preguntas con sus dificultades."""
        texto = """
INTRODUCTION:
Introducción de prueba.

QUESTION EASY:
¿Qué es la fotosíntesis?

QUESTION MEDIUM:
¿Dónde ocurre la fotosíntesis?

QUESTION HARD:
¿Cómo afecta la luz a la tasa de fotosíntesis?

REFLECTION:
La fotosíntesis es esencial para los ecosistemas.
"""
        resultado = parse_generated_activity(texto)
        preguntas = resultado["questions"]
        assert len(preguntas) == 3
        dificultades = [p.difficulty for p in preguntas]
        assert "easy" in dificultades
        assert "medium" in dificultades
        assert "hard" in dificultades

    def test_extrae_reflexion(self):
        """Debe extraer la sección REFLECTION correctamente."""
        texto = """
INTRODUCTION:
Intro.

QUESTION EASY:
Pregunta fácil.

QUESTION MEDIUM:
Pregunta media.

QUESTION HARD:
Pregunta difícil.

REFLECTION:
Esta es la reflexión final del tema.
"""
        resultado = parse_generated_activity(texto)
        assert "reflexión final" in resultado["reflection"]

    def test_seccion_faltante_devuelve_vacia(self):
        """Si falta una sección, debe devolver string vacío (no fallar)."""
        texto = """
INTRODUCTION:
Solo hay introducción aquí.
"""
        resultado = parse_generated_activity(texto)
        assert resultado["introduction"] != ""
        assert resultado["reflection"] == ""
        assert resultado["questions"] == []


# --- Tests de parse_evaluation ---

class TestParseEvaluation:

    def test_respuesta_correcta(self):
        """Debe detectar 'si' como resultado correcto."""
        texto = """
CORRECT:
si

FEEDBACK:
Muy bien, la respuesta es correcta y completa.

SCORE:
9
"""
        resultado = parse_evaluation(texto)
        assert resultado["correct"] == "si"
        assert resultado["score"] == 9
        assert "correcta" in resultado["feedback"]

    def test_respuesta_incorrecta(self):
        """Debe detectar 'no' como resultado incorrecto."""
        texto = """
CORRECT:
no

FEEDBACK:
La respuesta no es correcta. Revisá el concepto de evaporación.

SCORE:
0
"""
        resultado = parse_evaluation(texto)
        assert resultado["correct"] == "no"
        assert resultado["score"] == 0

    def test_respuesta_parcial(self):
        """Debe detectar 'parcial' correctamente."""
        texto = """
CORRECT:
parcial

FEEDBACK:
Mencionaste parte del proceso pero faltó incluir la condensación.

SCORE:
5
"""
        resultado = parse_evaluation(texto)
        assert resultado["correct"] == "parcial"
        assert resultado["score"] == 5

    def test_score_fuera_de_rango_se_limita(self):
        """El score debe limitarse entre 0 y 10 aunque Gemini devuelva otro valor."""
        texto = """
CORRECT:
si

FEEDBACK:
Excelente respuesta.

SCORE:
15
"""
        resultado = parse_evaluation(texto)
        assert resultado["score"] <= 10

    def test_score_invalido_usa_fallback(self):
        """Si el score no es un número, debe usar el valor por defecto según 'correct'."""
        texto = """
CORRECT:
si

FEEDBACK:
Muy bien.

SCORE:
perfecto
"""
        resultado = parse_evaluation(texto)
        # Para 'si' el fallback es 10
        assert resultado["score"] == 10
