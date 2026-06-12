"""
Tests unitarios para el parser de actividades generadas por la IA.
Verifica que la extracción de secciones (introducción, preguntas, reflexión) funciona.
"""

import pytest
from app.services.parser_service import parse_generated_activity


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
