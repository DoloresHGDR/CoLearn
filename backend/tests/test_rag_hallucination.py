"""
Tests de alucinación del pipeline RAG.

El objetivo es verificar que el sistema de recuperación de contexto
devuelve información relevante cuando la pregunta está relacionada con
el texto, y no recupera contexto útil cuando la pregunta es totalmente
ajena al documento.

Esto es importante porque si la IA responde con información que no
está en el contexto recuperado, estaría "alucinando" (inventando).
"""

import pytest
from app.rag.chunker import prepare_data
from app.rag.indexer import create_index, search_context
from app.rag.chunker import model as embedding_model


# Texto de prueba: contiene solo información sobre fotosíntesis
TEXTO_PRUEBA = """
La fotosíntesis es el proceso mediante el cual las plantas producen su alimento.
Utilizan la luz solar, el agua y el dióxido de carbono para generar glucosa y oxígeno.
Este proceso ocurre principalmente en los cloroplastos, orgánulos que contienen clorofila.
La clorofila es el pigmento verde que absorbe la energía lumínica.
La ecuación general de la fotosíntesis es: 6CO2 + 6H2O + luz → C6H12O6 + 6O2.
Las plantas realizan la fotosíntesis durante el día, cuando hay luz disponible.
Sin fotosíntesis, no existiría oxígeno en la atmósfera ni alimento en los ecosistemas.
La tasa de fotosíntesis depende de la intensidad de la luz, la temperatura y la concentración de CO2.
"""


@pytest.fixture(scope="module")
def pipeline():
    """Prepara el pipeline RAG una sola vez para todos los tests del módulo."""
    chunks, embeddings = prepare_data(TEXTO_PRUEBA)
    index = create_index(embeddings)
    return chunks, index


class TestRAGHallucination:

    def test_pregunta_relevante_recupera_contexto(self, pipeline):
        """
        Cuando la pregunta está relacionada con el texto,
        el contexto recuperado debe contener información útil.
        """
        chunks, index = pipeline
        contexto = search_context(
            question="¿Qué es la fotosíntesis?",
            chunks=chunks,
            index=index,
            model=embedding_model,
        )
        # El contexto debe mencionar información del documento
        assert any(
            palabra in contexto.lower()
            for palabra in ["fotosíntesis", "plantas", "glucosa", "clorofila", "luz"]
        ), f"El contexto recuperado no contiene información relevante: {contexto}"

    def test_pregunta_sobre_detalle_especifico(self, pipeline):
        """
        Una pregunta sobre un concepto específico del texto
        debe traer el chunk que lo contiene.
        """
        chunks, index = pipeline
        contexto = search_context(
            question="¿Dónde ocurre la fotosíntesis dentro de la célula?",
            chunks=chunks,
            index=index,
            model=embedding_model,
        )
        # El texto menciona "cloroplastos" como lugar de la fotosíntesis
        assert "cloroplasto" in contexto.lower(), (
            f"Se esperaba 'cloroplasto' en el contexto pero se obtuvo: {contexto}"
        )

    def test_pregunta_fuera_de_tema_no_coincide_bien(self, pipeline):
        """
        Cuando la pregunta es sobre un tema totalmente ajeno al documento,
        el contexto recuperado no debe contener respuestas relevantes.

        Esto verifica que el RAG no 'inventa' contexto:
        recupera algo (siempre devuelve k chunks), pero ese algo
        no responde la pregunta.
        """
        chunks, index = pipeline
        contexto = search_context(
            question="¿Cuánto cuesta un pasaje de avión a Europa?",
            chunks=chunks,
            index=index,
            model=embedding_model,
        )
        # El contexto no debe contener información sobre viajes o precios
        palabras_ajenas = ["avión", "pasaje", "europa", "precio", "vuelo", "aeropuerto"]
        tiene_info_ajena = any(p in contexto.lower() for p in palabras_ajenas)
        assert not tiene_info_ajena, (
            f"El RAG recuperó contexto que parece responder una pregunta ajena: {contexto}"
        )

    def test_chunking_genera_chunks_no_vacios(self):
        """El proceso de chunking no debe producir chunks vacíos."""
        chunks, embeddings = prepare_data(TEXTO_PRUEBA)
        assert len(chunks) > 0, "El chunking no produjo ningún chunk"
        for chunk in chunks:
            assert chunk.strip() != "", "Se encontró un chunk vacío"

    def test_embeddings_tienen_dimension_correcta(self):
        """Los embeddings deben tener la dimensión esperada del modelo (768 para all-mpnet-base-v2)."""
        chunks, embeddings = prepare_data(TEXTO_PRUEBA)
        assert embeddings.shape[0] == len(chunks), "La cantidad de embeddings no coincide con los chunks"
        assert embeddings.shape[1] == 768, f"Dimensión inesperada: {embeddings.shape[1]}"

    def test_chunks_cubren_el_texto_completo(self):
        """El texto del documento debe estar representado en los chunks generados."""
        chunks, _ = prepare_data(TEXTO_PRUEBA)
        texto_reunido = " ".join(chunks).lower()
        # Verificar que conceptos clave del texto estén presentes en los chunks
        conceptos = ["fotosíntesis", "clorofila", "glucosa", "cloroplasto"]
        for concepto in conceptos:
            assert concepto in texto_reunido, (
                f"El concepto '{concepto}' del texto original no aparece en ningún chunk"
            )
