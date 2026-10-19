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

QUESTION EASY 1:
¿Qué es la evaporación?

QUESTION EASY 2:
¿Qué es la condensación?

QUESTION MEDIUM 1:
¿Cómo se forma la lluvia?

QUESTION MEDIUM 2:
¿Qué relación hay entre el sol y el ciclo del agua?

QUESTION HARD:
¿Qué rol juega la temperatura en el ciclo hidrológico?

REFLECTION:
El ciclo del agua es fundamental para la vida.
"""
        resultado = parse_generated_activity(texto)
        assert "ciclo del agua" in resultado["introduction"]

    def test_extrae_cinco_preguntas(self):
        """Debe extraer 5 preguntas: 2 fáciles, 2 medias y 1 difícil."""
        texto = """
INTRODUCTION:
Introducción de prueba.

QUESTION EASY 1:
¿Qué es la fotosíntesis?

QUESTION EASY 2:
¿Qué necesitan las plantas para hacerla?

QUESTION MEDIUM 1:
¿Dónde ocurre la fotosíntesis?

QUESTION MEDIUM 2:
¿Por qué es importante para el oxígeno?

QUESTION HARD:
¿Cómo afecta la luz a la tasa de fotosíntesis?

REFLECTION:
La fotosíntesis es esencial para los ecosistemas.
"""
        resultado = parse_generated_activity(texto)
        preguntas = resultado["questions"]
        assert len(preguntas) == 5
        dificultades = [p.difficulty for p in preguntas]
        assert dificultades == ["easy", "easy", "medium", "medium", "hard"]

    def test_extrae_reflexion(self):
        """Debe extraer la sección REFLECTION correctamente."""
        texto = """
INTRODUCTION:
Intro.

QUESTION EASY 1:
Pregunta fácil uno.

QUESTION EASY 2:
Pregunta fácil dos.

QUESTION MEDIUM 1:
Pregunta media uno.

QUESTION MEDIUM 2:
Pregunta media dos.

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
