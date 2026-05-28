import logging
import re

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Modelo utilizado para generar embeddings semánticos
model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2"
)


# Divide el texto en chunks y genera embeddings
def prepare_data(text):
    text = text.replace("\n", " ").strip()

    # Separar texto en oraciones
    sentences = re.split(r'(?<=[.!?])\s+', text)
    total_sentences = len(sentences)

    # Ajustar tamaño de chunk según longitud del texto
    if total_sentences < 10:
        chunk_size = 1
    elif total_sentences < 30:
        chunk_size = 2
    elif total_sentences < 80:
        chunk_size = 3
    else:
        chunk_size = 5

    # Solapamiento entre chunks: 1 oración compartida entre chunks adyacentes
    # Evita perder contexto en los bordes (Lewis et al., 2020 — RAG original paper)
    overlap = 1 if chunk_size > 1 else 0
    step = chunk_size - overlap

    # Crear chunks con solapamiento
    chunks = []
    for i in range(0, total_sentences, step):
        chunk = " ".join(sentences[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    # Generar embeddings normalizados (necesario para usar distancia coseno con umbral)
    embeddings = model.encode(chunks, normalize_embeddings=True)
    embeddings = np.array(embeddings).astype("float32")

    logger.info(
        f"Chunking completado: {total_sentences} oraciones → {len(chunks)} chunks "
        f"(tamaño {chunk_size}, overlap {overlap})"
    )

    return chunks, embeddings